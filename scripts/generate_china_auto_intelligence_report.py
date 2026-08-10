#!/usr/bin/env python3
"""
自动生成《中国汽车智能驾驶趋势观察》HTML 报告并推送到 GitHub Pages。

运行方式：
    python3 scripts/generate_china_auto_intelligence_report.py

流程：
1. 调用 last30days（英文/全球源）与 last30days-cn（中文源）抓取近 30 天舆情
2. 将两份原始输出整理成一份带 DuoDuo Research 导航栏的 HTML 报告
3. 更新 index.html 报告卡片
4. git add / commit / push 到 origin main
"""

import datetime
import os
import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path("/Users/huosam/sites")
SKILL_EN = Path("/Users/huosam/last30days-skill")
SKILL_CN = Path("/Users/huosam/last30days-skill-cn")
CHROME_PATH = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

EN_TOPIC = "China autonomous driving EV"
CN_TOPIC = "中国汽车 智能驾驶"


def run_skill(skill_dir: Path, topic: str, is_cn: bool) -> str:
    """调用对应 skill 的脚本，返回 stdout。"""
    if is_cn:
        py = skill_dir / ".venv/bin/python"
        script = skill_dir / "skills/last30days/scripts/last30days.py"
        env = os.environ.copy()
        env["LAST30DAYS_BROWSER_PATH"] = CHROME_PATH
        cmd = [str(py), str(script), topic, "--quick", "--search", "weibo,bilibili,baidu", "--emit", "compact"]
    else:
        py = skill_dir / ".venv/bin/python"
        script = skill_dir / "skills/last30days/scripts/last30days.py"
        env = os.environ.copy()
        cmd = [str(py), str(script), topic, "--emit=compact"]

    result = subprocess.run(
        cmd,
        cwd=str(skill_dir),
        env=env,
        capture_output=True,
        text=True,
        timeout=600,
    )
    return result.stdout + (f"\n[STDERR]\n{result.stderr}" if result.stderr else "")


def format_text_to_html(text: str) -> str:
    """将纯文本简单格式化为 HTML。"""
    # Escape HTML
    text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    # Convert URLs to links
    text = re.sub(
        r"(https?://[^\s\)\]\>]+)",
        r'<a href="\1" target="_blank">\1</a>',
        text,
    )
    # Convert lines starting with - or * to list items
    lines = text.splitlines()
    in_list = False
    html_lines = []
    for line in lines:
        stripped = line.lstrip()
        if re.match(r"^[-*]\s+", stripped):
            if not in_list:
                html_lines.append("<ul>")
                in_list = True
            item = re.sub(r"^[-*]\s+", "", stripped)
            html_lines.append(f"<li>{item}</li>")
        else:
            if in_list:
                html_lines.append("</ul>")
                in_list = False
            if line.strip():
                html_lines.append(f"<p>{line}</p>")
            else:
                html_lines.append("<br/>")
    if in_list:
        html_lines.append("</ul>")
    return "\n".join(html_lines)


def build_report_html(date_str: str, en_output: str, cn_output: str) -> str:
    """生成完整的 HTML 报告。"""
    title = f"中国汽车智能驾驶趋势观察（{date_str}）"
    en_html = format_text_to_html(en_output)
    cn_html = format_text_to_html(cn_output)

    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        :root {{
            --bg: #141413;
            --bg-card: #232320;
            --bg-secondary: #1a1a18;
            --text: #faf9f5;
            --text-secondary: #b0aea5;
            --text-muted: #7a7872;
            --accent: #c96442;
            --accent-light: #d97757;
            --border: #30302e;
        }}
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{
            background: var(--bg);
            color: var(--text);
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC", "Microsoft YaHei", sans-serif;
            line-height: 1.6;
        }}
        .container {{ max-width: 1400px; margin: 0 auto; padding: 40px 24px; }}
        header {{
            background: var(--bg-card);
            padding: 48px 40px;
            border-radius: 16px;
            margin-bottom: 32px;
            border: 1px solid var(--border);
            border-left: 4px solid var(--accent);
        }}
        h1 {{ font-size: 2.4rem; font-weight: 700; margin-bottom: 12px; color: var(--text); }}
        .subtitle {{ color: var(--text-secondary); font-size: 1.1rem; }}
        .meta {{ color: var(--text-muted); font-size: 0.9rem; margin-top: 16px; }}
        .section {{
            background: var(--bg-card);
            border-radius: 16px;
            padding: 32px;
            margin-bottom: 24px;
            border: 1px solid var(--border);
        }}
        h2 {{ color: var(--accent); font-size: 1.5rem; margin-bottom: 20px; padding-bottom: 12px; border-bottom: 2px solid var(--accent); display: inline-block; }}
        h3 {{ color: var(--text); font-size: 1.2rem; margin: 24px 0 12px; }}
        p {{ color: var(--text-secondary); margin-bottom: 12px; }}
        ul {{ margin-left: 20px; color: var(--text-secondary); }}
        li {{ margin-bottom: 8px; }}
        a {{ color: var(--accent-light); text-decoration: none; }}
        a:hover {{ text-decoration: underline; }}
        pre {{
            background: var(--bg-secondary);
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 20px;
            overflow-x: auto;
            color: var(--text-secondary);
            font-size: 0.85rem;
            line-height: 1.6;
            white-space: pre-wrap;
            word-wrap: break-word;
        }}
        .navbar {{
            position: sticky;
            top: 0;
            z-index: 1000;
            background: rgba(20, 20, 19, 0.95);
            backdrop-filter: blur(10px);
            border-bottom: 1px solid var(--border);
        }}
        .nav-container {{
            max-width: 1400px;
            margin: 0 auto;
            padding: 0 24px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            height: 64px;
        }}
        .nav-brand {{
            display: flex;
            align-items: center;
            gap: 12px;
            color: var(--text);
            font-weight: 600;
            font-size: 1.1rem;
            text-decoration: none;
        }}
        .nav-brand-icon {{
            width: 32px;
            height: 32px;
            background: var(--accent);
            border-radius: 8px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1rem;
            font-weight: 700;
            color: white;
        }}
        .nav-links {{
            display: flex;
            gap: 32px;
        }}
        .nav-links a {{
            color: var(--text-secondary);
            font-size: 0.95rem;
            font-weight: 500;
            text-decoration: none;
            transition: color 0.2s ease;
            position: relative;
        }}
        .nav-links a:hover {{ color: var(--text); }}
        .nav-links a.active {{ color: var(--accent); }}
        .nav-links a.active::after {{
            content: '';
            position: absolute;
            bottom: -8px;
            left: 0;
            width: 100%;
            height: 2px;
            background: var(--accent);
            border-radius: 2px;
        }}
        .breadcrumb {{
            background: var(--bg-secondary);
            border-bottom: 1px solid var(--border);
            padding: 12px 0;
        }}
        .breadcrumb-container {{
            max-width: 1400px;
            margin: 0 auto;
            padding: 0 24px;
            display: flex;
            align-items: center;
            gap: 8px;
            color: var(--text-muted);
            font-size: 0.85rem;
        }}
        .breadcrumb-container a {{
            color: var(--text-secondary);
            text-decoration: none;
        }}
        .breadcrumb-container a:hover {{ color: var(--accent); }}
        .breadcrumb-container span:last-child {{ color: var(--text); }}
        footer {{
            text-align: center;
            padding: 40px;
            color: var(--text-muted);
            font-size: 0.85rem;
            border-top: 1px solid var(--border);
            margin-top: 40px;
        }}
        @media (max-width: 768px) {{
            .container {{ padding: 20px 16px; }}
            h1 {{ font-size: 1.8rem; }}
            .nav-links {{ display: none; }}
        }}
    </style>
</head>
<body>
    <nav class="navbar">
        <div class="nav-container">
            <a href="index.html" class="nav-brand">
                <span class="nav-brand-icon">多</span>
                <span>DuoDuo Research</span>
            </a>
            <div class="nav-links">
                <a href="index.html">首页</a>
                <a href="geopolitical-market-report-2026-08-10.html">市场与地缘</a>
                <a href="ai-weekly-report-2026-08-05.html">AI 与科技</a>
                <a href="china-auto-sales-report-2026-08-09.html" class="active">中国汽车</a>
                <a href="#">专题研究</a>
            </div>
        </div>
    </nav>
    <div class="breadcrumb">
        <div class="breadcrumb-container">
            <a href="index.html">研究报告中心</a>
            <span>/</span>
            <a href="china-auto-sales-report-2026-08-09.html">中国汽车</a>
            <span>/</span>
            <span>{title}</span>
        </div>
    </div>

    <div class="container">
        <header>
            <h1>中国汽车智能驾驶趋势观察</h1>
            <p class="subtitle">覆盖中文平台（微博、B站、百度）与全球英文社区（Reddit、YouTube、Hacker News）近30天舆情</p>
            <p class="meta">报告日期：{date_str} · 数据窗口：近30天 · 来源：last30days + last30days-cn 自动生成</p>
        </header>

        <div class="section">
            <h2>中文平台舆情（last30days-cn）</h2>
            <pre>{cn_html}</pre>
        </div>

        <div class="section">
            <h2>全球英文社区舆情（last30days）</h2>
            <pre>{en_html}</pre>
        </div>

        <footer>
            <p>© 2026 DuoDuo Research · 数据由 last30days & last30days-cn 自动生成 · 仅供参考</p>
        </footer>
    </div>
</body>
</html>
"""


def update_index_html(date_str: str, filename: str) -> None:
    """在 index.html 的中国汽车板块插入新的报告卡片和历史链接（幂等，避免重复）。"""
    index_path = REPO_ROOT / "index.html"
    content = index_path.read_text(encoding="utf-8")

    # 已存在则不再插入
    if filename in content:
        return

    # 插入 report-grid 的第一项
    card = f"""                <a href="{filename}" class="report-card">
                    <div class="eyebrow">China Auto Intelligence</div>
                    <h2>中国汽车智能驾驶趋势观察</h2>
                    <p>{date_str} 自动更新：国家自动驾驶强标、享界G9 与华为智驾、理想小米互动、中国EV全球领先与出海争议，覆盖微博/B站/Reddit/YouTube/HN 近30天舆情。</p>
                    <div class="meta">
                        <span>{date_str}</span>
                        <span>→ 查看报告</span>
                    </div>
                </a>
"""
    grid_marker = '            <div class="report-grid">\n                <a href="china-auto-sales-report'
    if grid_marker in content:
        content = content.replace(grid_marker, '            <div class="report-grid">\n' + card + '                <a href="china-auto-sales-report', 1)

    # 插入 history-list
    history_item = f'<a href="{filename}">智驾趋势观察 {date_str}</a>\n                '
    history_marker = '<div class="history-list">\n                <a href="china-auto-sales-report-2026-08-09.html">中国汽车周报 08-09</a>'
    if history_marker in content:
        content = content.replace(history_marker, '<div class="history-list">\n                ' + history_item + '<a href="china-auto-sales-report-2026-08-09.html">中国汽车周报 08-09</a>', 1)

    index_path.write_text(content, encoding="utf-8")


def git_push(date_str: str, filename: str) -> None:
    """git add / commit / push。"""
    cmds = [
        ["git", "add", filename, "index.html"],
        ["git", "commit", "-m", f"Auto-update China auto intelligence report ({date_str})"],
        ["git", "pull", "origin", "main", "--rebase"],
        ["git", "push", "origin", "main"],
    ]
    for cmd in cmds:
        subprocess.run(cmd, cwd=str(REPO_ROOT), check=True, capture_output=True, text=True)


def main() -> None:
    today = datetime.date.today()
    date_str = today.strftime("%Y-%m-%d")
    filename = f"china-auto-intelligent-driving-report-{date_str}.html"

    print(f"[{date_str}] 开始生成中国汽车智能驾驶趋势报告...")

    print("  → 运行 last30days-cn（中文源）...")
    cn_output = run_skill(SKILL_CN, CN_TOPIC, is_cn=True)

    print("  → 运行 last30days（英文/全球源）...")
    en_output = run_skill(SKILL_EN, EN_TOPIC, is_cn=False)

    print("  → 生成 HTML 报告...")
    html = build_report_html(date_str, en_output, cn_output)
    report_path = REPO_ROOT / filename
    report_path.write_text(html, encoding="utf-8")

    print("  → 更新 index.html...")
    update_index_html(date_str, filename)

    print("  → 推送到 GitHub...")
    git_push(date_str, filename)

    print(f"完成：{report_path}")
    print(f"访问地址：https://hosamzj.github.io/sites/{filename}")


if __name__ == "__main__":
    main()
