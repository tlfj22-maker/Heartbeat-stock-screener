from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, time
from typing import Optional
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd
import streamlit as st
import yfinance as yf

st.set_page_config(
    page_title="Troy's Heartbeat Screener",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown(
    """
    <style>
      .block-container {padding-top: 1rem; padding-bottom: 3rem; max-width: 1500px;}
      [data-testid="stMetricValue"] {font-size: 1.55rem;}
      .hero {
        padding: 1.1rem 1.2rem;
        border-radius: 18px;
        background: linear-gradient(135deg, rgba(40,90,255,.16), rgba(140,60,255,.10));
        border: 1px solid rgba(130,130,130,.22);
        margin-bottom: .9rem;
      }
      .hero h1 {margin: 0 0 .25rem 0; font-size: 2rem;}
      .hero p {margin: 0; opacity: .82;}
      .note {
        border-left: 4px solid #888;
        padding: .65rem .85rem;
        background: rgba(130,130,130,.08);
        border-radius: 8px;
      }
      @media (max-width: 700px) {
        .hero h1 {font-size: 1.55rem;}
        .block-container {padding-left: .7rem; padding-right: .7rem;}
      }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="hero">
      <h1>📈 Troy's Heartbeat Stock Screener V4.1</h1>
      <p>Opportunity intelligence, institutional accumulation, AI leadership, Smart Money Radar, and an under-$20 Hidden Gem Scanner with scheduled catalyst tracking.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

# -----------------------------------------------------------------------------
# Expanded AI ecosystem universe and category map
# -----------------------------------------------------------------------------
AI_GROUPS = {
    "AI Chips": [
        "NVDA","AMD","AVGO","TSM","ARM","QCOM","INTC","ADI","MCHP","ON","MPWR",
        "NXPI","MRVL","CRDO","ALAB","SMTC","LSCC","WOLF","GFS","UMC","ASX","SWKS","QRVO",
    ],
    "Memory & Storage": [
        "MU","WDC","STX","PSTG","NTAP","SNDK","RMBS","SIMO",
    ],
    "Semiconductor Equipment": [
        "ASML","AMAT","LRCX","KLAC","TER","ONTO","ACLS","AEHR","COHU","FORM","CAMT","VECO","MKSI",
    ],
    "Networking": [
        "ANET","CSCO","HPE","JNPR","CIEN","NOK","ERIC","EXTR","COMM","CALX","INFN",
    ],
    "Optical & Connectivity": [
        "COHR","LITE","APH","TEL","GLW","FN","AAOI","FLEX","SANM","JBL","CLS",
    ],
    "Power & Electrical": [
        "ETN","GEV","VRT","PWR","HUBB","NVT","POWL","EMR","ROK","AME","GNRC","ENS","ATKR",
    ],
    "Cooling & Thermal": [
        "VRT","MOD","TT","CARR","JCI","LII","AAON","FIX","WTS","BMI",
    ],
    "Construction & Infrastructure": [
        "FIX","PWR","EME","STRL","ACM","MTZ","GVA","PRIM","IESC","URI","CAT","DE","TEX","OSK",
    ],
    "Data Centers & Hardware": [
        "SMCI","DELL","HPE","HPQ","IBM","WDC","STX","PSTG","NTAP","JBL","FLEX","SANM","CLS",
    ],
    "Cloud Platforms": [
        "MSFT","AMZN","GOOGL","META","ORCL","IBM","SNOW","DDOG","MDB","NET","AKAM","GDDY",
    ],
    "AI Software": [
        "PLTR","AI","CRM","NOW","PATH","SOUN","BBAI","C3AI","UPST","TEM","RXRX","VERI","INOD",
    ],
    "Cybersecurity": [
        "PANW","CRWD","FTNT","ZS","OKTA","CYBR","S","TENB","RBRK","QLYS","VRNS","GEN",
    ],
    "Robotics & Automation": [
        "ISRG","ROK","TER","SYM","CGNX","IRBT","SERV","RR","OUST","MBLY","AEVA","LAZR",
    ],
    "Utilities & Generation": [
        "CEG","VST","NRG","NEE","DUK","SO","AEP","EXC","SRE","ETR","PCG","AES","TLN","OKLO","SMR","NNE",
    ],
    "Quantum & Emerging Compute": [
        "IONQ","RGTI","QBTS","QUBT","ARQQ","LAES",
    ],
}

AI_TICKERS = sorted({ticker for members in AI_GROUPS.values() for ticker in members})
AI_SEMI_PULLBACK_TICKERS = sorted(set(
    AI_GROUPS["AI Chips"]
    + AI_GROUPS["Memory & Storage"]
    + AI_GROUPS["Semiconductor Equipment"]
))
TICKER_TO_GROUPS: dict[str, list[str]] = {}
for group, members in AI_GROUPS.items():
    for ticker in members:
        TICKER_TO_GROUPS.setdefault(ticker, []).append(group)


# -----------------------------------------------------------------------------
# Hidden-gem universe: liquid small/mid-cap names in sectors with frequent
# earnings, contract, clinical, commodity, infrastructure, or AI catalysts.
# Price and market-cap rules are applied dynamically, so being listed here is
# only an invitation to scan — never an endorsement.
# -----------------------------------------------------------------------------
HIDDEN_GEM_GROUPS = {
    "Energy & Natural Gas": [
        "EQT","AR","RRC","CTRA","TELL","NEXT","NFE","CLNE","REI","KOS","VTLE","AMPY","SD","NGS","RES","OIS","HLX","BORR","VAL","DHT","NAT","TNP","GASS",
    ],
    "Oilfield, Chemicals & Materials": [
        "TROX","CC","HUN","OLN","KRO","KOP","NGVT","IOSP","CBT","KALU","CENX","TMC","LAC","LTHM","UUUU","URG","UEC","DNN","LEU",
    ],
    "AI, Cooling & Data Infrastructure": [
        "AAON","MOD","VRT","CLS","JBL","SANM","FLEX","AEHR","COHU","FORM","VECO","AIP","INOD","BBAI","SOUN","AI","VERI","REKR","OUST","AEVA","LAZR","LIDR","ARBE","KULR","NVTS","INDI","SMFL",
    ],
    "Industrials, Defense & Infrastructure": [
        "AIRJ","STRL","PRIM","IESC","GVA","MTZ","TWI","TGI","ATRO","AVAV","KTOS","RCAT","ONDS","UMAC","RDW","ASTS","RKLB","BWXT","LESL","HYLN","EOSE","STEM","FLNC","NVRI","MNTK",
    ],
    "Healthcare & Biotechnology": [
        "BIIB","RXRX","TEM","CRSP","NTLA","EDIT","BEAM","VERV","SANA","ARCT","KYMR","RVMD","IMVT","VKTX","TGTX","CYTK","IOVA","FATE","SLS","ALT","AKRO","MDGL","GERN","DYN","PRME","NAMS","MRUS","JANX","CGEM","ERAS","ELEV","DAWN","IRON","KURA","ZYME","ABCL","SDGR",
    ],
    "Power, Nuclear & Grid": [
        "SMR","OKLO","NNE","UUUU","LEU","UEC","DNN","URG","LTBR","EOSE","FLNC","STEM","AMTX","GEVO","CLSK","IREN","CIFR","CORZ","WULF","BTDR",
    ],
}
HIDDEN_GEM_TICKERS = sorted({t for members in HIDDEN_GEM_GROUPS.values() for t in members})
HIDDEN_TICKER_TO_GROUPS: dict[str, list[str]] = {}
for group, members in HIDDEN_GEM_GROUPS.items():
    for ticker in members:
        HIDDEN_TICKER_TO_GROUPS.setdefault(ticker, []).append(group)

FINANCE_TICKERS = [
    "JPM","BAC","WFC","C","GS","MS","SCHW","BLK","AXP","V","MA","SPGI","CME","ICE","CB"
]
ENERGY_TICKERS = [
    "XOM","CVX","COP","EOG","OXY","EQT","AR","RRC","CTRA","FANG","DVN","APA","SLB","MPC","VLO","KMI","WMB","OKE","PSX","HAL"
]
INDUSTRIAL_TICKERS = [
    "CAT","DE","HON","GE","RTX","LMT","NOC","LHX","EMR","ROK","PH","URI","FAST","GWW","ETN","PWR","FIX","STRL"
]
HEALTHCARE_TICKERS = [
    "LLY","UNH","JNJ","ABBV","MRK","AMGN","TMO","DHR","ISRG","BSX","SYK","VRTX","BIIB","REGN","GILD"
]
CONSUMER_TICKERS = [
    "AMZN","WMT","COST","HD","LOW","MCD","SBUX","NKE","BKNG","TJX","PG","KO","PEP"
]

UNIVERSES = {
    "V4.1 intelligence + hidden gems": sorted(set(AI_TICKERS + HIDDEN_GEM_TICKERS)),
    "Hidden gems — under $20 candidates": HIDDEN_GEM_TICKERS,
    "AI ecosystem — expanded": AI_TICKERS,
    "Financials": FINANCE_TICKERS,
    "Energy & oil": ENERGY_TICKERS,
    "Industrials & defense": INDUSTRIAL_TICKERS,
    "Healthcare": HEALTHCARE_TICKERS,
    "Consumer": CONSUMER_TICKERS,
    "All built-in sectors": sorted(set(
        AI_TICKERS + FINANCE_TICKERS + ENERGY_TICKERS +
        INDUSTRIAL_TICKERS + HEALTHCARE_TICKERS + CONSUMER_TICKERS + HIDDEN_GEM_TICKERS
    )),
}


@dataclass(frozen=True)
class Params:
    ma_days: int = 150
    avg_volume_days: int = 50
    min_volume_ratio: float = 1.5
    base_days: int = 40
    max_base_range: float = 0.22
    breakout_days: int = 40
    max_extension: float = 0.25
    min_price: float = 5.0
    min_avg_dollar_volume: float = 25_000_000


def market_elapsed_fraction() -> tuple[float, str]:
    now = datetime.now(ZoneInfo("America/New_York"))
    if now.weekday() >= 5:
        return 1.0, "Market closed — using full-day volume"
    open_dt = datetime.combine(now.date(), time(9, 30), tzinfo=now.tzinfo)
    close_dt = datetime.combine(now.date(), time(16, 0), tzinfo=now.tzinfo)
    if now <= open_dt:
        return 1.0, "Pre-market — using prior/full-day volume"
    if now >= close_dt:
        return 1.0, "Market closed — using full-day volume"
    elapsed = (now - open_dt).total_seconds()
    session = (close_dt - open_dt).total_seconds()
    fraction = min(max(elapsed / session, 0.08), 1.0)
    return fraction, f"Market session {fraction:.0%} complete"


def clean_ticker(t: str) -> str:
    return t.strip().upper().replace(".", "-")


@st.cache_data(ttl=1800, show_spinner=False)
def download_prices(tickers: tuple[str, ...], period: str = "2y") -> pd.DataFrame:
    return yf.download(
        list(tickers),
        period=period,
        interval="1d",
        auto_adjust=True,
        group_by="ticker",
        threads=True,
        progress=False,
    )


def frame_for(raw: pd.DataFrame, ticker: str, total: int) -> pd.DataFrame:
    try:
        df = raw.copy() if total == 1 else raw[ticker].copy()
        return df.dropna(subset=["Close", "Volume"])
    except Exception:
        return pd.DataFrame()


def safe_last(series: pd.Series, default: float = np.nan) -> float:
    try:
        value = float(series.iloc[-1])
        return value if np.isfinite(value) else default
    except Exception:
        return default


def calculate_rsi(close: pd.Series, period: int = 14) -> float:
    delta = close.diff()
    gains = delta.clip(lower=0).rolling(period).mean()
    losses = (-delta.clip(upper=0)).rolling(period).mean()
    rs = gains / losses.replace(0, np.nan)
    rsi = 100 - (100 / (1 + rs))
    return safe_last(rsi, 50.0)


def calculate_cmf(high: pd.Series, low: pd.Series, close: pd.Series, volume: pd.Series, period: int = 20) -> float:
    spread = (high - low).replace(0, np.nan)
    multiplier = ((close - low) - (high - close)) / spread
    money_flow_volume = multiplier.fillna(0) * volume
    cmf = money_flow_volume.rolling(period).sum() / volume.rolling(period).sum().replace(0, np.nan)
    return safe_last(cmf, 0.0)


def relative_return(stock: pd.Series, benchmark: pd.Series, days: int = 63) -> float:
    common = stock.index.intersection(benchmark.index)
    if len(common) <= days:
        return np.nan
    s = stock.loc[common]
    b = benchmark.loc[common]
    return float((s.iloc[-1] / s.iloc[-1-days] - 1) - (b.iloc[-1] / b.iloc[-1-days] - 1)) * 100


def score_institutional(
    price: float,
    ma50: float,
    ma150: float,
    ma200: float,
    ma50_slope: float,
    ma150_slope: float,
    ma200_slope: float,
    cmf: float,
    obv_change: float,
    ad_change: float,
    up_down_volume_ratio: float,
    volume_trend: float,
    rs_spy: float,
    rs_nvda: float,
) -> float:
    score = 0.0

    # Trend alignment: 25 points
    score += 10 if price > ma50 > ma150 > ma200 else 7 if price > ma150 > ma200 else 3 if price > ma200 else 0
    score += 5 if ma50_slope > 0 else 0
    score += 5 if ma150_slope > 0 else 0
    score += 5 if ma200_slope > 0 else 0

    # Money flow and accumulation: 40 points
    score += 12 if cmf >= 0.15 else 9 if cmf >= 0.05 else 5 if cmf > 0 else 0
    score += 10 if obv_change >= 0.10 else 7 if obv_change >= 0.03 else 3 if obv_change > 0 else 0
    score += 8 if ad_change >= 0.08 else 5 if ad_change >= 0.02 else 2 if ad_change > 0 else 0
    score += 6 if up_down_volume_ratio >= 1.35 else 4 if up_down_volume_ratio >= 1.10 else 2 if up_down_volume_ratio >= 1.0 else 0
    score += 4 if volume_trend >= 0.15 else 2 if volume_trend > 0 else 0

    # Relative strength: 35 points
    score += 20 if pd.notna(rs_spy) and rs_spy >= 15 else 15 if pd.notna(rs_spy) and rs_spy >= 5 else 8 if pd.notna(rs_spy) and rs_spy > 0 else 0
    score += 15 if pd.notna(rs_nvda) and rs_nvda >= 10 else 10 if pd.notna(rs_nvda) and rs_nvda >= 0 else 4 if pd.notna(rs_nvda) and rs_nvda >= -10 else 0

    return round(min(score, 100), 1)


def score_opportunity(
    breakout_pct: float,
    intraday_volume_pace: float,
    price: float,
    ma50: float,
    ma150: float,
    ma200: float,
    distance_200: float,
    rsi: float,
    base_range: float,
    max_base_range: float,
    atr_compression: float,
    sector_strength: float,
    institutional_score: float,
) -> float:
    score = 0.0

    # Breakout proximity: 25 points
    if breakout_pct >= 0:
        score += 25
    elif breakout_pct >= -0.01:
        score += 23
    elif breakout_pct >= -0.03:
        score += 20
    elif breakout_pct >= -0.07:
        score += 14
    elif breakout_pct >= -0.12:
        score += 8
    else:
        score += 2

    # Volume participation: 15 points
    score += 15 if intraday_volume_pace >= 2.0 else 12 if intraday_volume_pace >= 1.5 else 9 if intraday_volume_pace >= 1.2 else 5 if intraday_volume_pace >= 1.0 else 1

    # Trend quality: 15 points
    score += 15 if price > ma50 > ma150 > ma200 else 12 if price > ma150 > ma200 else 8 if price > ma200 else 3

    # Pullback / 200-day positioning: 10 points
    if -0.03 <= distance_200 <= 0.06:
        score += 10
    elif 0.06 < distance_200 <= 0.18:
        score += 7
    elif -0.08 <= distance_200 < -0.03:
        score += 4
    elif distance_200 > 0.18:
        score += 3

    # RSI health: 10 points
    score += 10 if 48 <= rsi <= 68 else 8 if 40 <= rsi < 48 else 6 if 68 < rsi <= 75 else 3 if 30 <= rsi < 40 else 1

    # Base quality: 10 points
    score += 10 if base_range <= max_base_range else 7 if base_range <= max_base_range * 1.25 else 3 if base_range <= max_base_range * 1.6 else 0

    # Volatility contraction: 5 points
    score += 5 if atr_compression <= 0.75 else 3 if atr_compression <= 0.95 else 1

    # Sector strength: 5 points
    score += max(0.0, min(sector_strength, 100.0)) * 0.05

    # Institutional activity: 10 points
    score += institutional_score * 0.10

    return round(min(score, 100), 1)


def technical_row(
    ticker: str,
    df: pd.DataFrame,
    spy: pd.DataFrame,
    nvda: pd.DataFrame,
    p: Params,
    session_fraction: float,
) -> Optional[dict]:
    if len(df) < 235:
        return None

    c = df["Close"].astype(float)
    h = df["High"].astype(float)
    l = df["Low"].astype(float)
    v = df["Volume"].astype(float)

    ma50 = c.rolling(50).mean()
    ma150 = c.rolling(150).mean()
    ma200 = c.rolling(200).mean()
    av = v.rolling(p.avg_volume_days).mean()
    adv = (c * v).rolling(p.avg_volume_days).mean()

    price = safe_last(c)
    prior_close = float(c.iloc[-2]) if len(c) >= 2 else np.nan
    day_change_pct = (price / prior_close - 1) * 100 if prior_close and np.isfinite(prior_close) else np.nan
    day_dollar_change = price - prior_close if prior_close and np.isfinite(prior_close) else np.nan
    ma50_now = safe_last(ma50)
    ma150_now = safe_last(ma150)
    ma200_now = safe_last(ma200)
    av_now = safe_last(av)
    dollar_vol = safe_last(adv)

    if any(np.isnan(x) for x in [price, ma50_now, ma150_now, ma200_now, av_now]):
        return None
    if price < p.min_price or dollar_vol < p.min_avg_dollar_volume:
        return None

    slope_days = 30
    ma50_slope = ma50_now / float(ma50.iloc[-1-slope_days]) - 1
    ma150_slope = ma150_now / float(ma150.iloc[-1-slope_days]) - 1
    ma200_slope = ma200_now / float(ma200.iloc[-1-slope_days]) - 1
    distance_150 = price / ma150_now - 1
    distance_200 = price / ma200_now - 1
    pullback_200_watch = bool(-0.03 <= distance_200 <= 0.06 and ma200_slope >= -0.01)

    base = c.iloc[-p.base_days:]
    base_low, base_high = float(base.min()), float(base.max())
    base_range = base_high / base_low - 1 if base_low else np.nan

    prior = c.iloc[-(p.breakout_days + 1):-1]
    prior_high = float(prior.max())
    breakout_pct = price / prior_high - 1 if prior_high else np.nan
    distance_to_breakout = breakout_pct * 100

    volume_ratio = float(v.iloc[-1]) / av_now if av_now else np.nan
    intraday_volume_pace = volume_ratio / (session_fraction ** 0.65) if session_fraction > 0 else volume_ratio
    intraday_volume_pace = min(intraday_volume_pace, 5.0) if pd.notna(intraday_volume_pace) else np.nan

    # Volatility compression: recent ATR compared with its longer baseline.
    true_range = pd.concat([
        h - l,
        (h - c.shift()).abs(),
        (l - c.shift()).abs(),
    ], axis=1).max(axis=1)
    atr14 = true_range.rolling(14).mean()
    atr_ratio = atr14 / c
    atr_compression = safe_last(atr_ratio) / safe_last(atr_ratio.rolling(60).mean(), 1.0)

    rsi = calculate_rsi(c)
    cmf = calculate_cmf(h, l, c, v)

    # OBV and Accumulation/Distribution trends.
    obv = (np.sign(c.diff()).fillna(0) * v).cumsum()
    obv_base = abs(float(obv.iloc[-21])) if len(obv) > 21 else np.nan
    obv_change = (float(obv.iloc[-1]) - float(obv.iloc[-21])) / obv_base if obv_base not in (0, np.nan) else 0.0

    money_flow_multiplier = (((c - l) - (h - c)) / (h - l).replace(0, np.nan)).fillna(0)
    ad_line = (money_flow_multiplier * v).cumsum()
    ad_base = abs(float(ad_line.iloc[-21])) if len(ad_line) > 21 else np.nan
    ad_change = (float(ad_line.iloc[-1]) - float(ad_line.iloc[-21])) / ad_base if ad_base not in (0, np.nan) else 0.0

    returns = c.pct_change()
    up_vol = float(v[returns > 0].tail(20).sum())
    down_vol = float(v[returns < 0].tail(20).sum())
    up_down_volume_ratio = up_vol / down_vol if down_vol > 0 else 2.0
    volume_trend = safe_last(v.rolling(10).mean()) / safe_last(v.rolling(50).mean()) - 1

    rs_spy = relative_return(c, spy["Close"].astype(float), 63) if not spy.empty else np.nan
    rs_nvda = relative_return(c, nvda["Close"].astype(float), 63) if not nvda.empty and ticker != "NVDA" else 0.0

    institutional_score = score_institutional(
        price, ma50_now, ma150_now, ma200_now,
        ma50_slope, ma150_slope, ma200_slope,
        cmf, obv_change, ad_change, up_down_volume_ratio,
        volume_trend, rs_spy, rs_nvda,
    )

    trend_ok = price > ma150_now and ma150_slope >= 0
    base_ok = base_range <= p.max_base_range * 1.35
    heads_up = bool(trend_ok and base_ok and breakout_pct >= -0.03 and intraday_volume_pace >= 1.2)
    trigger = bool(trend_ok and base_ok and breakout_pct >= -0.01 and intraday_volume_pace >= p.min_volume_ratio)
    heartbeat = bool(trigger and breakout_pct >= 0)

    setup = "Tier 1 — Heartbeat" if heartbeat else "Tier 2 — Almost there" if heads_up else "Tier 3 — Watch"
    if heartbeat:
        status = "🚨 Confirmed breakout"
    elif trigger:
        status = "🔥 Trigger zone"
    elif heads_up:
        status = "👀 Heads-up — close and building"
    elif trend_ok and breakout_pct >= -0.03:
        status = "Near breakout — needs volume"
    elif trend_ok:
        status = "Healthy trend — still forming"
    else:
        status = "Not ready"

    proximity_points = 45 if breakout_pct >= 0 else 40 if breakout_pct >= -.01 else 32 if breakout_pct >= -.03 else 20 if breakout_pct >= -.07 else 5
    volume_points = 35 if intraday_volume_pace >= p.min_volume_ratio else 27 if intraday_volume_pace >= 1.2 else 18 if intraday_volume_pace >= 1.0 else 7 if intraday_volume_pace >= .7 else 0
    structure_points = 20 if base_range <= p.max_base_range else 10 if base_range <= p.max_base_range * 1.35 else 0
    readiness_score = min(proximity_points + volume_points + structure_points, 100)

    quality_score = 0
    quality_score += 22 if price > ma150_now else 0
    quality_score += 22 if ma150_slope > .02 else 15 if ma150_slope > 0 else 4
    quality_score += 14 if 0 <= distance_150 <= p.max_extension else 7 if price > ma150_now else 0
    quality_score += 20 if base_range <= p.max_base_range else 11 if base_range <= p.max_base_range * 1.5 else 0
    quality_score += 12 if pd.notna(rs_spy) and rs_spy >= 10 else 7 if pd.notna(rs_spy) and rs_spy > 0 else 0
    quality_score = min(quality_score, 100)

    reasons = []
    if price > ma150_now:
        reasons.append("above 150D MA")
    if ma150_slope > 0:
        reasons.append("rising trend")
    if base_range <= p.max_base_range:
        reasons.append("tight base")
    if breakout_pct >= -.03:
        reasons.append(f"{abs(distance_to_breakout):.1f}% from breakout" if breakout_pct < 0 else "above breakout")
    if intraday_volume_pace >= 1.0:
        reasons.append(f"volume pace {intraday_volume_pace:.2f}x")
    if cmf > 0.05:
        reasons.append("positive money flow")

    return {
        "Ticker": ticker,
        "AI Groups": ", ".join(TICKER_TO_GROUPS.get(ticker, [])),
        "Setup": setup,
        "Quality Score": round(quality_score, 1),
        "Readiness Score": round(readiness_score, 1),
        "Institutional Score": institutional_score,
        "Opportunity Score": np.nan,  # Filled after sector strength is calculated.
        "Price": price,
        "Previous Close": prior_close,
        "Day Change $": day_dollar_change,
        "Day Change %": day_change_pct,
        "AI Semi Pullback": ticker in AI_SEMI_PULLBACK_TICKERS and pd.notna(day_change_pct) and day_change_pct < 0,
        "Breakout Level": prior_high,
        "Distance to Breakout %": distance_to_breakout,
        "Volume Ratio": volume_ratio,
        "Intraday Volume Pace": intraday_volume_pace,
        "Status": status,
        "Why": ", ".join(reasons[:6]) if reasons else "setup still developing",
        "Alert Stage": "TRIGGER" if trigger else "HEADS-UP" if heads_up else "",
        "Alert Ready": bool(trigger),
        "TradingView": f"https://www.tradingview.com/chart/?symbol={ticker}",
        "MA50": ma50_now,
        "MA150": ma150_now,
        "200D MA": ma200_now,
        "50D MA Slope %": ma50_slope * 100,
        "150D MA Slope %": ma150_slope * 100,
        "200D MA Slope %": ma200_slope * 100,
        "Distance From 150D MA %": distance_150 * 100,
        "Distance From 200D MA %": distance_200 * 100,
        "AI 200D Pullback Watch": pullback_200_watch and ticker in AI_TICKERS,
        "Base Range %": base_range * 100,
        "Breakout %": breakout_pct * 100,
        "RS vs SPY 3M %": rs_spy,
        "RS vs NVDA 3M %": rs_nvda,
        "RSI 14": rsi,
        "CMF 20": cmf,
        "OBV Trend 20D %": obv_change * 100,
        "A/D Trend 20D %": ad_change * 100,
        "Up/Down Volume Ratio": up_down_volume_ratio,
        "Volume Trend %": volume_trend * 100,
        "ATR Compression": atr_compression,
        "Avg Dollar Volume": dollar_vol,
    }


def safe_days_to_date(value) -> float:
    """Convert yfinance date-like values to calendar days from today."""
    try:
        ts = pd.Timestamp(value)
        if ts.tzinfo is not None:
            ts = ts.tz_convert("America/New_York").tz_localize(None)
        return float((ts.normalize() - pd.Timestamp.now().normalize()).days)
    except Exception:
        return np.nan


def hidden_gem_score(row: pd.Series) -> float:
    """Rank under-$20 candidates without pretending a catalyst guarantees gains."""
    score = 0.0
    score += min(float(row.get("Opportunity Score", 0)), 100) * 0.25
    score += min(float(row.get("Institutional Score", 0)), 100) * 0.20

    rev = row.get("Revenue Growth %", np.nan)
    score += 15 if pd.notna(rev) and rev >= 25 else 12 if pd.notna(rev) and rev >= 10 else 7 if pd.notna(rev) and rev > 0 else 0

    fcf = row.get("Free Cash Flow", np.nan)
    fcf_margin = row.get("FCF Margin %", np.nan)
    score += 15 if pd.notna(fcf) and fcf > 0 and pd.notna(fcf_margin) and fcf_margin >= 8 else 10 if pd.notna(fcf) and fcf > 0 else 3 if pd.notna(fcf_margin) and fcf_margin > -5 else 0

    upside = row.get("Analyst Target Upside %", np.nan)
    score += 10 if pd.notna(upside) and upside >= 30 else 7 if pd.notna(upside) and upside >= 15 else 3 if pd.notna(upside) and upside > 0 else 0

    days = row.get("Days to Earnings", np.nan)
    score += 10 if pd.notna(days) and 3 <= days <= 30 else 6 if pd.notna(days) and 31 <= days <= 60 else 2 if pd.notna(days) and 0 <= days < 3 else 0

    cap = row.get("Market Cap", np.nan)
    score += 5 if pd.notna(cap) and 100_000_000 <= cap <= 5_000_000_000 else 3 if pd.notna(cap) and cap <= 15_000_000_000 else 0
    return round(min(score, 100), 1)


@st.cache_data(ttl=21600, show_spinner=False)
def fundamentals(ticker: str) -> dict:
    try:
        info = yf.Ticker(ticker).info or {}
        price = info.get("currentPrice") or info.get("regularMarketPrice")
        target = info.get("targetMeanPrice")
        revenue_growth = info.get("revenueGrowth")
        earnings_growth = info.get("earningsGrowth")
        gross_margin = info.get("grossMargins")
        op_margin = info.get("operatingMargins")
        fcf = info.get("freeCashflow")
        revenue = info.get("totalRevenue")
        total_cash = info.get("totalCash")
        total_debt = info.get("totalDebt")
        short_float = info.get("shortPercentOfFloat")
        sector = info.get("sector")
        industry = info.get("industry")
        fcf_margin = fcf / revenue if fcf is not None and revenue not in (None, 0) else None
        target_upside = target / price - 1 if target and price else None

        score = 0
        if revenue_growth is not None:
            score += 7 if revenue_growth >= .20 else 5 if revenue_growth >= .10 else 3 if revenue_growth > 0 else 0
        if earnings_growth is not None:
            score += 6 if earnings_growth >= .20 else 4 if earnings_growth >= .10 else 2 if earnings_growth > 0 else 0
        if gross_margin is not None:
            score += 4 if gross_margin >= .50 else 3 if gross_margin >= .30 else 1
        if fcf_margin is not None:
            score += 5 if fcf_margin >= .15 else 3 if fcf_margin >= .05 else 1 if fcf_margin > 0 else 0
        inst = info.get("heldPercentInstitutions")
        if inst is not None:
            score += 3 if inst >= .70 else 2 if inst >= .50 else 1
        if target_upside is not None:
            score += 3 if target_upside >= .15 else 2 if target_upside > 0 else 0
        pe = info.get("forwardPE")

        next_earnings = pd.NaT
        try:
            cal = yf.Ticker(ticker).calendar
            if isinstance(cal, dict):
                raw_date = cal.get("Earnings Date")
                if isinstance(raw_date, (list, tuple)) and raw_date:
                    next_earnings = pd.Timestamp(raw_date[0])
                elif raw_date is not None:
                    next_earnings = pd.Timestamp(raw_date)
            elif isinstance(cal, pd.DataFrame) and not cal.empty:
                if "Earnings Date" in cal.index:
                    next_earnings = pd.Timestamp(cal.loc["Earnings Date"].iloc[0])
        except Exception:
            pass
        days_to_earnings = safe_days_to_date(next_earnings) if pd.notna(next_earnings) else np.nan

        if pe is not None:
            score += 2 if 0 < pe <= 25 else 1 if 25 < pe <= 40 else 0

        return {
            "Revenue Growth %": revenue_growth * 100 if revenue_growth is not None else np.nan,
            "EPS Growth %": earnings_growth * 100 if earnings_growth is not None else np.nan,
            "Gross Margin %": gross_margin * 100 if gross_margin is not None else np.nan,
            "Operating Margin %": op_margin * 100 if op_margin is not None else np.nan,
            "FCF Margin %": fcf_margin * 100 if fcf_margin is not None else np.nan,
            "Institutional Ownership %": inst * 100 if inst is not None else np.nan,
            "Insider Ownership %": (info.get("heldPercentInsiders") or np.nan) * 100,
            "Forward P/E": pe,
            "Analyst Target Upside %": target_upside * 100 if target_upside is not None else np.nan,
            "Market Cap": info.get("marketCap"),
            "Free Cash Flow": fcf,
            "Total Cash": total_cash,
            "Total Debt": total_debt,
            "Short Float %": short_float * 100 if short_float is not None else np.nan,
            "Sector": sector or "",
            "Industry": industry or "",
            "Next Earnings": next_earnings,
            "Days to Earnings": days_to_earnings,
            "Catalyst": "Scheduled earnings" if pd.notna(days_to_earnings) and 0 <= days_to_earnings <= 60 else "No scheduled event found",
            "Fundamental Score": score,
        }
    except Exception:
        return {"Fundamental Score": 0}


def build_heatmap(results: pd.DataFrame) -> pd.DataFrame:
    rows = []
    ai_results = results[results["Ticker"].isin(AI_TICKERS)].copy()
    for group, tickers in AI_GROUPS.items():
        subset = ai_results[ai_results["Ticker"].isin(tickers)]
        if subset.empty:
            continue
        strength = (
            subset["Institutional Score"].mean() * 0.45
            + subset["Quality Score"].mean() * 0.30
            + subset["Readiness Score"].mean() * 0.15
            + subset["RS vs SPY 3M %"].clip(-20, 30).fillna(0).mean() * 0.35
        )
        strength = float(np.clip(strength, 0, 100))
        state = "🟢 Leading" if strength >= 65 else "🟡 Improving" if strength >= 50 else "🟠 Mixed" if strength >= 35 else "🔴 Weak"
        rows.append({
            "AI Group": group,
            "State": state,
            "Group Strength": round(strength, 1),
            "Average Institutional": round(subset["Institutional Score"].mean(), 1),
            "Average Opportunity": round(subset["Opportunity Score"].mean(), 1),
            "Average RS vs SPY": round(subset["RS vs SPY 3M %"].mean(), 1),
            "Stocks": len(subset),
            "Leader": subset.sort_values("Opportunity Score", ascending=False).iloc[0]["Ticker"],
        })
    return pd.DataFrame(rows).sort_values("Group Strength", ascending=False) if rows else pd.DataFrame()


with st.expander("⚙️ Screener settings", expanded=False):
    c1, c2, c3 = st.columns(3)
    universe_name = c1.selectbox("Universe", list(UNIVERSES.keys()))
    volume_ratio = c2.slider("Minimum volume ratio", 1.0, 4.0, 1.5, .1)
    base_days = c3.slider("Base length", 15, 90, 40, 5)

    c4, c5, c6 = st.columns(3)
    max_base = c4.slider("Maximum base range", 8, 40, 22, 1) / 100
    breakout_days = c5.slider("Breakout lookback", 10, 90, 40, 5)
    min_dollar_vol = c6.number_input("Minimum avg dollar volume ($M)", 1.0, 5000.0, 25.0, 5.0)

    custom = st.text_area(
        "Optional custom tickers (comma-separated). Leave blank to use the selected universe.",
        "",
        placeholder="NVDA, AVGO, MU, EQT, BIIB",
    )
    include_fund = st.checkbox(
        "Include fundamentals and analyst data for every stock (slower)",
        value=False,
    )
    auto_hidden_fund = st.checkbox(
        "Automatically research under-$20 hidden-gem candidates",
        value=True,
        help="Fetches fundamentals and the next scheduled earnings date only for qualifying under-$20 candidates.",
    )

params = Params(
    min_volume_ratio=volume_ratio,
    base_days=base_days,
    max_base_range=max_base,
    breakout_days=breakout_days,
    min_avg_dollar_volume=min_dollar_vol * 1_000_000,
)

hidden_params = Params(
    min_volume_ratio=volume_ratio,
    base_days=base_days,
    max_base_range=max_base,
    breakout_days=breakout_days,
    min_price=1.0,
    min_avg_dollar_volume=2_000_000,
)

tickers = [clean_ticker(t) for t in custom.split(",") if t.strip()] if custom.strip() else UNIVERSES[universe_name]

session_fraction, session_label = market_elapsed_fraction()
st.caption(f"⏱️ {session_label}. Selected universe: {len(tickers)} stocks. Intraday volume pace adjusts today's volume for time elapsed.")

if st.button("🔍 Run V4.1 intelligence scan", type="primary", use_container_width=True):
    with st.spinner(f"Scanning {len(tickers)} stocks…"):
        benchmarks = download_prices(("SPY", "NVDA"))
        spy = frame_for(benchmarks, "SPY", 2)
        nvda = frame_for(benchmarks, "NVDA", 2)
        raw = download_prices(tuple(tickers))

        rows = []
        bar = st.progress(0)
        for i, ticker in enumerate(tickers):
            df = frame_for(raw, ticker, len(tickers))
            active_params = hidden_params if ticker in HIDDEN_GEM_TICKERS else params
            row = technical_row(ticker, df, spy, nvda, active_params, session_fraction)
            if row:
                row["Hidden Gem Groups"] = ", ".join(HIDDEN_TICKER_TO_GROUPS.get(ticker, []))
                should_research_hidden = auto_hidden_fund and ticker in HIDDEN_GEM_TICKERS and row["Price"] <= 20
                if include_fund or should_research_hidden:
                    f = fundamentals(ticker)
                    row.update(f)
                rows.append(row)
            bar.progress((i + 1) / len(tickers))
        bar.empty()

    results = pd.DataFrame(rows)
    if results.empty:
        st.warning("No usable results were returned. Try another universe or loosen the filters.")
    else:
        # First-pass sector strength using institutional/quality/readiness data.
        preliminary_heat = {}
        for group, members in AI_GROUPS.items():
            subset = results[results["Ticker"].isin(members)]
            if not subset.empty:
                preliminary_heat[group] = float(np.clip(
                    subset["Institutional Score"].mean() * 0.5
                    + subset["Quality Score"].mean() * 0.3
                    + subset["Readiness Score"].mean() * 0.2,
                    0, 100,
                ))

        opportunity_scores = []
        for _, row in results.iterrows():
            groups = TICKER_TO_GROUPS.get(row["Ticker"], [])
            sector_strength = max([preliminary_heat.get(g, 50.0) for g in groups], default=50.0)
            opportunity_scores.append(score_opportunity(
                breakout_pct=row["Breakout %"] / 100,
                intraday_volume_pace=row["Intraday Volume Pace"],
                price=row["Price"],
                ma50=row["MA50"],
                ma150=row["MA150"],
                ma200=row["200D MA"],
                distance_200=row["Distance From 200D MA %"] / 100,
                rsi=row["RSI 14"],
                base_range=row["Base Range %"] / 100,
                max_base_range=params.max_base_range,
                atr_compression=row["ATR Compression"],
                sector_strength=sector_strength,
                institutional_score=row["Institutional Score"],
            ))
        results["Opportunity Score"] = opportunity_scores

        if include_fund and "Fundamental Score" in results.columns:
            results["Opportunity Score"] = np.minimum(
                100,
                results["Opportunity Score"] + results["Fundamental Score"].fillna(0) * 0.35,
            ).round(1)

        # Fundamental ownership is a useful confirmation, but not the same as
        # current accumulation. Keep its influence intentionally modest.
        if "Institutional Ownership %" in results.columns:
            ownership_bonus = results["Institutional Ownership %"].fillna(0).clip(0, 90) / 30
            results["Institutional Score"] = np.minimum(100, results["Institutional Score"] + ownership_bonus).round(1)

        results["Hidden Gem Score"] = np.nan
        hidden_mask = (
            results["Ticker"].isin(HIDDEN_GEM_TICKERS)
            & (results["Price"] <= 20)
            & (results["Price"] >= 1)
        )
        if hidden_mask.any():
            results.loc[hidden_mask, "Hidden Gem Score"] = results.loc[hidden_mask].apply(hidden_gem_score, axis=1)

        results = results.sort_values(
            ["Opportunity Score", "Institutional Score", "Readiness Score"],
            ascending=[False, False, False],
        )
        st.session_state["results_v4"] = results
        st.session_state["heatmap_v4"] = build_heatmap(results)

if "results_v4" in st.session_state:
    results = st.session_state["results_v4"]
    heatmap = st.session_state.get("heatmap_v4", pd.DataFrame())

    st.subheader("🧠 V4.0.1 Intelligence Dashboard")
    top_opportunity = results.iloc[0]
    top_institutional = results.sort_values("Institutional Score", ascending=False).iloc[0]
    strongest_group = heatmap.iloc[0] if not heatmap.empty else None
    best_pullback = results[results["AI 200D Pullback Watch"]].sort_values("Opportunity Score", ascending=False)
    best_pullback_ticker = best_pullback.iloc[0]["Ticker"] if not best_pullback.empty else "None"

    d1, d2, d3, d4, d5 = st.columns(5)
    d1.metric("Stocks analyzed", len(results))
    d2.metric("Top opportunity", f"{top_opportunity['Ticker']} · {top_opportunity['Opportunity Score']:.0f}")
    d3.metric("Top institutional", f"{top_institutional['Ticker']} · {top_institutional['Institutional Score']:.0f}")
    d4.metric("Strongest AI group", strongest_group["AI Group"] if strongest_group is not None else "N/A")
    d5.metric("Best 200D pullback", best_pullback_ticker)

    st.subheader("🔥 AI leadership heatmap")
    if heatmap.empty:
        st.info("The selected universe did not contain enough AI-group stocks to build a heatmap.")
    else:
        st.dataframe(
            heatmap,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Group Strength": st.column_config.ProgressColumn(min_value=0, max_value=100, format="%.0f"),
                "Average Institutional": st.column_config.ProgressColumn(min_value=0, max_value=100, format="%.0f"),
                "Average Opportunity": st.column_config.ProgressColumn(min_value=0, max_value=100, format="%.0f"),
                "Average RS vs SPY": st.column_config.NumberColumn(format="%.1f%%"),
            },
        )

    st.subheader("📉 Biggest AI semiconductor pullbacks today")
    semi_pullbacks = results[
        results["Ticker"].isin(AI_SEMI_PULLBACK_TICKERS)
        & results["Day Change %"].notna()
        & (results["Day Change %"] < 0)
    ].sort_values("Day Change %", ascending=True).head(15).copy()

    if semi_pullbacks.empty:
        st.info("No scanned AI semiconductor companies are currently down on the day.")
    else:
        st.dataframe(
            semi_pullbacks[[
                "Ticker","AI Groups","Price","Day Change %","Day Change $",
                "Intraday Volume Pace","Opportunity Score","Institutional Score",
                "Distance From 200D MA %","TradingView"
            ]],
            use_container_width=True,
            hide_index=True,
            column_config={
                "Price": st.column_config.NumberColumn(format="$%.2f"),
                "Day Change %": st.column_config.NumberColumn("Today's pullback", format="%.2f%%"),
                "Day Change $": st.column_config.NumberColumn("Dollar move", format="$%.2f"),
                "Intraday Volume Pace": st.column_config.NumberColumn("Vol pace", format="%.2fx"),
                "Opportunity Score": st.column_config.ProgressColumn(min_value=0, max_value=100, format="%.0f"),
                "Institutional Score": st.column_config.ProgressColumn(min_value=0, max_value=100, format="%.0f"),
                "Distance From 200D MA %": st.column_config.NumberColumn("From 200D MA", format="%.2f%%"),
                "TradingView": st.column_config.LinkColumn("Chart", display_text="Open"),
            },
        )
    st.caption("This ranks the largest same-day percentage declines among AI chips, memory/storage, and semiconductor-equipment companies. A large one-day drop can be a buying opportunity or a warning; confirm the news, earnings context, volume, and technical support before acting.")

    st.subheader("💎 Hidden Gem Scanner — under $20")
    hidden = results[
        results["Ticker"].isin(HIDDEN_GEM_TICKERS)
        & results["Price"].between(1, 20, inclusive="both")
    ].copy()
    if "Market Cap" in hidden.columns:
        hidden = hidden[(hidden["Market Cap"].isna()) | hidden["Market Cap"].between(50_000_000, 15_000_000_000, inclusive="both")]
    hidden = hidden.sort_values(["Hidden Gem Score", "Opportunity Score", "Institutional Score"], ascending=False).head(20)
    if hidden.empty:
        st.info("No researched under-$20 candidates passed the current liquidity and technical filters. Select the V4.1 or Hidden Gems universe and run the scan again.")
    else:
        hidden_cols = [c for c in [
            "Ticker","Hidden Gem Groups","Price","Hidden Gem Score","Opportunity Score","Institutional Score",
            "Revenue Growth %","FCF Margin %","Free Cash Flow","Market Cap","Analyst Target Upside %",
            "Catalyst","Days to Earnings","Intraday Volume Pace","Distance to Breakout %","TradingView"
        ] if c in hidden.columns]
        hidden_display = hidden[hidden_cols].copy()
        st.dataframe(
            hidden_display, use_container_width=True, hide_index=True,
            column_config={
                "Price": st.column_config.NumberColumn(format="$%.2f"),
                "Hidden Gem Score": st.column_config.ProgressColumn(min_value=0, max_value=100, format="%.0f"),
                "Opportunity Score": st.column_config.ProgressColumn(min_value=0, max_value=100, format="%.0f"),
                "Institutional Score": st.column_config.ProgressColumn(min_value=0, max_value=100, format="%.0f"),
                "Revenue Growth %": st.column_config.NumberColumn(format="%.1f%%"),
                "FCF Margin %": st.column_config.NumberColumn(format="%.1f%%"),
                "Free Cash Flow": st.column_config.NumberColumn(format="$%.0f"),
                "Market Cap": st.column_config.NumberColumn(format="$%.0f"),
                "Analyst Target Upside %": st.column_config.NumberColumn(format="%.1f%%"),
                "Days to Earnings": st.column_config.NumberColumn(format="%.0f days"),
                "Intraday Volume Pace": st.column_config.NumberColumn("Vol pace", format="%.2fx"),
                "Distance to Breakout %": st.column_config.NumberColumn("To breakout", format="%.2f%%"),
                "TradingView": st.column_config.LinkColumn("Chart", display_text="Open"),
            },
        )
        st.caption("Hidden Gem Score rewards improving fundamentals, positive free cash flow, accumulation, technical opportunity, liquidity, and a verifiable scheduled earnings catalyst. It does not estimate the probability that the catalyst outcome will be positive.")

    st.subheader("🦅 Smart Money Radar")
    smart = results[
        (results["Institutional Score"] >= 65)
        & (results["CMF 20"] > 0)
        & (results["OBV Trend 20D %"] > 0)
    ].sort_values(["Institutional Score", "Opportunity Score"], ascending=False).head(15)
    if smart.empty:
        st.info("No stocks currently meet all Smart Money Radar confirmation rules.")
    else:
        st.dataframe(
            smart[["Ticker","AI Groups","Hidden Gem Groups","Institutional Score","Opportunity Score","CMF 20","OBV Trend 20D %","Up/Down Volume Ratio","RS vs SPY 3M %","Intraday Volume Pace","TradingView"]],
            use_container_width=True, hide_index=True,
            column_config={
                "Institutional Score": st.column_config.ProgressColumn(min_value=0, max_value=100, format="%.0f"),
                "Opportunity Score": st.column_config.ProgressColumn(min_value=0, max_value=100, format="%.0f"),
                "CMF 20": st.column_config.NumberColumn(format="%.2f"),
                "OBV Trend 20D %": st.column_config.NumberColumn(format="%.1f%%"),
                "Up/Down Volume Ratio": st.column_config.NumberColumn(format="%.2fx"),
                "RS vs SPY 3M %": st.column_config.NumberColumn(format="%.1f%%"),
                "Intraday Volume Pace": st.column_config.NumberColumn(format="%.2fx"),
                "TradingView": st.column_config.LinkColumn("Chart", display_text="Open"),
            },
        )

    a1, a2 = st.columns(2)
    with a1:
        st.subheader("🏆 Highest Opportunity Scores")
        opp_cols = ["Ticker","AI Groups","Opportunity Score","Institutional Score","Distance to Breakout %","Intraday Volume Pace","RSI 14","Status","TradingView"]
        st.dataframe(
            results.head(12)[opp_cols],
            use_container_width=True,
            hide_index=True,
            column_config={
                "Opportunity Score": st.column_config.ProgressColumn(min_value=0, max_value=100, format="%.0f"),
                "Institutional Score": st.column_config.ProgressColumn(min_value=0, max_value=100, format="%.0f"),
                "Distance to Breakout %": st.column_config.NumberColumn("To breakout", format="%.2f%%"),
                "Intraday Volume Pace": st.column_config.NumberColumn("Vol pace", format="%.2fx"),
                "RSI 14": st.column_config.NumberColumn(format="%.1f"),
                "TradingView": st.column_config.LinkColumn("Chart", display_text="Open"),
            },
        )

    with a2:
        st.subheader("🏦 Highest Institutional Scores")
        inst = results.sort_values("Institutional Score", ascending=False).head(12)
        inst_cols = ["Ticker","AI Groups","Institutional Score","CMF 20","OBV Trend 20D %","A/D Trend 20D %","Up/Down Volume Ratio","RS vs SPY 3M %","RS vs NVDA 3M %","TradingView"]
        st.dataframe(
            inst[inst_cols],
            use_container_width=True,
            hide_index=True,
            column_config={
                "Institutional Score": st.column_config.ProgressColumn(min_value=0, max_value=100, format="%.0f"),
                "CMF 20": st.column_config.NumberColumn(format="%.2f"),
                "OBV Trend 20D %": st.column_config.NumberColumn(format="%.1f%%"),
                "A/D Trend 20D %": st.column_config.NumberColumn(format="%.1f%%"),
                "Up/Down Volume Ratio": st.column_config.NumberColumn(format="%.2fx"),
                "RS vs SPY 3M %": st.column_config.NumberColumn(format="%.1f%%"),
                "RS vs NVDA 3M %": st.column_config.NumberColumn(format="%.1f%%"),
                "TradingView": st.column_config.LinkColumn("Chart", display_text="Open"),
            },
        )

    st.subheader("🚦 Closest to trigger")
    closest = results[results["Distance to Breakout %"].between(-5, 1, inclusive="both")].sort_values(
        ["Alert Ready", "Distance to Breakout %", "Intraday Volume Pace"],
        ascending=[False, False, False],
    ).head(10)
    if closest.empty:
        st.info("No stocks are currently within 5% of their breakout level.")
    else:
        st.dataframe(
            closest[["Ticker","Alert Stage","Status","Distance to Breakout %","Intraday Volume Pace","Readiness Score","Opportunity Score","TradingView"]],
            use_container_width=True,
            hide_index=True,
            column_config={
                "Distance to Breakout %": st.column_config.NumberColumn("To breakout", format="%.2f%%"),
                "Intraday Volume Pace": st.column_config.NumberColumn("Vol pace", format="%.2fx"),
                "Readiness Score": st.column_config.ProgressColumn(min_value=0, max_value=100, format="%.0f"),
                "Opportunity Score": st.column_config.ProgressColumn(min_value=0, max_value=100, format="%.0f"),
                "TradingView": st.column_config.LinkColumn("Chart", display_text="Open"),
            },
        )

    st.subheader("⚡ Unusual-volume watch")
    unusual = results[results["Intraday Volume Pace"] >= volume_ratio].sort_values(
        ["Intraday Volume Pace", "Opportunity Score"], ascending=[False, False]
    ).head(12)
    if unusual.empty:
        st.info(f"No stocks currently have conservative volume pace of {volume_ratio:.1f}× or higher.")
    else:
        st.dataframe(
            unusual[["Ticker","Intraday Volume Pace","Distance to Breakout %","Opportunity Score","Institutional Score","Status","TradingView"]],
            use_container_width=True,
            hide_index=True,
            column_config={
                "Intraday Volume Pace": st.column_config.NumberColumn("Vol pace", format="%.2fx"),
                "Distance to Breakout %": st.column_config.NumberColumn("To breakout", format="%.2f%%"),
                "Opportunity Score": st.column_config.ProgressColumn(min_value=0, max_value=100, format="%.0f"),
                "Institutional Score": st.column_config.ProgressColumn(min_value=0, max_value=100, format="%.0f"),
                "TradingView": st.column_config.LinkColumn("Chart", display_text="Open"),
            },
        )

    st.subheader("🧲 AI pullbacks near the 200-day moving average")
    ai200 = results[results["AI 200D Pullback Watch"]].copy()
    ai200["Absolute 200D Distance"] = ai200["Distance From 200D MA %"].abs()
    ai200 = ai200.sort_values(["Opportunity Score", "Absolute 200D Distance"], ascending=[False, True]).head(15)
    if ai200.empty:
        st.info("No scanned AI stocks are currently within 6% above or 3% below a stable/rising 200-day moving average.")
    else:
        st.dataframe(
            ai200[["Ticker","AI Groups","Price","200D MA","Distance From 200D MA %","200D MA Slope %","Opportunity Score","Institutional Score","Intraday Volume Pace","TradingView"]],
            use_container_width=True,
            hide_index=True,
            column_config={
                "Price": st.column_config.NumberColumn(format="$%.2f"),
                "200D MA": st.column_config.NumberColumn(format="$%.2f"),
                "Distance From 200D MA %": st.column_config.NumberColumn("From 200D MA", format="%.2f%%"),
                "200D MA Slope %": st.column_config.NumberColumn("200D slope", format="%.2f%%"),
                "Opportunity Score": st.column_config.ProgressColumn(min_value=0, max_value=100, format="%.0f"),
                "Institutional Score": st.column_config.ProgressColumn(min_value=0, max_value=100, format="%.0f"),
                "Intraday Volume Pace": st.column_config.NumberColumn("Vol pace", format="%.2fx"),
                "TradingView": st.column_config.LinkColumn("Chart", display_text="Open"),
            },
        )
    st.caption("The 200-day moving average can act as support during a major pullback, but proximity alone is not a buy signal. Look for stabilization, improving volume, and strengthening money flow.")

    st.subheader("📋 Full ranked intelligence table")
    preferred = [
        "Ticker","AI Groups","Hidden Gem Groups","Hidden Gem Score","Opportunity Score","Institutional Score","Readiness Score","Quality Score","Setup","Status","Why",
        "Price","Previous Close","Day Change $","Day Change %","AI Semi Pullback","Breakout Level","Distance to Breakout %","Intraday Volume Pace","Volume Ratio","RSI 14","CMF 20",
        "OBV Trend 20D %","A/D Trend 20D %","Up/Down Volume Ratio","RS vs SPY 3M %","RS vs NVDA 3M %",
        "MA50","MA150","200D MA","50D MA Slope %","150D MA Slope %","200D MA Slope %",
        "Distance From 150D MA %","Distance From 200D MA %","AI 200D Pullback Watch","Base Range %","ATR Compression",
        "Alert Ready","TradingView","Revenue Growth %","EPS Growth %","FCF Margin %","Gross Margin %",
        "Institutional Ownership %","Insider Ownership %","Forward P/E","Analyst Target Upside %","Market Cap",
    ]
    cols = [c for c in preferred if c in results.columns]
    display = results[cols].copy()
    if "Market Cap" in display.columns:
        display["Market Cap"] = display["Market Cap"].apply(lambda x: f"${x/1e9:.1f}B" if pd.notna(x) else "")

    st.dataframe(
        display,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Opportunity Score": st.column_config.ProgressColumn(min_value=0, max_value=100, format="%.0f"),
            "Institutional Score": st.column_config.ProgressColumn(min_value=0, max_value=100, format="%.0f"),
            "Readiness Score": st.column_config.ProgressColumn(min_value=0, max_value=100, format="%.0f"),
            "Quality Score": st.column_config.ProgressColumn(min_value=0, max_value=100, format="%.0f"),
            "Price": st.column_config.NumberColumn(format="$%.2f"),
            "Previous Close": st.column_config.NumberColumn(format="$%.2f"),
            "Day Change $": st.column_config.NumberColumn(format="$%.2f"),
            "Day Change %": st.column_config.NumberColumn(format="%.2f%%"),
            "AI Semi Pullback": st.column_config.CheckboxColumn(),
            "Breakout Level": st.column_config.NumberColumn(format="$%.2f"),
            "MA50": st.column_config.NumberColumn(format="$%.2f"),
            "MA150": st.column_config.NumberColumn(format="$%.2f"),
            "200D MA": st.column_config.NumberColumn(format="$%.2f"),
            "Volume Ratio": st.column_config.NumberColumn(format="%.2fx"),
            "Intraday Volume Pace": st.column_config.NumberColumn(format="%.2fx"),
            "Distance to Breakout %": st.column_config.NumberColumn(format="%.2f%%"),
            "Distance From 150D MA %": st.column_config.NumberColumn(format="%.2f%%"),
            "Distance From 200D MA %": st.column_config.NumberColumn(format="%.2f%%"),
            "AI 200D Pullback Watch": st.column_config.CheckboxColumn(),
            "Alert Ready": st.column_config.CheckboxColumn(),
            "TradingView": st.column_config.LinkColumn("Chart", display_text="Open"),
        },
    )

    st.download_button(
        "⬇️ Download V4.1 results",
        results.to_csv(index=False).encode("utf-8"),
        "heartbeat_v4_0_1_results.csv",
        "text/csv",
        use_container_width=True,
    )

    st.subheader("Chart inspection")
    chosen = st.selectbox("Choose a stock", results["Ticker"].tolist())
    chart_raw = download_prices((chosen,), period="1y")
    chart_df = frame_for(chart_raw, chosen, 1)
    if not chart_df.empty:
        price_chart = pd.DataFrame({
            chosen: chart_df["Close"],
            "50-day moving average": chart_df["Close"].rolling(50).mean(),
            "150-day moving average": chart_df["Close"].rolling(150).mean(),
            "200-day moving average": chart_df["Close"].rolling(200).mean(),
        })
        st.line_chart(price_chart, height=340)

        vol_chart = pd.DataFrame({
            "Daily volume": chart_df["Volume"],
            "50-day average": chart_df["Volume"].rolling(50).mean(),
        }).tail(120)
        st.bar_chart(vol_chart, height=260)

st.markdown(
    """
    <div class="note">
      <b>Important:</b> V4.1 ranks technical opportunity and evidence of accumulation; it does not predict outcomes or guarantee gains.
      Institutional Score is an estimate built from public price-and-volume behavior, not verified real-time institutional order flow.
      Always inspect the chart, earnings date, and company-specific risks before acting.
    </div>
    """,
    unsafe_allow_html=True,
)
