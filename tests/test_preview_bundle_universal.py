"""All product previews must have one precise pre- and post-deploy asset gate."""
import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
from verify_preview_bundle import (
    SCHEMA, check, css_urls, local_path, prepare, referenced_assets,
    deployed_source_tree, verify_deployment,
)


def provider_tree(manifest):
    root={}
    for entry in manifest["files"]:
        parts=entry["file"].split("/")
        node=root
        for seg in parts[:-1]:
            node=node.setdefault(seg,{})
        node[parts[-1]]=entry["sha"]
    def descend(children):
        return [{"name":k,"type":"directory","children":descend(v)} if isinstance(v,dict)
                else {"name":k,"type":"file","uid":v} for k,v in children.items()]
    return descend(root)


class UniversalPreviewBundleQA(unittest.TestCase):
    def test_existing_real_a2_and_x2_source_assets_are_collected(self):
        with tempfile.TemporaryDirectory() as directory:
            site=Path(directory)
            # Use actual product Factory sources; keep real source bytes.
            import product_factory
            for folder in ("a2-factory","x2-pilot"):
                product=json.loads((ROOT/"tests/fixtures"/folder/"product.json").read_text("utf-8"))
                name=folder+"-preview.html"
                (site/name).write_text(product_factory.render(ROOT,product,"preview"),"utf-8")
            # Materialize only source files found by the actual HTML/CSS walker.
            # Resolve from project root before preparing the temporary bundle.
            collected=set()
            for name in ("a2-factory-preview.html","x2-pilot-preview.html"):
                collected.update(referenced_assets((site/name).read_text("utf-8"),ROOT,name))
            for path in collected:
                dest=site/path
                dest.parent.mkdir(parents=True,exist_ok=True)
                dest.write_bytes((ROOT/path).read_bytes())
            manifest=prepare(site,[site/"a2-factory-preview.html",
                                   site/"x2-pilot-preview.html"],"a"*40)
            self.assertEqual(manifest["schema"],SCHEMA)
            self.assertEqual(manifest["preview_count"],2)
            self.assertIn("assets/img/airadmin8-robotics-logo-footer.svg",manifest["assets"])
            self.assertIn("assets/img/airadmin8-robotics-logo-pc.svg",manifest["assets"])
            self.assertIn("assets/img/airadmin8-robotics-logo-sp.svg",manifest["assets"])
            self.assertEqual(len(manifest["files"]),2+len(collected))
            actual=provider_tree(manifest)
            result=verify_deployment(manifest,actual,deployed_revision="a"*40,
                                      state="READY",target=None)
            self.assertEqual(result["status"],"PREVIEW_POST_DEPLOY_PASS")
            self.assertEqual(result["files_checked"],len(manifest["files"]))

    def test_postdeploy_rejects_missing_footer_and_wrong_css_sha(self):
        manifest={"schema":SCHEMA,"revision":"f"*40,
                  "previews":{"a2-factory-preview.html":"a"*40},
                  "assets":{"assets/img/airadmin8-robotics-logo-footer.svg":
                              {"sha1":"b"*40,"size":17},
                            "assets/css/shared-layout.css":
                              {"sha1":"c"*40,"size":25}},
                  "files":[{"file":"a2-factory-preview.html","sha":"a"*40,"size":123},
                           {"file":"assets/img/airadmin8-robotics-logo-footer.svg",
                            "sha":"b"*40,"size":17},
                           {"file":"assets/css/shared-layout.css","sha":"c"*40,"size":25}]}
        correct=provider_tree(manifest)
        self.assertEqual(verify_deployment(manifest,correct,deployed_revision="f"*40,
                                            state="READY",target=None)["status"],
                         "PREVIEW_POST_DEPLOY_PASS")
        absent=copy.deepcopy(correct)
        # Remove only the official footer image from its nested folder.
        image_dir=next(x for x in absent if x["name"]=="assets")
        img=next(x for x in image_dir["children"] if x["name"]=="img")
        img["children"]=[]
        with self.assertRaisesRegex(ValueError,"missing=.*footer"):
            verify_deployment(manifest,absent,deployed_revision="f"*40,
                              state="READY",target=None)
        mutated=copy.deepcopy(correct)
        assets_dir=next(x for x in mutated if x["name"]=="assets")
        css_dir=next(x for x in assets_dir["children"] if x["name"]=="css")
        css_dir["children"][0]["uid"]="0"*40
        with self.assertRaisesRegex(ValueError,"sha_mismatch=.*shared-layout"):
            verify_deployment(manifest,mutated,deployed_revision="f"*40,
                              state="READY",target=None)
        for sha,state,target in [("0"*40,"READY",None),("f"*40,"ERROR",None),
                                  ("f"*40,"READY","production")]:
            with self.subTest(sha=sha,state=state,target=target):
                with self.assertRaisesRegex(ValueError,"PREVIEW_BUNDLE_HOLD"):
                    verify_deployment(manifest,correct,deployed_revision=sha,
                                      state=state,target=target)

    def test_missing_real_asset_is_predeploy_hold(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            (root/"a2-preview.html").write_text(
                '<main data-product-factory="g1-v1"><meta content="noindex,nofollow">'
                '<footer><img src="/assets/img/airadmin8-robotics-logo-footer.svg">'
                '</footer></main>',"utf-8")
            with self.assertRaisesRegex(ValueError,"referenced asset not present"):
                prepare(root,[root/"a2-preview.html"],"f"*40)

    def test_recursive_css_and_srcset_missing_assets_cannot_escape(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            (root/"assets/css").mkdir(parents=True)
            (root/"assets/img").mkdir(parents=True)
            (root/"assets/css/a.css").write_text(
                '@import url("./b.css"); .a{background:url("../img/photo.svg")}',"utf-8")
            (root/"assets/css/b.css").write_text(
                '.b{background-image:url("../img/required.webp")}',"utf-8")
            (root/"assets/img/photo.svg").write_text("<svg/>","utf-8")
            (root/"assets/img/airadmin8-robotics-logo-footer.svg").write_text("<svg/>","utf-8")
            html='<link rel="stylesheet" href="/assets/css/a.css">'+(
                '<img srcset="/assets/img/photo.svg 1x">'
                '<img src="/assets/img/airadmin8-robotics-logo-footer.svg">')
            with self.assertRaisesRegex(ValueError,"required.webp"):
                referenced_assets(html,root)
            (root/"assets/img/required.webp").write_bytes(b"image")
            checked=referenced_assets(html,root)
            self.assertIn("assets/img/required.webp",checked)
            self.assertEqual(len(checked),5)
        with self.assertRaisesRegex(ValueError,"escapes web root"):
            local_path("../../etc/passwd")
        with self.assertRaisesRegex(ValueError,"unsafe resource"):
            local_path("javascript:alert(1)")

    def test_pick_only_deployed_product_from_auto_collected_multi_product_manifest(self):
        from verify_preview_bundle import select_deployed_previews
        manifest={
            "schema":SCHEMA,"revision":"f"*40,
            "previews":{"a2-factory-preview.html":"a"*40,
                        "x2-pilot-preview.html":"b"*40},
            "per_preview_assets":{
                "a2-factory-preview.html":["assets/img/airadmin8-robotics-logo-footer.svg"],
                "x2-pilot-preview.html":["assets/img/x2-hero.png"]},
            "assets":{
                "assets/img/airadmin8-robotics-logo-footer.svg":{"sha1":"c"*40,"size":10},
                "assets/img/x2-hero.png":{"sha1":"d"*40,"size":20}},
        }
        tree=provider_tree({"files":[
            {"file":"a2-factory-preview.html","sha":"a"*40},
            {"file":"assets/img/airadmin8-robotics-logo-footer.svg","sha":"c"*40},
        ]})
        selected=select_deployed_previews(manifest,tree)
        self.assertEqual(list(selected["previews"]),["a2-factory-preview.html"])
        self.assertEqual(list(selected["assets"]),
                         ["assets/img/airadmin8-robotics-logo-footer.svg"])
        self.assertEqual(verify_deployment(selected,tree,
            deployed_revision="f"*40,state="READY",target=None)["files_checked"],2)
        unknown=provider_tree({"files":[
            {"file":"unregistered-preview.html","sha":"a"*40}
        ]})
        with self.assertRaisesRegex(ValueError,"unregistered"):
            select_deployed_previews(manifest,unknown)

    def test_vercel_source_wrapper_is_not_part_of_deployed_url_paths(self):
        from verify_preview_bundle import deployed_source_tree
        nested=[{"name":"src","type":"directory","children":[
            {"name":"a2-factory-preview.html","type":"file","uid":"a"*40},
            {"name":"assets","type":"directory","children":[
                {"name":"img","type":"directory","children":[
                    {"name":"airadmin8-robotics-logo-footer.svg",
                     "type":"file","uid":"b"*40}]}]},
        ]}]
        files=deployed_source_tree(nested)
        self.assertIn("a2-factory-preview.html",files)
        self.assertIn("assets/img/airadmin8-robotics-logo-footer.svg",files)
        self.assertNotIn("src/a2-factory-preview.html",files)

    def test_malformed_deployed_file_tree_is_hold(self):
        with self.assertRaisesRegex(ValueError,"file SHA1"):
            deployed_source_tree([{"name":"x.svg","type":"file"}])
        with self.assertRaisesRegex(ValueError,"malformed deployment path"):
            deployed_source_tree([{"name":"../x","uid":"0"*40}])
