#!/usr/bin/env python3
"""Generate the weekly English magazines catalog report.

Source data: hehonghui/awesome-english-ebooks (GitHub).
Output:
  - english-magazines-weekly-YYYY-MM-DD.html (dated archive)
  - english-magazines-latest.html (always latest)
Then commit + push to github.com/hosamzj/sites for GitHub Pages.

Auth: uses GITHUB_TOKEN from env if set (the cron wrapper exports `gh auth token`),
falls back to the unauthenticated public API (subject to rate limits).
"""

import datetime
import glob
import html
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import urllib.parse
import urllib.request
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

from PIL import Image

REPO_DIR = Path.home() / "Sites"
UPSTREAM = "hehonghui/awesome-english-ebooks"
RAW_BASE = f"https://raw.githubusercontent.com/{UPSTREAM}/master"
TREE_BASE = f"https://github.com/{UPSTREAM}/tree/master"
API_BASE = f"https://api.github.com/repos/{UPSTREAM}/contents"
FORMATS = ["epub", "mobi", "pdf"]  # display order

MAGAZINES = {
    "economist": {
        "dir": "01_economist",
        "name": "The Economist",
        "zh": "经济学人",
        "frequency": "周刊",
        "update_day": "每周五",
        "color": "#e3120b",
        "desc": "全球政经、商业与科技分析的首选英文周刊",
    },
    "new_yorker": {
        "dir": "02_new_yorker",
        "name": "The New Yorker",
        "zh": "纽约客",
        "frequency": "周刊",
        "update_day": "每周六",
        "color": "#222222",
        "desc": "美国文化、时政评论与深度报道的标志性杂志",
    },
    "atlantic": {
        "dir": "04_atlantic",
        "name": "The Atlantic",
        "zh": "大西洋月刊",
        "frequency": "月刊",
        "update_day": "每月2号",
        "color": "#174ad6",
        "desc": "聚焦美国政治、社会与全球议题的深度月刊",
    },
    "wired": {
        "dir": "05_wired",
        "name": "Wired",
        "zh": "连线",
        "frequency": "月刊",
        "update_day": "每月2号",
        "color": "#000000",
        "desc": "科技、文化、商业与未来趋势的前沿报道",
    },
}

DATE_RE = re.compile(r"(\d{4})\.(\d{2})\.(\d{2})")


def gh_list(path):
    """List a directory via the GitHub contents API. Returns list of entries."""
    url = f"{API_BASE}/{path}" if path else API_BASE
    req = urllib.request.Request(url, headers={
        "Accept": "application/vnd.github+json",
        "User-Agent": "duoduo-english-magazines-report",
    })
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.load(resp)
    if not isinstance(data, list):
        raise RuntimeError(f"Unexpected API response for {path}: {data}")
    return data


def collect_issues(mag_dir):
    """Return list of {date, path, files} for all issue dirs, sorted desc by date."""
    issues = {}

    def walk(path):
        for entry in gh_list(path):
            if entry["type"] != "dir":
                continue
            m = DATE_RE.search(entry["name"])
            if m:
                date = f"{m.group(1)}.{m.group(2)}.{m.group(3)}"
                files = sorted(
                    e["name"] for e in gh_list(entry["path"])
                    if e["type"] == "file"
                    and e["name"].rsplit(".", 1)[-1].lower() in FORMATS
                )
                if files:
                    issues[date] = {"date": date, "path": entry["path"], "files": files}
            else:
                # year subfolder (e.g. 2025/) — recurse one level in
                walk(entry["path"])

    walk(mag_dir)
    return sorted(issues.values(), key=lambda x: x["date"], reverse=True)


def file_url(issue, ext):
    for fname in issue["files"]:
        if fname.rsplit(".", 1)[-1].lower() == ext:
            return f"{RAW_BASE}/{issue['path']}/{urllib.parse.quote(fname)}"
    return None


def make_cover_svg(key, name, date, color):
    """Fallback cover as an inline SVG data URI."""
    short = {"economist": "TE", "new_yorker": "NY", "atlantic": "TA", "wired": "W"}.get(key, "M")
    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="300" height="400" viewBox="0 0 300 400">'
        f'<rect width="300" height="400" fill="{color}"/>'
        f'<rect x="20" y="20" width="260" height="360" fill="none" stroke="rgba(255,255,255,0.25)" stroke-width="2"/>'
        f'<text x="150" y="170" font-family="Georgia,serif" font-size="64" fill="#faf9f5" text-anchor="middle">{short}</text>'
        f'<text x="150" y="230" font-family="Georgia,serif" font-size="26" fill="#faf9f5" text-anchor="middle">{html.escape(name)}</text>'
        f'<text x="150" y="330" font-family="monospace" font-size="20" fill="rgba(255,255,255,0.7)" text-anchor="middle">{date}</text>'
        f'</svg>'
    )
    import base64
    return "data:image/svg+xml;base64," + base64.b64encode(svg.encode()).decode()


PDFTOPPM = shutil.which("pdftoppm") or "/opt/homebrew/bin/pdftoppm"


def download(url, dest):
    """Download a raw.githubusercontent file. Prefer the authenticated GitHub
    Contents API (fast and reliable); fall back to the raw URL."""
    m = re.match(rf"{re.escape(RAW_BASE)}/(.+)", urllib.parse.unquote(url))
    if m and os.environ.get("GITHUB_TOKEN"):
        api = f"https://api.github.com/repos/{UPSTREAM}/contents/{urllib.parse.quote(m.group(1))}"
        req = urllib.request.Request(api, headers={
            "Accept": "application/vnd.github.raw+json",
            "Authorization": f"Bearer {os.environ['GITHUB_TOKEN']}",
            "User-Agent": "duoduo-english-magazines-report",
        })
        with urllib.request.urlopen(req, timeout=180) as resp, open(dest, "wb") as f:
            shutil.copyfileobj(resp, f)
        return
    req = urllib.request.Request(url, headers={"User-Agent": "duoduo-english-magazines-report"})
    with urllib.request.urlopen(req, timeout=180) as resp, open(dest, "wb") as f:
        shutil.copyfileobj(resp, f)


def _to_webp(img_path, out_path, width=600):
    img = Image.open(img_path)
    if img.mode in ("P", "L"):
        img = img.convert("RGB")
    img.thumbnail((width, 800), Image.Resampling.LANCZOS)
    img.save(out_path, "WEBP", quality=85, method=6)
    return out_path.exists()


def pdf_cover_to_webp(pdf_path, out_path):
    with tempfile.TemporaryDirectory() as tmp:
        prefix = Path(tmp) / "cover"
        subprocess.run(
            [PDFTOPPM, "-f", "1", "-l", "1", "-png", "-r", "150", str(pdf_path), str(prefix)],
            check=True, capture_output=True, timeout=120,
        )
        return _to_webp(sorted(Path(tmp).glob("cover-*.png"))[0], out_path)


def epub_cover_to_webp(epub_path, out_path):
    with zipfile.ZipFile(epub_path) as z:
        files = z.namelist()
        cover = next((f for f in files if f.lower() in
                      {"cover.jpg", "cover.jpeg", "cover.png", "cover.webp"}), None)
        if not cover:
            for opf in [f for f in files if f.endswith(".opf")]:
                root = ET.fromstring(z.read(opf).decode("utf-8", "ignore"))
                cover_id = next((m.get("content") for m in root.iter(
                    "{http://www.idpf.org/2007/opf}meta") if m.get("name") == "cover"), None)
                if cover_id:
                    href = next((i.get("href") for i in root.iter(
                        "{http://www.idpf.org/2007/opf}item") if i.get("id") == cover_id), None)
                    cover = next((f for f in files if f.endswith(href)), None) if href else None
                if cover:
                    break
        if not cover:
            return False
        with tempfile.TemporaryDirectory() as tmp:
            tmp_img = Path(tmp) / ("cover" + Path(cover).suffix)
            tmp_img.write_bytes(z.read(cover))
            return _to_webp(tmp_img, out_path)


NEW_COVERS = []  # webp files extracted this run, to be git-added


def ensure_cover(key, mag, issue):
    """Return cover src for the latest issue: local webp, else extract from
    the issue's PDF/EPUB (self-hosted webp), else branded SVG fallback."""
    covers_dir = REPO_DIR / "assets" / "english-magazines-covers"
    out_path = covers_dir / f"{key}_{issue['date']}.webp"
    if out_path.exists():
        return f"assets/english-magazines-covers/{key}_{issue['date']}.webp"
    covers_dir.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        for ext in ("pdf", "epub"):  # prefer PDF (first page is the cover)
            url = file_url(issue, ext)
            if not url:
                continue
            src = Path(tmp) / f"issue.{ext}"
            try:
                download(url, src)
                ok = (pdf_cover_to_webp if ext == "pdf" else epub_cover_to_webp)(src, out_path)
            except Exception as e:
                print(f"[{key}] cover extract from {ext} failed: {e}", file=sys.stderr)
                ok = False
            if ok:
                NEW_COVERS.append(str(out_path.relative_to(REPO_DIR)))
                print(f"[{key}] extracted cover -> {out_path.name}")
                return f"assets/english-magazines-covers/{key}_{issue['date']}.webp"
    return make_cover_svg(key, mag["name"], issue["date"], mag["color"])


def load_css():
    """Reuse the <style> block from the most recent existing report."""
    candidates = sorted(glob.glob(str(REPO_DIR / "english-magazines-weekly-*.html")), reverse=True)
    for path in candidates:
        text = Path(path).read_text(encoding="utf-8")
        m = re.search(r"<style>.*?</style>", text, re.S)
        if m:
            return m.group(0)
    raise RuntimeError("No existing english-magazines report found to reuse CSS from.")


def build_report(css, issues_by_mag, report_date):
    today = report_date
    week = today.isocalendar()[1]
    date_cn = f"{today.year} 年 {today.month:02d} 月 {today.day:02d} 日"

    sections = []
    for key, mag in MAGAZINES.items():
        issues = issues_by_mag.get(key, [])
        if not issues:
            continue
        latest, archives = issues[0], issues[1:13]
        cover = ensure_cover(key, mag, latest)

        buttons = "\n".join(
            f'<a href="{file_url(latest, ext)}" class="download-btn {ext}" target="_blank" rel="noopener">{ext.upper()}</a>'
            for ext in FORMATS if file_url(latest, ext)
        )
        rows = []
        for issue in archives:
            links = "".join(
                f'<a href="{file_url(issue, ext)}" class="download-link {ext}" target="_blank" rel="noopener">{ext.upper()}</a>'
                for ext in FORMATS if file_url(issue, ext)
            )
            rows.append(
                f'''<tr>
                    <td class="archive-date">{issue["date"]}</td>
                    <td class="archive-formats">{links}</td>
                    <td class="archive-source"><a href="{TREE_BASE}/{issue["path"]}" target="_blank" rel="noopener">GitHub ↗</a></td>
                </tr>'''
            )
        sections.append(f'''
        <section class="magazine-section" id="{key}">
            <div class="magazine-header">
                <div class="cover" style="background-color: {mag["color"]}">
                    <img src="{cover}" alt="{html.escape(mag["name"])} {latest["date"]}" loading="lazy">
                </div>
                <div class="magazine-info">
                    <div class="magazine-meta">
                        <span class="frequency">{mag["frequency"]}</span>
                        <span class="update-day">{mag["update_day"]}</span>
                    </div>
                    <h2>{html.escape(mag["name"])} <span class="zh-name">{mag["zh"]}</span></h2>
                    <p class="magazine-desc">{mag["desc"]}</p>
                    <div class="latest-issue">
                        <div class="issue-label">最新一期</div>
                        <div class="issue-date">{latest["date"]}</div>
                        <div class="download-buttons">
                            {buttons}
                        </div>
                    </div>
                </div>
            </div>

            <div class="archive">
                <h4>往期归档</h4>
                <table class="archive-table">
                    <thead><tr><th>日期</th><th>下载格式</th><th>来源</th></tr></thead>
                    <tbody>{"".join(rows)}
                </table>
            </div>
        </section>''')

    return f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>英语外刊精选 | {date_cn} | DuoDuo Research</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
    {css}
</head>
<body>
    <nav class="navbar">
        <div class="nav-container">
            <a href="index.html" class="nav-brand">
                <div class="nav-brand-icon">多</div>
                <span>DuoDuo Research</span>
            </a>
            <div class="nav-links">
                <a href="index.html">首页</a>
                <a href="index.html#geopolitical">市场与地缘</a>
                <a href="index.html#ai-tech">AI 与科技</a>
                <a href="index.html#auto">中国汽车</a>
                <a href="index.html#research" class="active">专题研究</a>
            </div>
        </div>
    </nav>
    <div class="breadcrumb">
        <a href="index.html">研究报告中心</a><span>→</span><a href="index.html#research">专题研究</a><span>→</span>英语外刊精选 | {date_cn}
    </div>

    <header class="hero">
        <div class="container hero-content">
            <div class="eyebrow">English Magazines Weekly</div>
            <h1>英语外刊精选</h1>
            <p class="subtitle">每周精选经济学人、纽约客、大西洋月刊、连线等优质英语外刊，提供 EPUB、MOBI、PDF 多格式下载链接。</p>
            <div class="meta">
                <div class="meta-item"><div class="meta-dot"></div>报告日期：{date_cn}</div>
                <div class="meta-item"><div class="meta-dot"></div>{today.year} 年第 {week} 周</div>
                <div class="meta-item"><div class="meta-dot"></div>来源：hehonghui/awesome-english-ebooks</div>
            </div>
        </div>
    </header>

    <main class="container">
        {"".join(sections)}
    </main>

    <footer class="footer">
        <div class="container">
            <p>数据来源：<a href="https://github.com/hehonghui/awesome-english-ebooks" target="_blank" rel="noopener">awesome-english-ebooks</a></p>
            <p>报告由 DuoDuo Research 自动生成，仅供学习交流使用</p>
        </div>
    </footer>
</body>
</html>'''


def git(*args):
    subprocess.run(["git", "-C", str(REPO_DIR), *args], check=True,
                   stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)


def main():
    os.chdir(REPO_DIR)
    report_date = datetime.date.today()
    css = load_css()

    issues_by_mag = {}
    for key, mag in MAGAZINES.items():
        issues = collect_issues(mag["dir"])
        if issues:
            issues_by_mag[key] = issues
            print(f"[{key}] {len(issues)} issues, latest {issues[0]['date']}")
        else:
            print(f"[{key}] WARNING: no issues found", file=sys.stderr)

    if not issues_by_mag:
        sys.exit("No magazine data collected; aborting.")

    html_out = build_report(css, issues_by_mag, report_date)
    dated_name = f"english-magazines-weekly-{report_date.isoformat()}.html"
    (REPO_DIR / dated_name).write_text(html_out, encoding="utf-8")
    (REPO_DIR / "english-magazines-latest.html").write_text(html_out, encoding="utf-8")

    git("add", dated_name, "english-magazines-latest.html", *NEW_COVERS)
    git("commit", "-m", f"Add English magazines weekly report {report_date.isoformat()}")
    git("pull", "--rebase", "origin", "main")
    git("push", "origin", "main")
    print(f"PUBLISHED {dated_name}")


if __name__ == "__main__":
    main()
