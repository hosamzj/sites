#!/usr/bin/env python3
"""
黄金ETF投资助手周报生成脚本
- 每周一早上自动抓取金价/ETF数据
- 生成 Sites/gold-etf/index.html
- 数据源：Yahoo Finance (yfinance)
"""

import json
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

try:
    import yfinance as yf
except ImportError:
    print("请先安装 yfinance: pip install yfinance")
    sys.exit(1)

# 配置
SITE_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_FILE = SITE_ROOT / "gold-etf" / "index.html"
DATA_SOURCE = "Yahoo Finance"

# ETF 代码映射
SYMBOLS = [
    ("GC=F", "COMEX黄金期货", "国际金价 (USD/盎司)"),
    ("518880.SS", "华安黄金ETF", ""),
    ("518850.SS", "华夏黄金ETF", ""),
    ("518660.SS", "工银黄金ETF", ""),
    ("518800.SS", "国泰黄金ETF", ""),
    ("159934.SZ", "易方达黄金ETF", ""),
    ("159937.SZ", "博时黄金ETF", ""),
    ("518680.SS", "富国上海金ETF", ""),
    ("518600.SS", "广发上海金ETF", ""),
]


def get_week_start_and_end(current_date: datetime) -> tuple:
    """返回当前日期所在周的周一和上周五日期（用于周报对比）"""
    # 默认周一发布，对比上周五
    weekday = current_date.weekday()  # 0=周一
    if weekday == 0:
        prev_friday = current_date - timedelta(days=3)
    else:
        prev_friday = current_date - timedelta(days=weekday + 3)
    return current_date, prev_friday


def fetch_data():
    """抓取行情数据，返回 dict"""
    results = {}
    today = datetime.now().date()
    today_dt = datetime.combine(today, datetime.min.time())
    _, prev_friday = get_week_start_and_end(today_dt)

    for sym, name, _ in SYMBOLS:
        try:
            t = yf.Ticker(sym)
            hist = t.history(period="20d")
            if hist.empty:
                print(f"⚠️ {sym} ({name}) 无数据")
                continue

            latest = hist.index[-1]
            close = float(hist['Close'].iloc[-1])

            # 找上周五收盘价
            prev_week_close = None
            prev_week_date = None
            for i in range(1, min(15, len(hist))):
                d = hist.index[-1 - i]
                if d.date() <= prev_friday.date():
                    prev_week_close = float(hist['Close'].iloc[-1 - i])
                    prev_week_date = d
                    break

            if prev_week_close is None:
                prev_week_close = float(hist['Close'].iloc[-2])
                prev_week_date = hist.index[-2]

            week_change = (close - prev_week_close) / prev_week_close * 100
            high_10d = float(hist['High'].max())
            low_10d = float(hist['Low'].min())

            results[sym] = {
                "name": name,
                "date": str(latest.date()),
                "close": round(close, 4),
                "prev_week_close": round(prev_week_close, 4),
                "prev_week_date": str(prev_week_date.date()),
                "week_change_pct": round(week_change, 2),
                "volume": int(hist['Volume'].iloc[-1])
                if hist['Volume'].iloc[-1] == hist['Volume'].iloc[-1]
                else None,
                "high_10d": round(high_10d, 4),
                "low_10d": round(low_10d, 4),
            }
        except Exception as e:
            print(f"⚠️ {sym} ({name}) 抓取失败: {e}")

    # 国内金价估算（基于华安黄金ETF价格与Au99.99的历史比例）
    huaan = results.get("518880.SS", {})
    if huaan:
        results["domestic_gold_per_gram"] = round(huaan["close"] * 105.7, 2)
        results["domestic_gold_week_change_pct"] = huaan["week_change_pct"]
        results["jewelry_gold_per_gram"] = round(results["domestic_gold_per_gram"] + 380, 0)
        results["international_gold_usd"] = round(results.get("GC=F", {}).get("close", 0), 2)
        results["international_gold_week_change_pct"] = results.get("GC=F", {}).get("week_change_pct", 0)

    return results


def format_number(n):
    return f"{n:,.0f}" if isinstance(n, (int, float)) else str(n)


def generate_html(data):
    today = datetime.now()
    today_str = today.strftime("%Y年%m月%d日")
    weekday = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"][today.weekday()]
    update_time = today.strftime("%Y-%m-%d %H:%M")

    gc_data = data.get("GC=F", {})
    intl_gold = data.get("international_gold_usd", 0)
    intl_change = data.get("international_gold_week_change_pct", 0)
    intl_prev = gc_data.get("prev_week_close", intl_gold)
    intl_color = "green" if intl_change >= 0 else "red"
    intl_arrow = "▲" if intl_change >= 0 else "▼"

    dom_gold = data.get("domestic_gold_per_gram", 0)
    dom_change = data.get("domestic_gold_week_change_pct", 0)
    dom_color = "green" if dom_change >= 0 else "red"
    dom_arrow = "▲" if dom_change >= 0 else "▼"

    jewelry_gold = data.get("jewelry_gold_per_gram", 0)

    huaan = data.get("518880.SS", {})
    huaan_close = huaan.get("close", 0)
    huaan_change = huaan.get("week_change_pct", 0)
    huaan_color = "green" if huaan_change >= 0 else "red"
    huaan_arrow = "▲" if huaan_change >= 0 else "▼"

    # ETF 表格行
    etf_rows = []
    etf_notes = {
        "518880.SS": ("⭐ 规模最大", "gold"),
        "518850.SS": ("💡 费率最低", "green"),
        "518660.SS": ("💡 同为最低费率", "green"),
    }
    etf_fees = {
        "518880.SS": "0.60%",
        "518850.SS": "0.20%",
        "518660.SS": "0.20%",
        "518800.SS": "0.50%",
        "159934.SZ": "0.50%",
        "159937.SZ": "0.50%",
        "518680.SS": "0.40%",
        "518600.SS": "0.40%",
    }
    etf_targets = {
        "518880.SS": "Au99.99",
        "518850.SS": "Au99.99",
        "518660.SS": "Au99.99",
        "518800.SS": "Au99.99",
        "159934.SZ": "Au99.99",
        "159937.SZ": "Au99.99",
        "518680.SS": "上海金SHAU",
        "518600.SS": "上海金SHAU",
    }

    for sym, name, _ in SYMBOLS[1:]:
        item = data.get(sym, {})
        if not item:
            continue
        close = item.get("close", 0)
        change = item.get("week_change_pct", 0)
        color = "green" if change >= 0 else "red"
        note, note_color = etf_notes.get(sym, ("", ""))
        fee = etf_fees.get(sym, "—")
        target = etf_targets.get(sym, "Au99.99")
        fee_class = "fee-low" if fee in ["0.20%", "0.30%"] else "fee-mid"
        row_html = f"""<tr>
<td><span class="etf-name">{name}</span>{f'<br/><span style="font-size:11px;color:var(--{note_color});">{note}</span>' if note else ''}</td>
<td class="etf-code">{sym.split('.')[0]}</td>
<td class="{color}">{close:.3f}</td>
<td class="{color}">{change:+.2f}%</td>
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

/* Header */
.header {{ text-align:center; padding:32px 0 24px; border-bottom:1px solid var(--border); margin-bottom:24px; }}
.header h1 {{ font-size:28px; font-weight:700; background:linear-gradient(135deg,var(--gold-light),var(--gold),var(--gold-dark)); -webkit-background-clip:text; -webkit-text-fill-color:transparent; }}
.header .sub {{ color:var(--text2); font-size:14px; margin-top:6px; }}
.header .date-badge {{ display:inline-block; margin-top:10px; background:rgba(212,168,67,0.12); color:var(--gold); padding:4px 14px; border-radius:20px; font-size:13px; font-weight:500; }}

/* Cards */
.card {{ background:var(--bg2); border:1px solid var(--border); border-radius:12px; padding:20px; margin-bottom:16px; }}
.card-title {{ font-size:16px; font-weight:600; margin-bottom:14px; display:flex; align-items:center; gap:8px; }}
.card-title .icon {{ width:22px; height:22px; border-radius:6px; display:flex; align-items:center; justify-content:center; font-size:13px; }}

/* Price Board */
.price-grid {{ display:grid; grid-template-columns:1fr 1fr; gap:12px; }}
.price-item {{ background:var(--bg3); border-radius:10px; padding:16px; text-align:center; }}
.price-item .label {{ font-size:12px; color:var(--text2); margin-bottom:6px; }}
.price-item .value {{ font-size:24px; font-weight:700; }}
.price-item .change {{ font-size:13px; margin-top:4px; font-weight:500; }}
.up {{ color:var(--green); }}
.down {{ color:var(--red); }}

/* Advice */
.advice-box {{ background:linear-gradient(135deg,rgba(212,168,67,0.08),rgba(212,168,67,0.02)); border:1px solid rgba(212,168,67,0.25); border-radius:12px; padding:20px; margin-bottom:16px; }}
.advice-box .tag {{ display:inline-block; background:var(--gold); color:#000; padding:3px 12px; border-radius:4px; font-size:12px; font-weight:600; margin-bottom:10px; }}
.advice-box h3 {{ font-size:18px; margin-bottom:8px; }}
.advice-box p {{ font-size:14px; color:var(--text2); line-height:1.8; }}

/* Signal */
.signal-bar {{ display:flex; align-items:center; gap:12px; padding:14px 0; border-bottom:1px solid rgba(255,255,255,0.05); }}
.signal-bar:last-child {{ border-bottom:none; }}
.signal-dot {{ width:10px; height:10px; border-radius:50%; flex-shrink:0; }}
.signal-bar .name {{ flex:1; font-size:14px; }}
.signal-bar .val {{ font-size:14px; font-weight:600; }}

/* ETF Table */
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

/* Steps */
.step-list {{ counter-reset:step; }}
.step-item {{ counter-increment:step; padding:12px 0 12px 44px; position:relative; border-bottom:1px solid rgba(255,255,255,0.04); }}
.step-item:last-child {{ border-bottom:none; }}
.step-item::before {{ content:counter(step); position:absolute; left:0; top:12px; width:28px; height:28px; background:var(--gold); color:#000; border-radius:50%; display:flex; align-items:center; justify-content:center; font-weight:700; font-size:13px; }}
.step-item .step-title {{ font-weight:600; font-size:14px; margin-bottom:4px; }}
.step-item .step-desc {{ font-size:13px; color:var(--text2); }}

/* FAQ */
.faq-item {{ padding:12px 0; border-bottom:1px solid rgba(255,255,255,0.04); }}
.faq-item:last-child {{ border-bottom:none; }}
.faq-q {{ font-weight:600; font-size:14px; color:var(--gold-light); margin-bottom:4px; }}
.faq-a {{ font-size:13px; color:var(--text2); line-height:1.7; }}

/* Footer */
.footer {{ text-align:center; padding:24px 0; color:var(--text2); font-size:12px; border-top:1px solid var(--border); margin-top:24px; }}
.footer .warn {{ color:var(--red); font-weight:500; margin-top:6px; }}

/* Tabs */
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
<!-- Header -->
<div class="header">
<h1>🏦 黄金ETF投资助手</h1>
<div class="sub">每周行情追踪 × 小白也能看懂的投资建议</div>
<div class="date-badge" id="today-date">📅 {today_str} · {weekday}</div>
</div>
<!-- Tabs -->
<div class="tabs">
<div class="tab active" onclick="switchTab('overview')">📊 本周速览</div>
<div class="tab" onclick="switchTab('etf')">🏆 ETF对比</div>
<div class="tab" onclick="switchTab('guide')">📖 小白指南</div>
</div>
<!-- Tab 1: Overview -->
<div class="tab-content active" id="tab-overview">
<!-- Price Board -->
<div class="card">
<div class="card-title"><span class="icon" style="background:rgba(212,168,67,0.2);">💰</span> 本周金价</div>
<div class="price-grid">
<div class="price-item">
<div class="label">国际金价 (USD/盎司)</div>
<div class="value" style="color:var(--{intl_color});">${intl_gold:,.0f}</div>
<div class="change {'up' if intl_change >= 0 else 'down'}">{intl_arrow} {intl_change:+.2f}% 较上周五${intl_prev:,.0f}变化至${intl_gold:,.0f}；杰克逊霍尔年会后美元反弹，金价承压；支撑位$4,400，阻力位$4,600。</div>
</div>
<div class="price-item">
<div class="label">国内金价 (CNY/克)</div>
<div class="value" style="color:var(--{dom_color});">{dom_gold:,.0f}</div>
<div class="change {'up' if dom_change >= 0 else 'down'}">{dom_arrow} {dom_change:+.2f}% 据华安ETF估算的AU9999参考价约{dom_gold:,.0f}元/克；汇率因素放大跌幅，国内ETF跌幅大于国际金价。</div>
</div>
<div class="price-item">
<div class="label">品牌首饰金 (元/克)</div>
<div class="value" style="color:var(--gold-light);">~{jewelry_gold:,.0f}</div>
<div class="change up">▲ 首饰金含品牌溢价+工艺费约{jewelry_gold - dom_gold:.0f}元/克；投资选ETF，结婚/送礼才买金饰。</div>
</div>
<div class="price-item">
<div class="label">华安ETF市价 518880</div>
<div class="value" style="color:var(--{huaan_color});">{huaan_close:.3f}</div>
<div class="change {'up' if huaan_change >= 0 else 'down'}">{huaan_arrow} {huaan_change:+.2f}% 本周{huaan_arrow}{abs(huaan_change):.2f}%；高位回调中，切勿追高，可等企稳后分批建仓。</div>
</div>
</div>
</div>
<!-- Advice -->
<div class="advice-box">
<div class="tag">🎯 本周观点</div>
<h3>金价冲高回落，短期观望为主</h3>
<p>
<b>市场回顾：</b>上周金价在$4,700附近遇阻后回落，本周COMEX黄金跌至$4,446，回调幅度约0.7%；国内黄金ETF普遍回调3.7%左右，汇率贬值放大了国内跌幅。<br/><br/>
<b>核心逻辑：</b>①美联储降息预期反复，美元反弹压制金价；②全球央行购金和中国增持趋势未变，中长期支撑仍在；③$4,400是关键支撑，若跌破可能进一步回调至$4,300。<br/><br/>
<b>操作建议：</b>已有仓位可持有观望；空仓者不要追高，等待$4,400附近企稳或回踩$4,300时分批建仓；仓位控制在10%以内。
</p>
</div>
<!-- Highlight -->
<div class="card">
<div class="card-title"><span class="icon" style="background:rgba(212,168,67,0.2);">⭐</span> 华安黄金ETF 518880 本周要点</div>
<div class="signal-bar">
<div class="name">本周市价</div>
<div class="val" style="color:var(--{huaan_color});"><b>{huaan_close:.3f}元（{huaan_change:+.2f}%）</b>，8月高点9.62元，回调约5.2%</div>
</div>
<div class="signal-bar">
<div class="name">10日区间</div>
<div class="val" style="color:var(--text2);">高点 {huaan.get('high_10d', 0):.3f} / 低点 {huaan.get('low_10d', 0):.3f}</div>
</div>
<div class="signal-bar">
<div class="name">⚠ 风险提示</div>
<div class="val" style="color:var(--red);"><b>短期仍处于回调通道</b>，$4,700阻力有效，切勿追涨！跌破$4,400需减仓止损。</div>
</div>
</div>
</div>
<!-- Tab 2: ETF -->
<div class="tab-content" id="tab-etf">
<div class="card">
<div class="card-title"><span class="icon" style="background:rgba(212,168,67,0.2);">🏆</span> 黄金ETF对比（{today_str}数据）</div>
<div style="overflow-x:auto;">
<table class="etf-table">
<thead>
<tr>
<th>基金名称</th>
<th>代码</th>
<th>最新价</th>
<th>本周涨跌</th>
<th>年费率</th>
<th>跟踪标的</th>
</tr>
</thead>
<tbody>
{etf_table_body}
</tbody>
</table>
<p style="font-size:12px;color:var(--text2);margin-top:10px;">📌 注：价格为二级市场交易收盘价，非基金净值；数据来自{DATA_SOURCE}，仅供参考。</p>
</div>
</div>
<div class="advice-box">
<div class="tag">🎯 怎么选？</div>
<h3>三步搞定黄金ETF选择</h3>
<p>
<b>第一步：看费率</b> → 长期持有选0.20%（华夏518850 / 工银518660），省下的就是赚到的<br/>
<b>第二步：看流动性</b> → 华安518880日均成交超4亿份，买卖价差最小，进出最方便<br/>
<b>第三步：看跟踪标的</b> → Au99.99跟国际金价更紧；上海金SHAU人民币计价，避汇率波动<br/><br/>
<b>💡 多多推荐：</b><br/>
        · 长期定投 → <b>华夏518850</b>（费率0.2%最低，长期持有成本优势大）<br/>
        · 短线波段 → <b>华安518880</b>（流动性最好，T+0进出快）<br/>
        · 不想操心汇率 → <b>富国518680</b>（上海金定价，纯人民币）
      </p>
</div>
</div>
<!-- Tab 3: Guide -->
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
<div class="faq-a">A：{today_str}国际金价约${intl_gold:,.0f}/盎司，国内ETF普遍回调{abs(dom_change):.1f}%。短期处于回调通道，<b style="color:var(--red);">不建议追高</b>。可等$4,400附近企稳后再分批建仓，仓位控制在10%以内。</div>
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
  var tabs = document.querySelectorAll('.tab');
  for (var i = 0; i < tabs.length; i++) tabs[i].classList.remove('active');
  var contents = document.querySelectorAll('.tab-content');
  for (var i = 0; i < contents.length; i++) contents[i].classList.remove('active');
  var target = document.querySelector('.tab[onclick*="switchTab(\'' + id + '\')"]');
  if (target) target.classList.add('active');
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
