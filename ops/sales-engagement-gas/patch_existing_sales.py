"""Apply a minimal, reversible patch to a LOCAL CLONED sales GAS source.

NEVER edits the original. Do not run clasp push or deploy.
Expected original: 03_sales_import_dedup.js from airadmin8-haishin.
"""
import argparse, difflib, hashlib, json
from pathlib import Path

def patch(source: str) -> str:
    rules = [
      (
       "      '日程調整へ ' + buildBookingUrl_(deliveryId)\n    );\n}\n",
       "      '日程調整へ ' + buildBookingUrl_(deliveryId)\n    ) +"
       " '\\n\\n□ 研究用ロボット製品一覧：' + buildTrackedCatalogUrl_(deliveryId);\n}\n",
      ),
      (
       "    escapedBody + '<br><br>' + escapedSignature +\n    '</div>';",
       "    escapedBody + '<br><br>' +\n"
       "    '<a href=\"' + escapeHtmlForSalesMail_(buildTrackedCatalogUrl_(deliveryId)) +\n"
       "    '\" style=\"color:#1155cc;text-decoration:underline;\">研究用ロボット製品一覧を見る</a><br><br>' +\n"
       "    escapedSignature +\n    '</div>';",
      ),
      (
       "    syncWebEngagementFromLog_();\n  } catch (webLogError) {",
       "    syncWebEngagementFromLog_();\n"
       "    // Sales-wide KPI materialization is disabled by default during TEST E2E.\n"
       "    // Original Web engagement sync and TEST filtering remain unchanged.\n"
       "    if (String(PropertiesService.getScriptProperties().getProperty('AA8_WEB_EVENT_SUMMARY_ENABLED') || '').trim().toUpperCase() === 'TRUE') {\n"
       "      const summary=syncAa8WebMarketingSummary_();\n"
       "      if(!summary.ok)throw new Error('Web attribution summary failed: '+summary.error);\n"
       "    }\n"
       "  } catch (webLogError) {",
      ),
      (
       "  validateHeaders_(wh, ['送信管理ID','イベント日時','ページ種別','ページパス'], 'Web行動ログ');",
       "  validateHeaders_(wh, ['送信管理ID','イベント日時','ページ種別','ページパス','データソース'], 'Web行動ログ');",
      ),
      (
       "    const pageType = clean_(value_(row, wh, 'ページ種別'));\n"
       "    const pagePath = clean_(value_(row, wh, 'ページパス'));\n"
       "    if (!byId[deliveryId])",
       "    const pageType = clean_(value_(row, wh, 'ページ種別'));\n"
       "    const pagePath = clean_(value_(row, wh, 'ページパス'));\n"
       "    const dataSource = clean_(value_(row, wh, 'データソース'));\n"
       "    // TEST events remain in existing Web行動ログ for audit, but never\n"
       "    // advance live customer last-reaction timestamps or sales KPIs.\n"
       "    if (pageType.startsWith('TEST_') || dataSource === 'VERCEL_WEB_EVENT_TEST') continue;\n"
       "    if (!byId[deliveryId])",
      ),
    ]
    for old, new in rules:
        times = source.count(old)
        if times != 1:
            raise ValueError(f"Expected 1 unique patch anchor; found {times}: {old[:70]!r}")
        source = source.replace(old,new)
    return source

def main():
    cli=argparse.ArgumentParser()
    cli.add_argument("--source",type=Path,required=True)
    cli.add_argument("--output",type=Path,required=True)
    cli.add_argument("--diff",type=Path,required=True)
    args=cli.parse_args()
    if args.source.resolve()==args.output.resolve():
        raise SystemExit("FAIL CLOSED: source overwrite prohibited")
    if args.output.exists() or args.diff.exists():
        raise SystemExit("FAIL CLOSED: output collision")
    original=args.source.read_text(encoding="utf-8")
    updated=patch(original)
    changes=list(difflib.unified_diff(original.splitlines(keepends=True),updated.splitlines(keepends=True),
                fromfile="airadmin8-haishin original 03_sales_import_dedup.js",
                tofile="proposed approved-source candidate 03_sales_import_dedup.js"))
    args.output.write_text(updated,encoding="utf-8",newline="\n")
    args.diff.write_text("".join(changes),encoding="utf-8",newline="\n")
    print(json.dumps({"base_sha256":hashlib.sha256(original.encode()).hexdigest(),
                      "candidate_sha256":hashlib.sha256(updated.encode()).hexdigest(),
                      "diff_hunks":sum(line.startswith("@@ ") for line in changes),
                      "source_preserved":True,
                      "output":str(args.output),
                      "diff":str(args.diff)},ensure_ascii=False))
if __name__=="__main__":
    main()
