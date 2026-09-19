#!/usr/bin/env python3
"""地缘板块首页卡片维护：网格最多保留 N 张最新卡片，其余移入历史列表（去重、按日期倒序）。

用法：python3 scripts/trim_geopolitical_cards.py [--apply]
不带 --apply 时只打印将要发生的改动（dry-run）。
"""
import argparse
import re
import sys
from pathlib import Path

REPO_DIR = Path(__file__).resolve().parent.parent
INDEX_FILE = REPO_DIR / "index.html"
GRID_MAX = 4
SECTION_ID = "geopolitical"
CARD_RE = re.compile(
    r'\n\s*<a href="(geopolitical-market-report-\d{4}-\d{2}-\d{2}\.html)" class="report-card">.*?</a>',
    re.S,
)
HIST_RE = re.compile(r'<div class="history-list">(.*?)</div>', re.S)


def hist_label(url: str) -> str:
    m = re.search(r'(\d{4})-(\d{2})-(\d{2})', url)
    return f"地缘周报 {m.group(2)}-{m.group(3)}" if m else url


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()

    text = INDEX_FILE.read_text(encoding="utf-8")
    sec_start = text.find(f'<section class="section" id="{SECTION_ID}">')
    if sec_start == -1:
        print(f"ERROR: 未找到 section#{SECTION_ID}", file=sys.stderr)
        return 1
    sec_end = text.find("</section>", sec_start)
    seg = text[sec_start:sec_end]

    cards = CARD_RE.findall(seg)
    if not cards:
        print("无卡片可整理")
        return 0
    cards_sorted = sorted(set(cards), reverse=True)
    keep, move = cards_sorted[:GRID_MAX], cards_sorted[GRID_MAX:]
    print(f"网格卡片: 现有 {len(cards)} 张（去重后 {len(cards_sorted)}）→ 保留 {len(keep)}，移出 {len(move)}")
    for u in keep:
        print(f"  保留 {u}")
    for u in move:
        print(f"  移入历史 {u}")

    if args.apply:
        grid_start = seg.find('<div class="report-grid">')
        # 网格结束位置：最后一张卡片之后紧跟的 </div>（卡片内部含多个 </div>，不能用第一个）
        grid_tail = seg[grid_start:]
        card_hits = list(CARD_RE.finditer(grid_tail))
        if not card_hits:
            print("ERROR: 网格内未找到卡片", file=sys.stderr)
            return 1
        grid_close = grid_start + grid_tail.find("</div>", card_hits[-1].end())
        if grid_close == -1:
            print("ERROR: 未找到网格闭合标签", file=sys.stderr)
            return 1
        grid = seg[grid_start:grid_close]
        blocks = CARD_RE.findall(grid)
        # 按日期倒序重建网格，仅保留前 GRID_MAX 张卡片的完整 HTML
        keep_blocks = []
        for url in keep:
            m = re.search(
                r'\n\s*<a href="' + re.escape(url) + r'" class="report-card">.*?</a>', grid, re.S
            )
            if m:
                keep_blocks.append(m.group(0))
        new_grid = '<div class="report-grid">' + "".join(keep_blocks) + "\n            </div>"
        seg = seg[:grid_start] + new_grid + seg[grid_close + len("</div>"):]

        # 历史列表 = 移出的卡片 + 原有历史（去重、倒序）
        hm = HIST_RE.search(seg)
        old_links = re.findall(r'<a href="([^"]+)"', hm.group(1)) if hm else []
        all_hist = sorted(set(old_links) | set(move), reverse=True)
        hist_html = "\n".join(
            f'                <a href="{u}">{hist_label(u)}</a>' for u in all_hist
        )
        new_hist = f'<div class="history-list">\n{hist_html}\n            </div>'
        if hm:
            seg = seg[: hm.start()] + new_hist + seg[hm.end():]
        else:
            seg = seg.replace("</div>\n        \n", new_hist + "\n        ", 1)

        text = text[:sec_start] + seg + text[sec_end:]
        INDEX_FILE.write_text(text, encoding="utf-8")
        print(f"✅ 已写回 {INDEX_FILE}（网格 {len(keep)} 张，历史 {len(all_hist)} 条）")
    else:
        print("(dry-run；加 --apply 生效)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
