#!/usr/bin/env python3
"""Batch-inject Waline comment component into static report HTML pages.

Targets:
  (a) Root-level *.html report pages (contain class="navbar" AND
      class="breadcrumb"; excludes index.html / index-v2.html)
  (b) Subdirectory reports: gold-etf/, world-cup-2026/, gpt6-astra/
      (index.html if present, otherwise all *.html in the directory)

Idempotent: files already containing the "waline-comments" marker are skipped.

Usage:
    python3 inject_comments.py            # scan & inject (dry-run preview counts)
    python3 inject_comments.py --apply    # actually write files
    python3 inject_comments.py --root /path/to/site --apply
"""

import argparse
import re
import sys
from pathlib import Path

MARKER = "waline-comments"
SUBDIRS = ("gold-etf", "world-cup-2026", "gpt6-astra")
EXCLUDE_ROOT = {"index.html", "index-v2.html"}

DIV_TEMPLATE = (
    '<div id="waline-comments" '
    'style="max-width: 860px; margin: 40px auto; padding: 0 24px;"></div>\n'
)


def build_snippet(prefix: str) -> str:
    """Return the Waline embed block. `prefix` is '' for root pages,
    '../assets/waline/' style relative prefix for subdirectory pages."""
    base = f"{prefix}assets/waline" if prefix else "assets/waline"
    return (
        f"<!-- Waline comments -->\n"
        f'{DIV_TEMPLATE}'
        f'<link rel="stylesheet" href="{base}/waline.css" />\n'
        f'<script src="{base}/waline.umd.js"></script>\n'
        f"<script>\n"
        f"  Waline.init({{\n"
        f'    el: "#waline-comments",\n'
        f'    serverURL: "https://comment.hosamzj.cn",\n'
        f"    path: location.pathname.replace(/\\.html$/, ''),\n"
        f"    dark: 'body',\n"
        f"    lang: 'zh-CN',\n"
        f"    pageview: true,\n"
        f"  }});\n"
        f"</script>\n"
    )


def is_report_page(html: str) -> bool:
    return 'class="navbar"' in html and 'class="breadcrumb"' in html


def find_targets(root: Path):
    root_reports, sub_reports, skipped = [], [], []

    for f in sorted(root.glob("*.html")):
        if f.name in EXCLUDE_ROOT:
            continue
        html = f.read_text(encoding="utf-8")
        if not is_report_page(html):
            skipped.append((f, "not a report page"))
            continue
        if MARKER in html:
            skipped.append((f, "already injected"))
            continue
        root_reports.append(f)

    for sub in SUBDIRS:
        d = root / sub
        if not d.is_dir():
            skipped.append((d, "missing subdirectory"))
            continue
        idx = d / "index.html"
        candidates = [idx] if idx.exists() else sorted(d.glob("*.html"))
        for f in candidates:
            html = f.read_text(encoding="utf-8")
            if MARKER in html:
                skipped.append((f, "already injected"))
                continue
            sub_reports.append(f)

    return root_reports, sub_reports, skipped


def inject(path: Path, prefix: str) -> bool:
    html = path.read_text(encoding="utf-8")
    if MARKER in html:
        return False
    m = re.search(r"</body\s*>", html, re.IGNORECASE)
    if not m:
        return False
    snippet = build_snippet(prefix)
    new = html[: m.start()] + snippet + html[m.start():]
    path.write_text(new, encoding="utf-8")
    return True


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--apply", action="store_true", help="write changes (default: dry-run)")
    ap.add_argument("--root", default=str(Path(__file__).resolve().parent.parent),
                    help="site repository root (default: parent of scripts/)")
    args = ap.parse_args()

    root = Path(args.root).resolve()
    root_reports, sub_reports, skipped = find_targets(root)

    print(f"Root report pages : {len(root_reports)}")
    for f in root_reports:
        print(f"  {f.relative_to(root)}")
    print(f"Subdir report pages: {len(sub_reports)}")
    for f in sub_reports:
        print(f"  {f.relative_to(root)}")
    print(f"Skipped           : {len(skipped)}")
    for f, why in skipped:
        print(f"  {f.relative_to(root) if isinstance(f, Path) else f} ({why})")

    if not args.apply:
        print("\nDry-run: re-run with --apply to write changes.")
        return

    done = 0
    for f in root_reports:
        if inject(f, prefix=""):
            done += 1
            print(f"injected: {f.relative_to(root)}")
    for f in sub_reports:
        if inject(f, prefix="../"):
            done += 1
            print(f"injected: {f.relative_to(root)}")
    print(f"\nInjected into {done} files.")


if __name__ == "__main__":
    main()
