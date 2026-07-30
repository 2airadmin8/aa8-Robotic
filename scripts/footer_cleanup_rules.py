#!/usr/bin/env python3
"""Footer cleanup rules shared by the static-site build."""

from __future__ import annotations

import re

NOTICE_TEXT = "製品仕様・価格・納期・保証は正式見積時に確認します。"


def cleanup_footer(markup: str) -> str:
    footer_match = re.search(r"(<footer\b[^>]*>)(.*?)(</footer>)", markup, flags=re.IGNORECASE | re.DOTALL)
    if not footer_match:
        return markup

    footer_body = footer_match.group(2)
    footer_body = re.sub(rf"<p\b[^>]*>\s*{re.escape(NOTICE_TEXT)}\s*</p>", "", footer_body, flags=re.IGNORECASE)
    footer_body = footer_body.replace(NOTICE_TEXT, "")

    learning_start = footer_body.find('class="aa8-footer-learning')
    upper_part = footer_body if learning_start < 0 else footer_body[:learning_start]
    lower_part = "" if learning_start < 0 else footer_body[learning_start:]

    upper_part = re.sub(r'<a\b[^>]*href=["\'][^"\']*resources\.html[^"\']*["\'][^>]*>\s*資料・SDK\s*</a>', "", upper_part, flags=re.IGNORECASE)
    upper_part = re.sub(r'<a\b[^>]*href=["\'][^"\']*faq\.html[^"\']*["\'][^>]*>\s*よくある質問\s*</a>', "", upper_part, flags=re.IGNORECASE)

    replacement = footer_match.group(1) + upper_part + lower_part + footer_match.group(3)
    return markup[:footer_match.start()] + replacement + markup[footer_match.end():]
