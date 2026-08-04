#!/usr/bin/env python3
"""
王煜全 2024-2026 AI 视频专题自动更新脚本
- 搜索 YouTube 上王煜全相关视频
- 获取 2024-2026 年视频的完整元数据
- 生成 HTML 专题报告并更新 index.html
- git commit/push
"""
import json
import subprocess
from datetime import datetime
from pathlib import Path

REPO_DIR = Path("/private/tmp/sites")
OUTPUT_FILE = REPO_DIR / "wang-yuquan-ai-2024-2026.html"
INDEX_FILE = REPO_DIR / "index.html"

SEARCH_QUERIES = [
    "王煜全",
    "王煜全 演讲",
    "王煜全 访谈",
    "王煜全 前哨",
    "王煜全 AI",
    "王煜全 人工智能",
    "王煜全 2024",
    "王煜全 2025",
    "王煜全 创新地图",
    "王煜全 科技投资",
]

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>王煜全 2024-2026 AI 与科技视频专题 | DuoDuo Research</title>
    <style>
        :root { --bg: #141413; --card: #1e1e1c; --card-hover: #252522; --accent: #c96442; --accent-light: #e07a55; --text: #faf9f5; --text-secondary: #b0aea5; --border: #30302e; }
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'PingFang SC', 'Microsoft YaHei', sans-serif; background-color: var(--bg); color: var(--text); line-height: 1.7; min-height: 100vh; }
        .container { max-width: 960px; margin: 0 auto; padding: 60px 24px 80px; }
        .header { text-align: center; margin-bottom: 48px; }
        .channel-badge { display: inline-flex; align-items: center; gap: 10px; background: var(--card); border: 1px solid var(--border); border-radius: 50px; padding: 8px 18px; font-size: 14px; color: var(--text-secondary); margin-bottom: 24px; }
        .channel-badge img { width: 28px; height: 28px; border-radius: 50%; }
        .title { font-size: 34px; font-weight: 700; margin-bottom: 12px; letter-spacing: -0.02em; }
        .subtitle { font-size: 17px; color: var(--text-secondary); margin-bottom: 24px; max-width: 720px; margin-left: auto; margin-right: auto; }
        .date-range { display: inline-block; background: rgba(201, 100, 66, 0.15); color: var(--accent-light); padding: 6px 14px; border-radius: 20px; font-size: 14px; font-weight: 500; }
        .summary { background: var(--card); border: 1px solid var(--border); border-radius: 20px; padding: 32px; margin-bottom: 40px; }
        .summary h2 { font-size: 20px; margin-bottom: 16px; display: flex; align-items: center; gap: 10px; }
        .summary ul { list-style: none; padding-left: 0; }
        .summary li { padding: 8px 0; padding-left: 24px; position: relative; color: var(--text-secondary); }
        .summary li::before { content: "•"; color: var(--accent); position: absolute; left: 8px; font-weight: bold; }
        .stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr)); gap: 16px; margin-bottom: 40px; }
        .stat-card { background: var(--card); border: 1px solid var(--border); border-radius: 16px; padding: 24px; text-align: center; }
        .stat-card .number { font-size: 32px; font-weight: 700; color: var(--accent-light); margin-bottom: 6px; }
        .stat-card .label { font-size: 13px; color: var(--text-secondary); }
        .video-list { display: flex; flex-direction: column; gap: 24px; }
        .video-card { background: var(--card); border: 1px solid var(--border); border-radius: 20px; overflow: hidden; transition: transform 0.2s ease, border-color 0.2s ease; display: grid; grid-template-columns: 320px 1fr; }
        .video-card:hover { transform: translateY(-2px); border-color: var(--accent); }
        .thumbnail-link { position: relative; display: block; background: #000; min-height: 180px; }
        .thumbnail-link img { width: 100%; height: 100%; object-fit: cover; display: block; }
        .play-icon { position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); width: 52px; height: 52px; background: rgba(201, 100, 66, 0.95); border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 20px; color: white; opacity: 0.9; transition: opacity 0.2s ease; }
        .thumbnail-link:hover .play-icon { opacity: 1; }
        .duration-badge { position: absolute; bottom: 10px; right: 10px; background: rgba(0,0,0,0.8); color: var(--text); padding: 4px 8px; border-radius: 6px; font-size: 12px; font-weight: 600; }
        .source-badge { position: absolute; top: 10px; left: 10px; background: rgba(201, 100, 66, 0.9); color: white; padding: 4px 10px; border-radius: 12px; font-size: 12px; font-weight: 600; }
        .video-info { padding: 28px; }
        .video-info h3 { font-size: 19px; font-weight: 700; margin-bottom: 12px; line-height: 1.4; }
        .video-info h3 a { color: var(--text); text-decoration: none; }
        .video-info h3 a:hover { color: var(--accent-light); }
        .video-meta { display: flex; gap: 16px; font-size: 13px; color: var(--text-secondary); margin-bottom: 12px; flex-wrap: wrap; }
        .theme-tags { display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 14px; }
        .theme-tags span { font-size: 12px; color: var(--accent-light); background: rgba(201, 100, 66, 0.12); padding: 4px 10px; border-radius: 12px; }
        .description { color: var(--text-secondary); font-size: 15px; line-height: 1.6; margin-bottom: 16px; }
        .watch-link { color: var(--accent); text-decoration: none; font-size: 14px; font-weight: 500; }
        .watch-link:hover { color: var(--accent-light); }
        .footer { text-align: center; margin-top: 60px; color: var(--text-secondary); font-size: 14px; }
        .footer a { color: var(--accent); text-decoration: none; }
        .navbar { background: var(--card); border-bottom: 1px solid var(--border); position: sticky; top: 0; z-index: 100; }
        .navbar .nav-container { max-width: 960px; margin: 0 auto; padding: 16px 24px; display: flex; align-items: center; justify-content: space-between; gap: 16px; }
        .nav-brand { display: flex; align-items: center; gap: 10px; color: var(--text); text-decoration: none; font-weight: 700; font-size: 16px; }
        .nav-brand-icon { width: 32px; height: 32px; background: var(--accent); border-radius: 8px; display: flex; align-items: center; justify-content: center; font-size: 14px; color: var(--text); }
        .nav-links { display: flex; gap: 8px; flex-wrap: wrap; }
        .nav-links a { color: var(--text-secondary); text-decoration: none; font-size: 14px; padding: 8px 14px; border-radius: 20px; transition: all 0.2s ease; }
        .nav-links a:hover { color: var(--text); background: rgba(201, 100, 66, 0.1); }
        .nav-links a.active { color: var(--accent-light); background: rgba(201, 100, 66, 0.15); }
        .breadcrumb { max-width: 960px; margin: 0 auto; padding: 20px 24px 0; font-size: 13px; color: var(--text-secondary); }
        .breadcrumb a { color: var(--text-secondary); text-decoration: none; }
        .breadcrumb a:hover { color: var(--accent-light); }
        .breadcrumb span { margin: 0 8px; }
        .notice { background: rgba(201, 100, 66, 0.08); border: 1px solid rgba(201, 100, 66, 0.3); border-radius: 12px; padding: 16px 20px; margin-bottom: 32px; font-size: 14px; color: var(--text-secondary); }
        @media (max-width: 768px) { .title { font-size: 28px; } .video-card { grid-template-columns: 1fr; } .thumbnail-link { height: 200px; } .navbar .nav-container { flex-direction: column; gap: 12px; padding: 16px; } .nav-links a { padding: 6px 10px; font-size: 13px; } .breadcrumb { padding: 16px 16px 0; } }
    </style>
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
                <a href="index.html#ai-tech" class="active">AI 与科技</a>
                <a href="index.html#auto">中国汽车</a>
                <a href="index.html#research">专题研究</a>
            </div>
        </div>
    </nav>
    <div class="breadcrumb">
        <a href="index.html">研究报告中心</a><span>→</span>AI 与科技<span>→</span>王煜全 2024-2026 专题
    </div>
    <div class="container">
        <header class="header">
            <div class="channel-badge">
                <img src="https://yt3.googleusercontent.com/ytc/AIdro_mXl5yWVrKvoM8Fm9Ll0eRr4Zpo6waoBndRvRfQ49bD8w=s72-c-k-c0x00ffffff-no-rj" alt="王煜全">
                <span>王煜全 · 科技投资人</span>
            </div>
            <h1 class="title">王煜全 2024-2026 AI 与科技视频专题</h1>
            <p class="subtitle">汇总王煜全官方频道及第三方频道在 2024-2026 年发布的 AI、科技投资与未来趋势相关视频，附链接与内容概述。</p>
            <div class="date-range">更新时间：__REPORT_DATE__</div>
        </header>

        <div class="notice">
            📌 本专题收集范围包括王煜全 YouTube 官方频道（@王煜全）以及提及/引用王煜全观点的第三方频道。因多数视频未开放字幕，概述基于标题、描述与公开主题推断，不含全文转录。
        </div>

        <div class="stats">
            <div class="stat-card"><div class="number">__TOTAL_VIDEOS__</div><div class="label">收录视频</div></div>
            <div class="stat-card"><div class="number">__OFFICIAL_COUNT__</div><div class="label">官方频道</div></div>
            <div class="stat-card"><div class="number">__THIRD_PARTY_COUNT__</div><div class="label">第三方频道</div></div>
            <div class="stat-card"><div class="number">__TOTAL_HOURS__h+</div><div class="label">总时长</div></div>
        </div>

        <section class="summary">
            <h2>🎯 2024-2026 核心关注方向</h2>
            <ul>
                <li><strong>AI 革命的历史韵脚：</strong>《前哨大会2024》以历次技术革命为镜，预测 AI 泡沫、洗牌与产业落地的时间线。</li>
                <li><strong>AI 时代竞争力与学习法则：</strong>反复强调 AI 作为"外脑"的定位，提出问题驱动学习与持续迭代的认知升级路径。</li>
                <li><strong>数字健康与生物科技：</strong>与 LifeQ CEO 对谈，关注可穿戴设备、连续健康数据与预防医学的产业机会。</li>
                <li><strong>中国企业出海：</strong>分析被动出海与主动布局的区别，强调理解全球政治经济格局的重要性。</li>
                <li><strong>2024 宏观趋势：</strong>地缘政治、AI 崛起与中国优势三大趋势，以及相应的科技投资机遇。</li>
            </ul>
        </section>

        <section class="summary">
            <h2>🏷️ 主题标签分布</h2>
            <ul>
__THEME_LIST__
            </ul>
        </section>

        <section class="video-list">
            <h2 style="font-size: 22px; margin-bottom: 24px;">📹 视频列表（按发布时间倒序）</h2>
__VIDEO_CARDS__
        </section>

        <footer class="footer">
            <p>数据来源：YouTube 公开搜索与频道抓取 · 自动生成于 __REPORT_DATE__</p>
        </footer>
    </div>
</body>
</html>"""


def run_yt_search(query, max_results=20):
    """Run yt-dlp search and return list of video entries."""
    url = f"ytsearch{max_results}:{query}"
    try:
        out = subprocess.run(
            ["yt-dlp", "--flat-playlist", "--dump-single-json", url],
            capture_output=True, text=True, timeout=120
        )
        if out.returncode != 0:
            return []
        data = json.loads(out.stdout)
        if not data:
            return []
        entries = data.get("entries", [])
        if not entries and 'id' in data:
            entries = [data]
        return entries
    except Exception:
        return []


def fetch_video_meta(vid):
    """Fetch full metadata for a single video ID."""
    try:
        out = subprocess.run(
            ["yt-dlp", "--dump-json", f"https://www.youtube.com/watch?v={vid}"],
            capture_output=True, text=True, timeout=60
        )
        if out.returncode != 0:
            return None
        return json.loads(out.stdout)
    except Exception:
        return None


def collect_videos():
    """Collect unique Wang Yuquan videos from multiple searches and own channel."""
    seen = set()
    results = []

    # 1. Own channel videos
    try:
        out = subprocess.run(
            ["yt-dlp", "--dump-json", "--playlist-end", "100",
             "https://www.youtube.com/channel/UCLm1Ufx86Ce1axU5NGBgZmQ/videos"],
            capture_output=True, text=True, timeout=180
        )
        if out.returncode == 0:
            for line in out.stdout.strip().split("\n"):
                try:
                    e = json.loads(line)
                    vid = e.get('id')
                    if vid and vid not in seen:
                        seen.add(vid)
                        results.append(e)
                except Exception:
                    continue
    except Exception:
        pass

    # 2. Searches
    for q in SEARCH_QUERIES:
        entries = run_yt_search(q, max_results=15)
        for e in entries:
            vid = e.get('id')
            if not vid or vid in seen:
                continue
            text = f"{e.get('title','')} {e.get('description','')} {e.get('channel','')}"
            if "王煜全" not in text and "Wang Yuquan" not in text:
                continue
            seen.add(vid)
            results.append(e)

    # 3. Enrich and filter
    enriched = []
    for v in results:
        vid = v.get('id')
        if not vid:
            continue
        if v.get('upload_date'):
            enriched.append(v)
            continue
        full = fetch_video_meta(vid)
        if full and full.get('upload_date'):
            enriched.append(full)

    filtered = []
    for v in enriched:
        upload_date = v.get('upload_date')
        if not upload_date or upload_date[:4] not in ('2024', '2025', '2026'):
            continue
        text = f"{v.get('title','')} {v.get('description','')} {v.get('channel','')}"
        if "王煜全" not in text and "Wang Yuquan" not in text:
            continue
        filtered.append({
            'id': v.get('id'),
            'title': v.get('title'),
            'description': v.get('description', '')[:800],
            'duration': v.get('duration') or 0,
            'duration_string': v.get('duration_string') or '',
            'view_count': v.get('view_count') or 0,
            'upload_date': upload_date,
            'channel': v.get('channel'),
            'channel_id': v.get('channel_id'),
            'thumbnail': v.get('thumbnail'),
            'webpage_url': v.get('webpage_url'),
        })

    filtered.sort(key=lambda x: x['upload_date'], reverse=True)
    return filtered


def analyze_video(v):
    title = v['title']
    desc = v.get('description', '')
    channel = v.get('channel', '')
    source_type = '官方频道' if channel == '王煜全' else '第三方频道'

    if 'LifeQ' in title or 'Wearable' in title:
        themes = ['数字健康', '可穿戴技术', '生物科技']
        summary = '王煜全对谈 LifeQ CEO Laurie，探讨可穿戴设备采集连续健康数据如何改变预防医学和个性化医疗。'
    elif '前哨大会2024' in title:
        themes = ['AI未来预测', '技术革命', '年度演讲']
        summary = '王煜全 2024 年度《前哨大会》演讲，以"历史的韵脚"为主线，分析历次技术革命规律，预测 AI 革命的泡沫、洗牌与落地周期。'
    elif 'AI时代的竞争力法则' in title:
        themes = ['AI竞争力', '学习方法', '企业战略']
        summary = '系统阐述 AI 时代个人与企业如何构建可持续竞争力，从理解 AI 能力边界到建立人机协作框架。'
    elif '3步进入AI学习时代' in title:
        themes = ['AI学习', '教育变革', '终身学习']
        summary = '提出"3 步进入 AI 学习时代"的方法论：把 AI 当作外脑、以问题驱动学习、持续迭代知识体系。'
    elif '2024年的3大趋势和6大机遇' in title or '3大趋势' in title:
        themes = ['2024趋势', '科技投资', '中国机会']
        summary = '王煜全分享 2024 年三大趋势（地缘政治、AI 崛起、中国优势）与六大机遇，强调 AI 是理解世界的新工具。'
    elif '前哨大会2023' in title:
        themes = ['变革时代', '年度演讲', '行动指南']
        summary = '王煜全 2023 年度演讲，聚焦全球经济转型、AI 与自动化浪潮，给出变革时代的行动指南。'
    elif '2029' in title and 'AI泡沫' in title or 'AI泡沫' in title and '破裂' in title or 'AI泡沫' in title and '破灭' in title:
        themes = ['AI泡沫预测', '2029预测', '科技投资']
        summary = '王煜全预测 AI 泡沫将在 2029 年左右破裂，之后经历洗牌，2030 年代真正繁荣，强调当前是布局窗口。'
    elif 'AI预测' in title or '最新AI预测' in title or '八大' in title and 'AI' in title:
        themes = ['AI预测', '趋势洞察', '未来科技']
        summary = '王煜全最新 AI 预测合集，涵盖技术趋势、产业应用和投资机会。'
    elif 'AI制药' in title or '生物制药' in title or 'AI医药' in title:
        themes = ['AI制药', '生物科技', '数字健康']
        summary = '王煜全讨论 AI 在制药和生物科技领域的应用，预测生物制药将在三年内成为热点。'
    elif 'AI编程' in title or '编程' in title and 'AI' in title:
        themes = ['AI编程', '软件开发', '未来工作']
        summary = '王煜全将 AI 编程视为时代信号，认为 2030 年后将迎来繁荣期。'
    elif '数字封建主义' in title or '平台经济' in title or '超级APP' in title:
        themes = ['平台经济', '数字封建主义', 'AI应用']
        summary = '王煜全分析 AI 带来的文明级认知变革，以及超级 APP 对传统数字帝国商业模式的颠覆。'
    elif '刘润' in title or '颠覆生活的可能性' in title or '人工智能有哪些' in title:
        themes = ['AI颠覆', '未来生活', '刘润对话']
        summary = '王煜全做客刘润商学，探讨人工智能将如何颠覆日常生活、工作方式与商业形态。'
    elif '出海' in title or '出海都有哪些坑' in title:
        themes = ['企业出海', '全球化', '商业战略']
        summary = '王煜全谈中国企业出海：被动出海必然大浪淘沙，只有主动分析未来政治经济格局的企业才能成为真正赢家。'
    elif 'AI取代' in title or ('普通人' in title and 'AI' in title):
        themes = ['AI焦虑', '普通人应对', '认知提升']
        summary = '基于王煜全科技史观点，讨论 AI 时代普通人如何抓住机遇、避免被替代。'
    elif '马斯克逻辑' in title or '火星到服务' in title:
        themes = ['马斯克', '服务规模化', '二次创作']
        summary = '基于王煜全演讲的二次创作，解读马斯克从火星探索到服务未来的商业逻辑。'
    else:
        themes = ['科技创新', '产业观察']
        summary = desc[:120] if desc else '王煜全相关科技投资与产业趋势内容。'

    return source_type, themes, summary


def build_video_card(v):
    source_type, themes, summary = analyze_video(v)
    upload_date_fmt = f"{v['upload_date'][:4]}.{v['upload_date'][4:6]}.{v['upload_date'][6:]}"
    theme_tags = ''.join(f'<span>{t}</span>' for t in themes)
    return f'''<div class="video-card">
    <a href="https://www.youtube.com/watch?v={v['id']}" target="_blank" class="thumbnail-link">
        <img src="{v['thumbnail']}" alt="{v['title']}" loading="lazy">
        <div class="play-icon">▶</div>
        <div class="duration-badge">{v['duration_string']}</div>
        <div class="source-badge">{source_type}</div>
    </a>
    <div class="video-info">
        <h3><a href="https://www.youtube.com/watch?v={v['id']}" target="_blank">{v['title']}</a></h3>
        <div class="video-meta">
            <span class="date">📅 {upload_date_fmt}</span>
            <span class="channel">📺 {v['channel']}</span>
            <span class="duration">⏱ {v['duration_string']}</span>
        </div>
        <div class="theme-tags">{theme_tags}</div>
        <p class="description">{summary}</p>
        <a href="https://www.youtube.com/watch?v={v['id']}" target="_blank" class="watch-link">在 YouTube 观看 →</a>
    </div>
</div>'''


def generate_report(videos):
    report_date = datetime.now().strftime('%Y-%m-%d')

    total = len(videos)
    official = len([v for v in videos if v.get('channel') == '王煜全'])
    third_party = total - official
    total_hours = sum(v.get('duration', 0) for v in videos) // 3600

    video_cards = '\n'.join(build_video_card(v) for v in videos)

    all_themes = {}
    for v in videos:
        _, themes, _ = analyze_video(v)
        for t in themes:
            all_themes[t] = all_themes.get(t, 0) + 1
    top_themes = sorted(all_themes.items(), key=lambda x: x[1], reverse=True)
    theme_list = ''.join(f'<li><strong>{t[0]}</strong>（{t[1]} 个视频）</li>' for t in top_themes)

    html = HTML_TEMPLATE
    html = html.replace('__REPORT_DATE__', report_date)
    html = html.replace('__TOTAL_VIDEOS__', str(total))
    html = html.replace('__OFFICIAL_COUNT__', str(official))
    html = html.replace('__THIRD_PARTY_COUNT__', str(third_party))
    html = html.replace('__TOTAL_HOURS__', str(total_hours))
    html = html.replace('__THEME_LIST__', theme_list)
    html = html.replace('__VIDEO_CARDS__', video_cards)
    return html


def update_index_html():
    """Ensure index.html links to the report."""
    content = INDEX_FILE.read_text(encoding='utf-8')
    if 'wang-yuquan-ai-2024-2026.html' in content:
        return
    # Add card to AI section if not present
    if 'wang-yuquan-ai-' not in content:
        marker = '<section class="section" id="ai-tech">'
        grid_marker = '<div class="report-grid">'
        ai_section_start = content.find(marker)
        if ai_section_start != -1:
            grid_pos = content.find(grid_marker, ai_section_start)
            if grid_pos != -1:
                card = '''\n                <a href="wang-yuquan-ai-2024-2026.html" class="report-card">
                    <div class="eyebrow">Creator Insights</div>
                    <h2>王煜全 AI 长播客专题</h2>
                    <p>汇总王煜全官方频道及第三方频道在 2024-2026 年发布的 AI、科技投资与未来趋势相关视频，附链接与内容概述。</p>
                    <div class="meta">
                        <span>2024-2026</span>
                        <span>→ 查看报告</span>
                    </div>
                </a>'''
                content = content[:grid_pos + len(grid_marker)] + card + content[grid_pos + len(grid_marker):]
        history_marker = '<div class="history-list">'
        ai_history_pos = content.find(history_marker, ai_section_start)
        if ai_history_pos != -1:
            link = '\n                <a href="wang-yuquan-ai-2024-2026.html">王煜全 2024-2026</a>'
            content = content[:ai_history_pos + len(history_marker)] + link + content[ai_history_pos + len(history_marker):]
        INDEX_FILE.write_text(content, encoding='utf-8')


def git_push():
    """Commit and push changes."""
    try:
        subprocess.run(["git", "add", "-A"], cwd=REPO_DIR, check=True)
        subprocess.run(
            ["git", "commit", "-m", f"auto: update 王煜全 2024-2026 专题 ({datetime.now().strftime('%Y-%m-%d')})"],
            cwd=REPO_DIR, check=False
        )
        for _ in range(3):
            subprocess.run(
                ["git", "pull", "origin", "main", "--rebase"],
                cwd=REPO_DIR, capture_output=True, text=True, check=False
            )
            result = subprocess.run(
                ["git", "push", "origin", "main"],
                cwd=REPO_DIR, capture_output=True, text=True, check=False
            )
            if result.returncode == 0:
                print("Pushed to GitHub Pages")
                return
            time.sleep(2)
        print("Push failed:", result.stderr)
    except Exception as e:
        print(f"Git error: {e}")


def main():
    print("Collecting Wang Yuquan 2024-2026 videos...")
    videos = collect_videos()
    print(f"Found {len(videos)} videos")

    if not videos:
        print("No videos found, skipping report generation.")
        return

    print("Generating report...")
    html = generate_report(videos)
    OUTPUT_FILE.write_text(html, encoding='utf-8')

    print("Updating index.html...")
    update_index_html()

    print("Pushing to GitHub...")
    import time
    git_push()

    print(f"Done. Report: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
