#!/usr/bin/env python3
"""X2 EDU: fail-closed design approval gate for production PR."""
import json
import sys
from pathlib import Path

p = Path("docs/x2-edu-release-gates.json")
data = json.loads(p.read_text(encoding="utf-8"))
design = data["design_master"]
checks = {
    "Figma PC/SP URL登録": bool(design.get("figma_design_url")),
    "PC 1440正式承認Frame": bool(design.get("pc_frame_url")),
    "SP 390正式承認Frame": bool(design.get("sp_frame_url")),
    "デザイン承認リビジョン": bool(design.get("approved_revision")),
    "最終デザイン承認": design.get("status") == "承認済み",
    "実画面比較合格": data["validation"].get("figma_vs_browser_review") == "合格",
}
unmet = [name for name, passed in checks.items() if not passed]
if unmet:
    print("X2 EDU DESIGN GATE: 不合格（コードCI成功とデザイン合格は別）")
    for name in unmet:
        print(f" - 未完了: {name}")
    sys.exit(1)
print("X2 EDU DESIGN GATE: 設計申告の必須フィールド確認済み（証跡実査は別途必須）")
