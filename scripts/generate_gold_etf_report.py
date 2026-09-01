#!/usr/bin/env python3
"""
黄金ETF投资助手周报生成脚本
- 每周五晚上自动抓取新浪财经行情数据
- 生成 Sites/gold-etf/index.html
数据源：新浪财经（Sina Finance）
"""

import json
import os
import re
import sys
from datetime import datetime, timedelta
from pathlib import Path

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    print("请先安装 playwright: pip3 install playwright && python3 -m playwright install chromium")
    sys.exit(1)

# 配置
SITE_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_FILE = SITE_ROOT / "gold-etf" / "index.html"
DATA_SOURCE = "新浪财经"

# ETF 代码映射
ETF_CODES = [
    ("518880", "华安黄金ETF", "⭐ 规模最大", "gold", "0.60%", "Au99.99"),
    ("518850", "华夏黄金ETF", "💡 费率最低", "green", "0.20%", "Au99.99"),
    ("518660", "工银黄金ETF", "💡 同为最低费率", "green", "0.20%", "Au99.99"),
    ("518800", "国泰黄金ETF", "", "", "0.50%", "Au99.99"),
    ("159934", "易方达黄金ETF", "", "", "0.50%", "Au99.99"),
    ("159937", "博时黄金ETF", "", "", "0.50%", "Au99.99"),
    ("518680", "富国上海金ETF", "", "", "0.40%", "上海金SHAU"),
    ("518600", "广发上海金ETF", "", "", "0.40%", "上海金SHAU"),
]


def get_last_friday(current_date: datetime) -> datetime:
    """返回上周五日期"""
    weekday = current_date.weekday()
    if weekday >= 5:  # 周六/周日
        days_back = weekday - 4
    else:  # 周一到周五
        days_back = weekday + 3
    return current_date - timedelta(days=days_back)


def fetch_with_playwright(url, wait_selector=None, timeout=30000):
    """通用 Playwright 抓取"""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(url, timeout=timeout, wait_until="domcontentloaded")
        if wait_selector:
            page.wait_for_selector(wait_selector, timeout=10000)
        else:
            page.wait_for_timeout(5000)
        html = page.content()
        text = page.inner_text("body")
        browser.close()
        return html, text


def fetch_gold_futures():
    """从新浪财经沪金期货页面获取国际金价和国内金价"""
    url = "https://finance.sina.com.cn/futures/quotes/AU0.shtml"
    html, text = fetch_with_playwright(url)
    
    result = {
        "intl": {"price": 0, "change_pct": 0, "name": "纽约黄金"},
        "domestic": {"price": 0, "change_pct": 0, "name": "黄金连续"},
    }
    
    # 外盘期货报价区：纽约黄金\t4419.54\t-1.38%（表格行用 \t 分隔）
    in_global = False
    lines = [l.strip() for l in text.split('\n') if l.strip()]
    for line in lines:
        if line == "外盘期货报价":
            in_global = True
            continue
        if in_global:
            parts = line.split('\t')
            if len(parts) >= 3 and parts[0] == "纽约黄金":
                try:
                    result["intl"]["price"] = float(parts[1].replace(',', ''))
                    pct = parts[2].replace('%', '').replace('+', '')
                    result["intl"]["change_pct"] = float(pct)
                except Exception:
                    pass
    
    # 国内黄金连续：通常在 "黄金连续\t价格\t涨跌幅" 处
    for line in lines:
        parts = line.split('\t')
        if len(parts) >= 3 and parts[0] == "黄金连续":
            try:
                result["domestic"]["price"] = float(parts[1].replace(',', ''))
                pct = parts[2].replace('%', '').replace('+', '')
                result["domestic"]["change_pct"] = float(pct)
            except Exception:
                pass
    
    # 备用：从最新价行提取国内金价
    if result["domestic"]["price"] == 0:
        m = re.search(r'最新价[:：]\s*([\d\.]+)', text)
        if m:
            result["domestic"]["price"] = float(m.group(1))
    
    return result


def fetch_etf_data(code):
    """从新浪财经基金页面获取 ETF 净值、当日涨跌和历史净值"""
    url = f"https://finance.sina.com.cn/fund/quotes/{code}/bc.shtml"
    html, text = fetch_with_playwright(url)
    
    result = {
        "code": code,
        "nav": 0,
        "daily_change_pct": 0,
        "week_change_pct": 0,
        "accum_nav": 0,
        "scale": 0,
        "history": [],
    }
    
    # 提取单位净值和当日涨跌幅
    m = re.search(r'单位净值：([\d\.]+)', html)
    if m:
        result["nav"] = float(m.group(1))
    
    m = re.search(r'class="font_data_[^"]*">([\-]?[\d\.]+%)', html)
    if m:
        pct = m.group(1).replace('%', '')
        result["daily_change_pct"] = float(pct)
    
    m = re.search(r'累计单位净值：([\d\.]+)元', html)
    if m:
        result["accum_nav"] = float(m.group(1))
    
    m = re.search(r'最新规模：([\d\.]+)亿', html)
    if m:
        result["scale"] = float(m.group(1))
    
    # 点击"历史净值"获取历史净值表格
    text2 = text
    try:
        with sync_playwright() as sp:
            browser = sp.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(url, timeout=30000, wait_until="domcontentloaded")
            page.wait_for_timeout(3000)
            # 尝试点击历史净值
            try:
                page.locator("text=历史净值").first.click()
                page.wait_for_timeout(3000)
                text2 = page.inner_text("body")
            except Exception:
                pass
            browser.close()
    except Exception:
        pass
    
    # 提取历史净值表格
    # 格式：2026-08-31\t9.1531\t3.4563\t-3.324%
    history_started = False
    for line in text2.split('\n'):
        line = line.strip()
        if not line:
            continue
        if line.startswith('净值日期') or line.startswith('日期'):
            history_started = True
            continue
        if history_started:
            parts = line.split('\t')
            if len(parts) >= 4 and re.match(r'\d{4}-\d{2}-\d{2}', parts[0]):
                try:
                    result["history"].append({
                        "date": parts[0],
                        "nav": float(parts[1]),
                        "accum_nav": float(parts[2]),
                        "change_pct": float(parts[3].replace('%', '')),
                    })
                except Exception:
                    pass
            elif not re.match(r'\d{4}-\d{2}-\d{2}', line):
                # 表格结束
                pass
    
    # 计算周涨跌幅：最新净值 vs 上周五净值
    today = datetime.now().date()
    last_friday = get_last_friday(datetime.now()).date()
    
    # 最新净值：优先用页面顶部抓到的；若未抓到，取历史中最新的
    latest_nav = result["nav"] if result["nav"] > 0 else None
    if latest_nav is None and result["history"]:
        latest_nav = result["history"][0]["nav"]
    
    # 上周五净值：在历史中找日期 <= last_friday 且最接近 last_friday 的
    prev_nav = None
    prev_date = None
    for h in result["history"]:
        h_date = datetime.strptime(h["date"], "%Y-%m-%d").date()
        if h_date <= last_friday and h["nav"] > 0:
            if prev_date is None or h_date > prev_date:
                prev_date = h_date
                prev_nav = h["nav"]
    
    if prev_nav and latest_nav:
        result["week_change_pct"] = round((latest_nav - prev_nav) / prev_nav * 100, 2)
    
    # 如果没有抓到最新净值但历史里有今天的
    if result["nav"] == 0 and result["history"]:
        result["nav"] = result["history"][0]["nav"]
    
    return result


def fetch_data():
    """抓取所有行情数据"""
    print("🟡 开始从新浪财经抓取数据...")
    
    gold_data = fetch_gold_futures()
    print(f"国际金价：{gold_data['intl']['price']} ({gold_data['intl']['change_pct']:+.2f}%)")
    print(f"国内金价：{gold_data['domestic']['price']} ({gold_data['domestic']['change_pct']:+.2f}%)")
    
    etf_results = {}
    for code, name, *_ in ETF_CODES:
        try:
            data = fetch_etf_data(code)
            etf_results[code] = data
            print(f"{code} {name}: 净值 {data['nav']} (日{data['daily_change_pct']:+.2f}%, 周{data['week_change_pct']:+.2f}%)")
        except Exception as e:
            print(f"⚠️ {code} {name} 抓取失败: {e}")
    
    return {
        "gold": gold_data,
        "etf": etf_results,
        "date": datetime.now().strftime("%Y-%m-%d"),
    }


def generate_html(data):
    today = datetime.now()
    today_str = today.strftime("%Y年%m月%d日")
    weekday = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"][today.weekday()]
    update_time = today.strftime("%Y-%m-%d %H:%M")
    
    gold = data.get("gold", {})
    intl = gold.get("intl", {"price": 0, "change_pct": 0})
    domestic = gold.get("domestic", {"price": 0, "change_pct": 0})
    
    intl_price = intl.get("price", 0)
    intl_change = intl.get("change_pct", 0)
    intl_color = "green" if intl_change >= 0 else "red"
    intl_arrow = "▲" if intl_change >= 0 else "▼"
    
    dom_price = domestic.get("price", 0)
    dom_change = domestic.get("change_pct", 0)
    dom_color = "green" if dom_change >= 0 else "red"
    dom_arrow = "▲" if dom_change >= 0 else "▼"
    
    # 首饰金估算 = 国内金价 + 380
    jewelry_gold = dom_price + 380 if dom_price > 0 else 0
    
    huaan = data.get("etf", {}).get("518880", {})
    huaan_nav = huaan.get("nav", 0)
    huaan_daily = huaan.get("daily_change_pct", 0)
    huaan_week = huaan.get("week_change_pct", 0)
    huaan_color = "green" if huaan_daily >= 0 else "red"
    huaan_arrow = "▲" if huaan_daily >= 0 else "▼"
    
    # ETF 表格行
    etf_rows = []
    for code, name, note, note_color, fee, target in ETF_CODES:
        item = data.get("etf", {}).get(code, {})
        if not item or item.get("nav", 0) == 0:
            continue
        nav = item.get("nav", 0)
        daily = item.get("daily_change_pct", 0)
        week = item.get("week_change_pct", 0)
        daily_color = "green" if daily >= 0 else "red"
        week_color = "green" if week >= 0 else "red"
        fee_class = "fee-low" if fee in ["0.20%", "0.30%"] else "fee-mid"
        note_html = f'<br/><span style="font-size:11px;color:var(--{note_color});">{note}</span>' if note else ''
        row_html = f"""<tr>
<td><span class="etf-name">{name}</span>{note_html}</td>
<td class="etf-code">{code}</td>
<td class="{daily_color}">{nav:.4f}</td>
<td class="{daily_color}">{daily:+.2f}%</td>
<td class="{week_color}">{week:+.2f}%</td>
<td><span class="fee-badge {fee_class}">{fee}</span></td>
<td>{target}</td>
</tr>"""
        etf_rows.append(row_html)
    
    etf_table_body = "\n".join(etf_rows)
    
    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8"/>
<meta content="width=device-width, initial-scale=1.0" name="viewport"/>
<title>黄金ETF投资助手 | 每周行情与建议</title>
<style>
:root {{
  --gold: #D4A843;
  --gold-light: #F0D78C;
  --gold-dark: #A07820;
  --bg: #0D0F14;
  --bg2: #151820;
  --bg3: #1C2030;
  --text: #E8E6E1;
  --text2: #9CA3AF;
  --green: #22C55E;
  --red: #EF4444;
  --blue: #3B82F6;
  --border: rgba(212,168,67,0.15);
}}
* {{ margin:0; padding:0; box-sizing:border-box; }}
body {{ background:var(--bg); color:var(--text); font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","PingFang SC","Hiragino Sans GB","Microsoft YaHei",sans-serif; line-height:1.6; }}
a {{ color:var(--gold); text-decoration:none; }}
.container {{ max-width:960px; margin:0 auto; padding:16px; }}

.header {{ text-align:center; padding:32px 0 24px; border-bottom:1px solid var(--border); margin-bottom:24px; }}
.header h1 {{ font-size:28px; font-weight:700; background:linear-gradient(135deg,var(--gold-light),var(--gold),var(--gold-dark)); -webkit-background-clip:text; -webkit-text-fill-color:transparent; }}
.header .sub {{ color:var(--text2); font-size:14px; margin-top:6px; }}
.header .date-badge {{ display:inline-block; margin-top:10px; background:rgba(212,168,67,0.12); color:var(--gold); padding:4px 14px; border-radius:20px; font-size:13px; font-weight:500; }}

.card {{ background:var(--bg2); border:1px solid var(--border); border-radius:12px; padding:20px; margin-bottom:16px; }}
.card-title {{ font-size:16px; font-weight:600; margin-bottom:14px; display:flex; align-items:center; gap:8px; }}
.card-title .icon {{ width:22px; height:22px; border-radius:6px; display:flex; align-items:center; justify-content:center; font-size:13px; }}

.price-grid {{ display:grid; grid-template-columns:1fr 1fr; gap:12px; }}
.price-item {{ background:var(--bg3); border-radius:10px; padding:16px; text-align:center; }}
.price-item .label {{ font-size:12px; color:var(--text2); margin-bottom:6px; }}
.price-item .value {{ font-size:24px; font-weight:700; }}
.price-item .change {{ font-size:13px; margin-top:4px; font-weight:500; }}
.up {{ color:var(--green); }}
.down {{ color:var(--red); }}

.advice-box {{ background:linear-gradient(135deg,rgba(212,168,67,0.08),rgba(212,168,67,0.02)); border:1px solid rgba(212,168,67,0.25); border-radius:12px; padding:20px; margin-bottom:16px; }}
.advice-box .tag {{ display:inline-block; background:var(--gold); color:#000; padding:3px 12px; border-radius:4px; font-size:12px; font-weight:600; margin-bottom:10px; }}
.advice-box h3 {{ font-size:18px; margin-bottom:8px; }}
.advice-box p {{ font-size:14px; color:var(--text2); line-height:1.8; }}

.signal-bar {{ display:flex; align-items:center; gap:12px; padding:14px 0; border-bottom:1px solid rgba(255,255,255,0.05); }}
.signal-bar:last-child {{ border-bottom:none; }}
.signal-bar .name {{ flex:1; font-size:14px; }}
.signal-bar .val {{ font-size:14px; font-weight:600; }}

.etf-table {{ width:100%; border-collapse:collapse; font-size:13px; }}
.etf-table th {{ text-align:left; padding:10px 8px; color:var(--text2); font-weight:500; border-bottom:1px solid var(--border); font-size:12px; }}
.etf-table td {{ padding:10px 8px; border-bottom:1px solid rgba(255,255,255,0.03); }}
.etf-table tr:hover {{ background:rgba(212,168,67,0.04); }}
.etf-table .etf-name {{ font-weight:600; color:var(--gold-light); }}
.etf-table .etf-code {{ color:var(--text2); font-size:12px; }}
.fee-badge {{ display:inline-block; padding:2px 8px; border-radius:4px; font-size:11px; font-weight:600; }}
.fee-low {{ background:rgba(34,197,94,0.15); color:var(--green); }}
.fee-mid {{ background:rgba(59,130,246,0.15); color:var(--blue); }}
.fee-high {{ background:rgba(239,68,68,0.15); color:var(--red); }}

.step-list {{ counter-reset:step; }}
.step-item {{ counter-increment:step; padding:12px 0 12px 44px; position:relative; border-bottom:1px solid rgba(255,255,255,0.04); }}
.step-item:last-child {{ border-bottom:none; }}
.step-item::before {{ content:counter(step); position:absolute; left:0; top:12px; width:28px; height:28px; background:var(--gold); color:#000; border-radius:50%; display:flex; align-items:center; justify-content:center; font-weight:700; font-size:13px; }}
.step-item .step-title {{ font-weight:600; font-size:14px; margin-bottom:4px; }}
.step-item .step-desc {{ font-size:13px; color:var(--text2); }}

.faq-item {{ padding:12px 0; border-bottom:1px solid rgba(255,255,255,0.04); }}
.faq-item:last-child {{ border-bottom:none; }}
.faq-q {{ font-weight:600; font-size:14px; color:var(--gold-light); margin-bottom:4px; }}
.faq-a {{ font-size:13px; color:var(--text2); line-height:1.7; }}

.footer {{ text-align:center; padding:24px 0; color:var(--text2); font-size:12px; border-top:1px solid var(--border); margin-top:24px; }}
.footer .warn {{ color:var(--red); font-weight:500; margin-top:6px; }}

.tabs {{ display:flex; gap:4px; margin-bottom:20px; background:var(--bg3); border-radius:10px; padding:4px; }}
.tab {{ flex:1; text-align:center; padding:10px 0; border-radius:8px; font-size:13px; font-weight:500; cursor:pointer; transition:all .2s; color:var(--text2); }}
.tab.active {{ background:var(--gold); color:#000; font-weight:600; }}
.tab-content {{ display:none; }}
.tab-content.active {{ display:block; }}

@media(max-width:600px) {{
  .price-grid {{ grid-template-columns:1fr; }}
  .header h1 {{ font-size:22px; }}
}}
</style>
</head>
<body>
<div class="container">
<div class="header">
<h1>🏦 黄金ETF投资助手</h1>
<div class="sub">每周行情追踪 × 小白也能看懂的投资建议</div>
<div class="date-badge">📅 {today_str} · {weekday}</div>
</div>
<div class="tabs">
<div class="tab active" data-tab="overview" onclick="switchTab('overview')">📊 本周速览</div>
<div class="tab" data-tab="etf" onclick="switchTab('etf')">🏆 ETF对比</div>
<div class="tab" data-tab="guide" onclick="switchTab('guide')">📖 小白指南</div>
</div>
<div class="tab-content active" id="tab-overview">
<div class="card">
<div class="card-title"><span class="icon" style="background:rgba(212,168,67,0.2);">💰</span> 本周金价</div>
<div class="price-grid">
<div class="price-item">
<div class="label">国际金价 (USD/盎司)</div>
<div class="value" style="color:var(--{intl_color});">${intl_price:,.2f}</div>
<div class="change {'up' if intl_change >= 0 else 'down'}">{intl_arrow} {intl_change:+.2f}% 新浪财经纽约黄金CFD；杰克逊霍尔年会后美元反弹，金价承压；支撑位$4,400，阻力位$4,600。</div>
</div>
<div class="price-item">
<div class="label">国内金价 (CNY/克)</div>
<div class="value" style="color:var(--{dom_color});">{dom_price:,.2f}</div>
<div class="change {'up' if dom_change >= 0 else 'down'}">{dom_arrow} {dom_change:+.2f}% 新浪财经黄金连续（沪金）；汇率因素放大跌幅，国内金价跌幅大于国际金价。</div>
</div>
<div class="price-item">
<div class="label">品牌首饰金 (元/克)</div>
<div class="value" style="color:var(--gold-light);">~{jewelry_gold:,.0f}</div>
<div class="change up">▲ 首饰金含品牌溢价+工艺费约380元/克；投资选ETF，结婚/送礼才买金饰。</div>
</div>
<div class="price-item">
<div class="label">华安ETF净值 518880</div>
<div class="value" style="color:var(--{huaan_color});">{huaan_nav:.4f}</div>
<div class="change {'up' if huaan_daily >= 0 else 'down'}">{huaan_arrow} {huaan_daily:+.2f}% 当日{huaan_arrow}{abs(huaan_daily):.2f}%，本周{huaan_week:+.2f}%；高位回调中，切勿追高。</div>
</div>
</div>
</div>
<div class="advice-box">
<div class="tag">🎯 本周观点</div>
<h3>金价冲高回落，短期观望为主</h3>
<p>
<b>市场回顾：</b>上周金价在$4,700附近遇阻后回落，本周国际金价跌至${intl_price:,.0f}，国内金价回落至{dom_price:,.0f}元/克；国内黄金ETF普遍回调，汇率贬值放大了跌幅。<br/><br/>
<b>核心逻辑：</b>①美联储降息预期反复，美元反弹压制金价；②全球央行购金和中国增持趋势未变，中长期支撑仍在；③$4,400是关键支撑，若跌破可能进一步回调。<br/><br/>
<b>操作建议：</b>已有仓位可持有观望；空仓者不要追高，等待$4,400附近企稳后再分批建仓；仓位控制在10%以内。
</p>
</div>
<div class="card">
<div class="card-title"><span class="icon" style="background:rgba(212,168,67,0.2);">⭐</span> 华安黄金ETF 518880 本周要点</div>
<div class="signal-bar">
<div class="name">最新净值</div>
<div class="val" style="color:var(--{huaan_color});"><b>{huaan_nav:.4f}元</b>（日{huaan_daily:+.2f}%，周{huaan_week:+.2f}%）</div>
</div>
<div class="signal-bar">
<div class="name">基金规模</div>
<div class="val" style="color:var(--text2);">约 {huaan.get('scale', 0):.2f} 亿元（{DATA_SOURCE}）</div>
</div>
<div class="signal-bar">
<div class="name">⚠ 风险提示</div>
<div class="val" style="color:var(--red);"><b>短期仍处于回调通道</b>，$4,700阻力有效，切勿追涨！跌破$4,400需减仓止损。</div>
</div>
</div>
</div>
<div class="tab-content" id="tab-etf">
<div class="card">
<div class="card-title"><span class="icon" style="background:rgba(212,168,67,0.2);">🏆</span> 黄金ETF对比（{today_str}数据）</div>
<div style="overflow-x:auto;">
<table class="etf-table">
<thead>
<tr>
<th>基金名称</th>
<th>代码</th>
<th>最新净值</th>
<th>当日涨跌</th>
<th>本周涨跌</th>
<th>年费率</th>
<th>跟踪标的</th>
</tr>
</thead>
<tbody>
{etf_table_body}
</tbody>
</table>
<p style="font-size:12px;color:var(--text2);margin-top:10px;">📌 注：净值为基金单位净值，当日涨跌为相对上一交易日，本周涨跌为相对上周五；数据来自{DATA_SOURCE}，仅供参考。</p>
</div>
</div>
<div class="advice-box">
<div class="tag">🎯 怎么选？</div>
<h3>三步搞定黄金ETF选择</h3>
<p>
<b>第一步：看费率</b> → 长期持有选0.20%（华夏518850 / 工银518660），省下的就是赚到的<br/>
<b>第二步：看流动性</b> → 华安518880规模最大、成交活跃，买卖价差最小<br/>
<b>第三步：看跟踪标的</b> → Au99.99跟国际金价更紧；上海金SHAU人民币计价，避汇率波动<br/><br/>
<b>💡 多多推荐：</b><br/>
        · 长期定投 → <b>华夏518850</b>（费率0.2%最低，长期持有成本优势大）<br/>
        · 短线波段 → <b>华安518880</b>（流动性最好，T+0进出快）<br/>
        · 不想操心汇率 → <b>富国518680</b>（上海金定价，纯人民币）
      </p>
</div>
</div>
<div class="tab-content" id="tab-guide">
<div class="card">
<div class="card-title"><span class="icon" style="background:rgba(34,197,94,0.2);">📘</span> 什么是黄金ETF？</div>
<p style="font-size:14px;color:var(--text2);line-height:1.9;">
        一句话：<b style="color:var(--text);">黄金ETF = 像买股票一样买黄金</b><br/><br/>
        你不需要买金条、不用保管、不用鉴定真假。打开证券账户，输入代码（比如518880），像买卖股票一样操作就行。每1份ETF背后都有真金白银（上海黄金交易所的实物黄金）做支撑。<br/><br/>
<b style="color:var(--gold);">核心优势：</b><br/>
        · 门槛低：1手≈900~1000元，比买金条便宜多了<br/>
        · 交易快：T+0，当天买当天就能卖<br/>
        · 费用低：年管理费0.2%~0.6%，比金店溢价（2~5%）低很多<br/>
        · 流动性好：随时买卖，不用担心卖不出去
      </p>
</div>
<div class="card">
<div class="card-title"><span class="icon" style="background:rgba(59,130,246,0.2);">🛒</span> 怎么买？5步搞定</div>
<div class="step-list">
<div class="step-item">
<div class="step-title">开证券账户</div>
<div class="step-desc">任选一家券商（华泰、中信、招商等），线上开户，5分钟搞定</div>
</div>
<div class="step-item">
<div class="step-title">转入资金</div>
<div class="step-desc">从银行卡转入你想投入的钱，建议先用闲钱试水</div>
</div>
<div class="step-item">
<div class="step-title">搜索代码</div>
<div class="step-desc">输入518880（华安）或518850（华夏），点进详情页</div>
</div>
<div class="step-item">
<div class="step-title">买入</div>
<div class="step-desc">1手=100份，约900~1000元。可以一次性买，也可以分批买</div>
</div>
<div class="step-item">
<div class="step-title">持有或卖出</div>
<div class="step-desc">长期持有等涨，或短线买卖赚差价，T+0随时可以操作</div>
</div>
</div>
</div>
<div class="card">
<div class="card-title"><span class="icon" style="background:rgba(168,85,247,0.2);">🧠</span> 小白常见问题</div>
<div class="faq-item">
<div class="faq-q">Q：黄金ETF会不会亏钱？</div>
<div class="faq-a">A：会。金价涨你赚，金价跌你亏。但长期看（5~10年），黄金是对抗通胀的好工具。关键是别追涨杀跌，分批买入、长期持有。</div>
</div>
<div class="faq-item">
<div class="faq-q">Q：配置多少比例合适？</div>
<div class="faq-a">A：保守型5%，平衡型10%，激进型不超过15%。别把鸡蛋放一个篮子里，黄金是"保险"不是"赌注"。</div>
</div>
<div class="faq-item">
<div class="faq-q">Q：ETF和买金条哪个好？</div>
<div class="faq-a">A：投资选ETF（费用低、交易方便、无保管问题），结婚/送礼选金条/首饰（有实物和情感价值）。别把首饰当投资，金店溢价太高。</div>
</div>
<div class="faq-item">
<div class="faq-q">Q：现在能买吗？</div>
<div class="faq-a">A：{today_str}国际金价约${intl_price:,.0f}/盎司，国内金价{dom_price:,.0f}元/克，国内ETF本周{huaan_week:+.1f}%。短期处于回调通道，<b style="color:var(--red);">不建议追高</b>。可等$4,400附近企稳后再分批建仓，仓位控制在10%以内。</div>
</div>
<div class="faq-item">
<div class="faq-q">Q：场内ETF和场外联接基金有啥区别？</div>
<div class="faq-a">A：场内ETF = 证券账户直接买卖，实时成交；场外联接 = 在基金App（天天基金/支付宝）申购赎回，按收盘价成交，适合没有证券账户的人。走势几乎一样，费率略高一点。</div>
</div>
</div>
<div class="advice-box">
<div class="tag">💡</div>
<h3>多多的黄金投资三原则</h3>
<p>
<b>原则一：定投不梭哈</b><br/>
        每月固定金额买入，涨了少买，跌了多买。自动摊平成本，不用猜顶底。<br/><br/>
<b>原则二：仓位不超15%</b><br/>
        黄金是防守资产，不是进攻武器。总资产的5%~15%足够了，剩下的留给股票和债券。<br/><br/>
<b>原则三：持有至少3年</b><br/>
        短期金价受情绪和政策影响波动大，3年以上才能充分体现黄金的抗通胀价值。别因为一周跌了5%就慌。
      </p>
</div>
</div>
</div>
<div class="footer">📅 数据更新时间：{update_time} · 多多每周自动更新 · 数据来源：{DATA_SOURCE}<div class="warn">⚠ 投资有风险，决策需谨慎。本网站所有内容仅供学习参考，不构成投资建议。</div></div>
<script>
function switchTab(id) {{
  document.querySelectorAll('.tab').forEach(function(t) {{ t.classList.remove('active'); }});
  document.querySelectorAll('.tab-content').forEach(function(c) {{ c.classList.remove('active'); }});
  var targetTab = document.querySelector('.tab[data-tab="' + id + '"]');
  if (targetTab) targetTab.classList.add('active');
  var panel = document.getElementById('tab-' + id);
  if (panel) panel.classList.add('active');
}}
</script>
</body>
</html>
"""
    return html


def main():
    print("🟡 开始生成黄金ETF投资助手周报...")
    data = fetch_data()
    html = generate_html(data)
    
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_FILE.write_text(html, encoding="utf-8")
    print(f"✅ 已生成: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
