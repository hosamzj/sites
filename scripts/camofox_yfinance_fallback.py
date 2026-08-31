#!/usr/bin/env python3
"""
Camofox yfinance fallback
==========================
当 yfinance 对美股/指数返回 NaN 或被 Yahoo Finance 反爬拦截时，
自动 fallback 到本地 Camofox 浏览器抓取 Yahoo Finance 网页版延迟报价。

典型用法：
    from camofox_yfinance_fallback import get_market_data
    data = get_market_data(['^GSPC', '^NDX', 'TEL', 'APH'])

返回结构：
    {
      '^GSPC': {
        'price': 7711.76,           # 最新收盘价
        'week_change': 0.49,        # 近一周涨跌幅 %
        'six_month_change': 12.11,  # 近六个月涨跌幅 %
        'source': 'camofox'         # 'yfinance' 或 'camofox'
      },
      ...
    }

依赖：requests（Python 标准库除外）
"""

import json
import re
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from urllib.parse import quote

import requests

CAMOFOX_BASE = "http://127.0.0.1:9377"
CAMOFOX_USER = "hermes_stock_fallback"


# ---------------------------------------------------------------------------
# yfinance 尝试
# ---------------------------------------------------------------------------
def _try_yfinance(tickers: List[str]) -> Dict[str, Optional[dict]]:
    """尝试用 yfinance 获取数据；对失败或 NaN 的标的返回 None。"""
    try:
        import yfinance as yf
    except ImportError:
        return {t: None for t in tickers}

    result = {}
    end = datetime.now()
    start = end - timedelta(days=200)  # 保证覆盖 6 个月
    for t in tickers:
        try:
            obj = yf.Ticker(t)
            hist = obj.history(start=start.strftime('%Y-%m-%d'), end=end.strftime('%Y-%m-%d'))
            if hist is None or hist.empty:
                result[t] = None
                continue

            latest_close = hist['Close'].iloc[-1]
            latest_date = hist.index[-1]

            if latest_close != latest_close:  # NaN check
                result[t] = None
                continue

            # 找一周前的交易日
            one_week_ago = latest_date - timedelta(days=7)
            week_row = hist[hist.index <= one_week_ago]
            week_close = week_row['Close'].iloc[-1] if not week_row.empty else None

            # 找约六个月前的交易日
            six_month_ago = latest_date - timedelta(days=180)
            sixm_row = hist[hist.index <= six_month_ago]
            sixm_close = sixm_row['Close'].iloc[-1] if not sixm_row.empty else None

            def pct(now, before):
                return round((now / before - 1) * 100, 2) if before else None

            result[t] = {
                'price': round(latest_close, 2),
                'week_change': pct(latest_close, week_close),
                'six_month_change': pct(latest_close, sixm_close),
                'source': 'yfinance',
                'latest_date': latest_date.strftime('%Y-%m-%d')
            }
        except Exception as e:
            result[t] = None
    return result


# ---------------------------------------------------------------------------
# Camofox 浏览器抓取
# ---------------------------------------------------------------------------
def _camofox_create_tab(url: str) -> str:
    r = requests.post(
        f"{CAMOFOX_BASE}/tabs",
        json={"userId": CAMOFOX_USER, "sessionKey": "stockdata", "url": url},
        timeout=30
    )
    r.raise_for_status()
    return r.json()["tabId"]


def _camofox_get_snapshot(tab_id: str) -> str:
    r = requests.get(
        f"{CAMOFOX_BASE}/tabs/{tab_id}/snapshot",
        params={"userId": CAMOFOX_USER},
        timeout=30
    )
    r.raise_for_status()
    return r.json()["snapshot"]


def _camofox_close_tab(tab_id: str) -> None:
    try:
        requests.delete(f"{CAMOFOX_BASE}/tabs/{tab_id}", params={"userId": CAMOFOX_USER}, timeout=10)
    except Exception:
        pass


def _parse_quote_price(snapshot: str, symbol: str) -> tuple[Optional[float], Optional[str]]:
    """从 Yahoo Finance 报价页 snapshot 提取最新收盘价和最新交易日。
    返回 (price, latest_date_str)，日期格式为 '%b %d, %Y'，如 'Aug 28, 2026'。
    """
    heading_idx = None
    lines = snapshot.splitlines()
    for i, line in enumerate(lines):
        if 'heading' in line and f'({symbol})' in line:
            heading_idx = i
            break
    if heading_idx is None:
        return None, None

    # 在 heading 后面的有限行内找 text: "价格 ... At close: Month DD ..."
    price = None
    date_str = None
    for line in lines[heading_idx:heading_idx + 10]:
        # 先尝试匹配完整文本里的价格和日期
        m = re.search(
            r'text:\s*"([\d,]+\.?\d*)\s+[^"]*At close:\s*([A-Za-z]+\s+\d{1,2})',
            line
        )
        if m:
            price = float(m.group(1).replace(',', ''))
            # 补上年份（当前年，可能在跨年时需调整，但对报告场景够用）
            month_day = m.group(2)
            year = datetime.now().year
            date_str = f"{month_day}, {year}"
            break
        # 备选：只匹配价格
        m2 = re.search(r'text:\s*"([\d,]+\.?\d*)', line)
        if m2 and price is None:
            price = float(m2.group(1).replace(',', ''))
    return price, date_str


def _parse_history_table(snapshot: str) -> Dict[str, float]:
    """从 Yahoo Finance 历史页 snapshot 提取日期→收盘价映射。"""
    rows = re.findall(r'- row "([^"]+)":', snapshot)
    data = {}
    month_re = re.compile(
        r'^(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{1,2},\s+\d{4}$'
    )
    for row in rows:
        parts = row.split()
        if len(parts) < 7:
            continue
        date_str = ' '.join(parts[:3])
        if not month_re.match(date_str):
            continue
        try:
            close = float(parts[6].replace(',', ''))
            data[date_str] = close
        except ValueError:
            continue
    return data


def _camofox_get_quote(symbol: str) -> tuple[Optional[float], Optional[str]]:
    url = f"https://finance.yahoo.com/quote/{quote(symbol, safe='')}/"
    tab = _camofox_create_tab(url)
    try:
        time.sleep(3)
        snap = _camofox_get_snapshot(tab)
        return _parse_quote_price(snap, symbol)
    finally:
        _camofox_close_tab(tab)


_MONTH_MAP = {
    'Jan': 1, 'January': 1,
    'Feb': 2, 'February': 2,
    'Mar': 3, 'March': 3,
    'Apr': 4, 'April': 4,
    'May': 5,
    'Jun': 6, 'June': 6,
    'Jul': 7, 'July': 7,
    'Aug': 8, 'August': 8,
    'Sep': 9, 'September': 9,
    'Oct': 10, 'October': 10,
    'Nov': 11, 'November': 11,
    'Dec': 12, 'December': 12
}


def _parse_yahoo_date(date_str: str) -> Optional[datetime]:
    """解析 Yahoo Finance 日期格式 'Aug 28, 2026'，不依赖 locale。"""
    parts = date_str.replace(',', '').split()
    if len(parts) != 3:
        return None
    month = _MONTH_MAP.get(parts[0])
    if month is None:
        return None
    try:
        day = int(parts[1])
        year = int(parts[2])
        return datetime(year, month, day)
    except ValueError:
        return None


def _camofox_get_history(symbol: str) -> Dict[str, float]:
    url = f"https://finance.yahoo.com/quote/{quote(symbol, safe='')}/history/"
    tab = _camofox_create_tab(url)
    try:
        time.sleep(3)
        snap = _camofox_get_snapshot(tab)
        return _parse_history_table(snap)
    finally:
        _camofox_close_tab(tab)


def _camofox_fetch(tickers: List[str]) -> Dict[str, Optional[dict]]:
    """用 Camofox 抓取报价页 + 历史页，计算价格、周变动、六个月变动。"""
    result = {}
    for sym in tickers:
        try:
            price, latest_date_str = _camofox_get_quote(sym)
            hist = _camofox_get_history(sym)
            if price is None or not hist or not latest_date_str:
                result[sym] = None
                continue

            latest_date = _parse_yahoo_date(latest_date_str)
            if latest_date is None:
                result[sym] = None
                continue

            # 用最新交易日作为基准，找 1 周前、6 个月前参考价
            def find_ref(target: datetime) -> Optional[float]:
                candidates = []
                for d_str, close in hist.items():
                    d = _parse_yahoo_date(d_str)
                    if d is None:
                        continue
                    if d <= target:
                        candidates.append((d, close))
                if not candidates:
                    return None
                candidates.sort(key=lambda x: x[0], reverse=True)
                return candidates[0][1]

            week_target = latest_date - timedelta(days=7)
            sixm_target = latest_date - timedelta(days=180)
            week_close = find_ref(week_target)
            sixm_close = find_ref(sixm_target)

            def pct(now, before):
                return round((now / before - 1) * 100, 2) if before else None

            result[sym] = {
                'price': round(price, 2),
                'week_change': pct(price, week_close),
                'six_month_change': pct(price, sixm_close),
                'source': 'camofox',
                'latest_date': latest_date.strftime('%Y-%m-%d')
            }
        except Exception:
            result[sym] = None
    return result


# ---------------------------------------------------------------------------
# 对外接口
# ---------------------------------------------------------------------------
def camofox_health() -> bool:
    """检查 Camofox 服务是否可用。"""
    try:
        r = requests.get(f"{CAMOFOX_BASE}/health", timeout=5)
        return r.status_code == 200 and r.json().get('browserConnected', False)
    except Exception:
        return False


def get_market_data(
    tickers: List[str],
    use_camofox: bool = True,
    camofox_required_for: Optional[List[str]] = None
) -> Dict[str, Optional[dict]]:
    """
    优先使用 yfinance；对失败/NaN 的标的自动 fallback 到 Camofox。

    参数：
        tickers: 标的列表，如 ['^GSPC', '^NDX', 'TEL', 'APH']
        use_camofox: 是否启用 Camofox fallback（默认 True）
        camofox_required_for: 强制使用 Camofox 的标的（即使 yfinance 成功也用它）
    """
    camofox_required_for = camofox_required_for or []

    # 第一步：yfinance
    yf_result = _try_yfinance(tickers)

    # 第二步：决定哪些需要 fallback
    need_camofox = []
    for t in tickers:
        if t in camofox_required_for:
            need_camofox.append(t)
        elif yf_result.get(t) is None:
            need_camofox.append(t)

    if not need_camofox or not use_camofox:
        return yf_result

    if not camofox_health():
        # Camofox 没启动，返回 yfinance 结果（含 None）
        return yf_result

    cf_result = _camofox_fetch(need_camofox)

    # 合并结果
    final = dict(yf_result)
    for t in need_camofox:
        if cf_result.get(t):
            final[t] = cf_result[t]
    return final


# ---------------------------------------------------------------------------
# 命令行测试
# ---------------------------------------------------------------------------
if __name__ == '__main__':
    import sys
    test_tickers = sys.argv[1:] or ['^GSPC', '^NDX', 'TEL', 'APH']
    print(f'测试标的: {test_tickers}')
    print(f'Camofox 健康: {camofox_health()}')
    data = get_market_data(test_tickers)
    print(json.dumps(data, indent=2, ensure_ascii=False))
