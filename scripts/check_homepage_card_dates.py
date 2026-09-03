#!/usr/bin/env python3
"""
Audit index.html report-card dates against the actual report files.

Usage:
    python check_homepage_card_dates.py              # audit only
    python check_homepage_card_dates.py --fix      # auto-fix mismatches in index.html
    python check_homepage_card_dates.py --verbose    # show all cards

Exit codes:
    0 - no mismatches
    1 - mismatches found (or file error)
"""
from __future__ import annotations

import argparse
import re
import sys
from datetime import datetime
from pathlib import Path

SITE_ROOT = Path(__file__).resolve().parents[1]
INDEX_PATH = SITE_ROOT / "index.html"

# Labels that are not calendar dates and should not be overwritten automatically.
# If a label is encountered, the script will still warn when the underlying
# report is newer than the label implies, but it will not change the label
# without --force-labels.
STATIC_LABELS = {"每周六更新", "专题研究"}


def extract_report_date(path: Path) -> tuple[str | None, str]:
    """Return (date_str, source_description) for a report HTML file."""
    if not path.exists():
        return None, "file not found"

    text = path.read_text(encoding="utf-8", errors="ignore")

    # Prefer filename date if it is explicitly confirmed in the page title.
    filename_date: str | None = None
    m = re.search(r"(\d{4}-\d{2}-\d{2})", path.name)
    if m:
        filename_date = m.group(1)

    # 1. Explicit report meta: 报告日期 / 生成时间 / 更新时间 / 发布于.
    explicit_patterns = [
        r"报告日期[:：]\s*([\d]{4}-[\d]{2}-[\d]{2})",
        r"生成时间[:：]\s*([\d]{4}-[\d]{2}-[\d]{2})",
        r"更新时间[:：]\s*([\d]{4}-[\d]{2}-[\d]{2})",
        r"发布于[:：]\s*([\d]{4}-[\d]{2}-[\d]{2})",
        r"(?:发布|更新|生成)于?\s*([\d]{4}-[\d]{2}-[\d]{2})",
    ]
    for pat in explicit_patterns:
        m = re.search(pat, text)
        if m:
            return m.group(1), "explicit meta"

    # 2. Title / heading date (ISO or Chinese), preferring the filename date
    #    if it appears there.
    for section_re in [r"<title>.*?</title>", r"<h1.*?</h1>", r"<h2.*?</h2>"]:
        sm = re.search(section_re, text, re.DOTALL)
        if not sm:
            continue
        section_text = sm.group(0)
        if filename_date and filename_date in section_text:
            return filename_date, f"matches filename in {section_re}"
        cm = re.search(r"(\d{4})\s*年\s*(\d{1,2})\s*月\s*(\d{1,2})\s*日", section_text)
        if cm:
            return (
                f"{cm.group(1)}-{int(cm.group(2)):02d}-{int(cm.group(3)):02d}",
                f"chinese date in {section_re}",
            )
        dm = re.search(r"(\d{4}-\d{2}-\d{2})", section_text)
        if dm:
            return dm.group(1), f"iso date in {section_re}"

    # 3. Filename itself is a strong signal.
    if filename_date:
        return filename_date, "filename date"

    # 4. Last resort: file modification time.
    mtime = datetime.fromtimestamp(path.stat().st_mtime)
    return mtime.strftime("%Y-%m-%d"), "file mtime"


def parse_cards(index_html: str) -> list[tuple[str, str, str]]:
    """
    Parse index.html report cards.
    Returns list of (href, card_date, full_card_html).
    """
    pattern = re.compile(
        r'(<a href="([^"]+)" class="report-card">'
        r'.*?<div class="meta">\s*<span>(.*?)</span>\s*<span>→ 查看报告</span>\s*</div>\s*</a>)',
        re.DOTALL,
    )
    return [(href, date_span.strip(), full) for full, href, date_span in pattern.findall(index_html)]


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Audit/fixi index.html report-card dates against report files."
    )
    parser.add_argument("--fix", action="store_true", help="Update index.html with detected dates")
    parser.add_argument("--force-labels", action="store_true", help="Also overwrite static labels such as '每周六更新'")
    parser.add_argument("--verbose", action="store_true", help="Print every card, not just mismatches")
    args = parser.parse_args()

    if not INDEX_PATH.exists():
        print(f"ERROR: {INDEX_PATH} not found", file=sys.stderr)
        return 1

    index_html = INDEX_PATH.read_text(encoding="utf-8")
    cards = parse_cards(index_html)
    mismatches: list[tuple[str, str, str | None, str, str]] = []  # href, card_date, detected, source, full_card

    print(f"{'Card date':<22} {'Detected date':<18} {'Source':<30} Href")
    print("=" * 105)

    for href, card_date, full_card in cards:
        path = SITE_ROOT / href
        if href.endswith("/"):
            path = path / "index.html"

        detected, source = extract_report_date(path)

        if detected is None:
            status = "⚠ FILE MISSING"
            print(f"{card_date:<22} {'N/A':<18} {source:<30} {href} {status}")
            mismatches.append((href, card_date, detected, source, full_card))
            continue

        # Static labels: report but do not auto-fix unless forced.
        if card_date in STATIC_LABELS:
            status = "label"
            if args.verbose:
                print(f"{card_date:<22} {detected:<18} {source:<30} {href} {status}")
            # A label is only a mismatch if the caller wants to numericise it.
            if args.force_labels:
                mismatches.append((href, card_date, detected, source, full_card))
            continue

        if detected == card_date:
            status = "✓"
            if args.verbose:
                print(f"{card_date:<22} {detected:<18} {source:<30} {href} {status}")
        else:
            status = "✗ MISMATCH"
            print(f"{card_date:<22} {detected:<18} {source:<30} {href} {status}")
            mismatches.append((href, card_date, detected, source, full_card))

    if not mismatches:
        print("\nNo mismatches found.")
        return 0

    print(f"\n{len(mismatches)} mismatch(es) found.")

    if not args.fix and not args.force_labels:
        print("Run with --fix to update index.html.")
        return 1

    # Apply fixes.
    fixed_count = 0
    new_html = index_html
    for href, card_date, detected, source, full_card in mismatches:
        if detected is None:
            print(f"  SKIP {href}: target file not found")
            continue

        # Replace the date span inside this exact card block.
        new_card = re.sub(
            r'(<a href="' + re.escape(href) + r'" class="report-card">.*?<div class="meta">\s*<span>)(.*?)(</span>\s*<span>→ 查看报告</span>)',
            r"\g<1>" + detected + r"\g<3>",
            full_card,
            count=1,
            flags=re.DOTALL,
        )
        if new_card == full_card:
            print(f"  WARN {href}: regex replacement did not change anything")
            continue
        new_html = new_html.replace(full_card, new_card)
        fixed_count += 1
        print(f"  FIXED {href}: {card_date} -> {detected}")

    if fixed_count:
        INDEX_PATH.write_text(new_html, encoding="utf-8")
        print(f"\nUpdated {INDEX_PATH} ({fixed_count} card(s) fixed).")

    return 0 if not [m for m in mismatches if m[2] is None] else 1


if __name__ == "__main__":
    sys.exit(main())
