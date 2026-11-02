#!/usr/bin/env python3
"""首页结构校验器：在 git commit / 推送前拦截损坏的 index.html。

校验项：
1. 全文标签配对（排除 void 元素）
2. 每个 section 内 class="report-card" 的 <a> 开闭配对完整（落单 </a> / 截断卡片）
3. 每个 section 内不允许有裸奔的 <h2>/<p>（即不在 .report-card / .section-header / .history-list 内）
4. 四个版块的 report-grid 均非空

退出码 0 = 通过；非 0 = 失败并打印明细。

用法：
  python3 scripts/validate_homepage_html.py [index.html路径]   # 默认仓库根 index.html
"""
import re
import sys
from html.parser import HTMLParser
from pathlib import Path

REPO_DIR = Path(__file__).resolve().parent.parent
INDEX_FILE = REPO_DIR / "index.html"
SECTIONS = ["geopolitical", "ai-tech", "auto", "research"]
VOID = {"img", "br", "hr", "meta", "link", "input", "source", "area", "base", "col", "embed", "track", "wbr"}


class Checker(HTMLParser):
    """一次性收集：标签配对错误、卡片配对、裸奔 h2/p、各版块网格卡片数。"""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.stack = []          # [(tag, attrs_dict)]
        self.errors = []         # 标签配对
        self.stray = []          # 裸奔 h2/p
        self.card_anchor_depth = 0
        self.section_header_depth = 0
        self.history_depth = 0
        self.section = None      # 当前 section id
        self.grid_depth = None   # report-grid 所在深度（相对 stack）
        self.grid_cards = {}     # sec_id -> 网格内卡片数
        self._pending_card = False

    def _classes(self, attrs):
        return attrs.get("class") or ""

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag in VOID:
            # <img> 等无需配对，但仍检查
            return
        if tag == "section" and "id" in attrs:
            self.section = attrs["id"]
            self.grid_cards.setdefault(self.section, 0)
        if tag == "a" and "report-card" in self._classes(attrs):
            self.card_anchor_depth = len(self.stack) + 1
        if tag == "div":
            cls = self._classes(attrs)
            if "section-header" in cls:
                self.section_header_depth = len(self.stack) + 1
            elif "history-list" in cls:
                self.history_depth = len(self.stack) + 1
            elif "report-grid" in cls and self.section in SECTIONS:
                self.grid_depth = len(self.stack) + 1
        if tag in ("h2", "p") and self.section in SECTIONS:
            in_card = self.card_anchor_depth and len(self.stack) >= self.card_anchor_depth
            in_header = self.section_header_depth and len(self.stack) >= self.section_header_depth
            in_hist = self.history_depth and len(self.stack) >= self.history_depth
            if not (in_card or in_header or in_hist):
                self.stray.append(f"#{self.section}: 裸奔 <{tag}> at {self.getpos()}: {self.get_starttag_text()!r}")
        if tag == "a" and "report-card" in self._classes(attrs) and self.grid_depth:
            if len(self.stack) + 1 > self.grid_depth:
                self.grid_cards[self.section] = self.grid_cards.get(self.section, 0) + 1
        self.stack.append((tag, attrs))

    def handle_endtag(self, tag):
        if tag in VOID:
            return
        if not self.stack:
            self.errors.append(f"多余的 </{tag}> at {self.getpos()}")
            return
        if self.stack[-1][0] == tag:
            self.stack.pop()
        elif any(t == tag for t, _ in self.stack):
            while self.stack and self.stack[-1][0] != tag:
                t, _ = self.stack.pop()
                self.errors.append(f"未闭合的 <{t}>，被 </{tag}>（{self.getpos()}）强行关闭")
            self.stack.pop()
        else:
            self.errors.append(f"落单的 </{tag}> at {self.getpos()}")
        # 深度复位
        depth = len(self.stack)
        if self.card_anchor_depth and depth < self.card_anchor_depth:
            self.card_anchor_depth = 0
        if self.section_header_depth and depth < self.section_header_depth:
            self.section_header_depth = 0
        if self.history_depth and depth < self.history_depth:
            self.history_depth = 0
        if self.grid_depth and depth < self.grid_depth:
            self.grid_depth = None
        if tag == "section":
            self.section = None

    def finish(self):
        for t, _ in self.stack:
            self.errors.append(f"从未闭合的 <{t}>")


def validate(path: Path) -> list:
    problems = []
    text = path.read_text(encoding="utf-8")
    html = re.sub(r"<!--.*?-->", "", text, flags=re.S)

    c = Checker()
    c.feed(html)
    c.finish()
    problems.extend(c.errors)
    problems.extend(c.stray)

    for sec_id in SECTIONS:
        if sec_id not in c.grid_cards:
            problems.append(f"缺少版块 section#{sec_id}")
        elif c.grid_cards[sec_id] == 0:
            problems.append(f"#{sec_id}: report-grid 为空")

    return problems


def main() -> int:
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else INDEX_FILE
    problems = validate(path)
    if problems:
        print(f"❌ {path.name} 结构校验失败（{len(problems)} 项）:")
        for p in problems:
            print(f"  - {p}")
        return 1
    print(f"✅ {path.name} 结构校验通过")
    return 0


if __name__ == "__main__":
    sys.exit(main())
