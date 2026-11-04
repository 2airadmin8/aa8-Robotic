"""Approval-gated catalog downloads; all fixtures are synthetic."""
import hashlib
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import json
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import product_factory as factory

class CatalogDownloadTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        (self.root/"assets/pdf").mkdir(parents=True)
        (self.root/"data").mkdir()
        src = Path(__file__).resolve().parents[1]
        products = factory.catalog(src)
        self.products = products
        self.product = next(p for p in products if "pageFactory" in p)
        self.spec = json.loads(json.dumps(self.product["pageFactory"]))
        self.pdf = self.root/"assets/pdf/test-brochure.pdf"
        self.pdf.write_bytes(b"%PDF-1.4\\nsynthetic QA sample only")
        self.sha=hashlib.sha256(self.pdf.read_bytes()).hexdigest()

    def _check(self, spec):
        # Real local-product/source/media validation is out of scope here;
        # mock only those unrelated parts of the contract.
        with patch.object(factory, "page_path",return_value=self.root/"products/test.html"),\
             patch.object(factory, "local_asset",return_value="/assets/img/test.webp"),\
             patch.object(factory, "official_url",return_value="https://example.org/spec"),\
             patch.object(factory, "catalog",return_value=self.products):
            return factory.validate_page_factory(self.root,{**self.product,"pageFactory":spec})

    def test_internal_review_cannot_publish_path(self):
        self.spec["catalogDownload"]={"status":"internal_review","path":"assets/pdf/test-brochure.pdf"}
        with self.assertRaisesRegex(factory.ContractError,"must not define public PDF"):
            self._check(self.spec)

    def test_internal_review_has_no_pdf_url(self):
        self.spec["catalogDownload"]={"status":"internal_review"}
        self._check(self.spec)

    def test_approved_pdf_requires_revision_and_approval_and_hash(self):
        for omitted in ["revision","approvalRef","pdfSha256"]:
            payload=dict(status="approved_public",path="assets/pdf/test-brochure.pdf",revision="v1",approvalRef="QA-001",pdfSha256=self.sha)
            del payload[omitted]
            self.spec["catalogDownload"]=payload
            with self.assertRaises(factory.ContractError):
                self._check(self.spec)

    def test_bad_sha_blocks_release(self):
        self.spec["catalogDownload"]={"status":"approved_public","path":"assets/pdf/test-brochure.pdf","revision":"v1","approvalRef":"QA-001","pdfSha256":"0"*64}
        with self.assertRaisesRegex(factory.ContractError,"SHA256 mismatch"):
            self._check(self.spec)
