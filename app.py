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
    page_title="Alpha Capital V5.1",
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
      <h1>📈 Alpha Capital V5.1</h1>
      <p>Business-first stock research: company quality, debt quality, future growth, accumulation, breakout timing, pullbacks, and hidden gems.</p>
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


def score_accumulation(
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
    accumulation_score: float,
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
    score += accumulation_score * 0.10

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

    accumulation_score = score_accumulation(
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
        "Accumulation Score": accumulation_score,
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
    score += min(float(row.get("Accumulation Score", 0)), 100) * 0.20

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
    """Business-first research model. Debt is judged by affordability and purpose,
    not by the headline balance alone. Analyst targets are displayed but do not
    drive the Alpha Business Score.
    """
    def val(info: dict, key: str):
        x = info.get(key)
        try:
            return float(x) if x is not None and np.isfinite(float(x)) else np.nan
        except Exception:
            return np.nan

    def pts(x, rules, missing=0.0):
        if pd.isna(x):
            return missing
        for threshold, score in rules:
            if x >= threshold:
                return score
        return 0.0

    try:
        stock = yf.Ticker(ticker)
        info = stock.info or {}

        price = val(info, "currentPrice")
        if pd.isna(price):
            price = val(info, "regularMarketPrice")
        target = val(info, "targetMeanPrice")
        revenue_growth = val(info, "revenueGrowth")
        earnings_growth = val(info, "earningsGrowth")
        gross_margin = val(info, "grossMargins")
        op_margin = val(info, "operatingMargins")
        profit_margin = val(info, "profitMargins")
        fcf = val(info, "freeCashflow")
        operating_cf = val(info, "operatingCashflow")
        revenue = val(info, "totalRevenue")
        cash = val(info, "totalCash")
        debt = val(info, "totalDebt")
        ebitda = val(info, "ebitda")
        current_ratio = val(info, "currentRatio")
        quick_ratio = val(info, "quickRatio")
        roe = val(info, "returnOnEquity")
        roa = val(info, "returnOnAssets")
        forward_pe = val(info, "forwardPE")
        peg = val(info, "pegRatio")
        ev_ebitda = val(info, "enterpriseToEbitda")
        market_cap = val(info, "marketCap")
        shares = val(info, "sharesOutstanding")
        float_shares = val(info, "floatShares")
        inst = val(info, "heldPercentInstitutions")
        insider = val(info, "heldPercentInsiders")
        short_float = val(info, "shortPercentOfFloat")

        fcf_margin = fcf / revenue if pd.notna(fcf) and pd.notna(revenue) and revenue != 0 else np.nan
        debt_to_ebitda = debt / ebitda if pd.notna(debt) and pd.notna(ebitda) and ebitda > 0 else np.nan
        net_debt = debt - cash if pd.notna(debt) and pd.notna(cash) else np.nan
        debt_to_fcf = debt / fcf if pd.notna(debt) and pd.notna(fcf) and fcf > 0 else np.nan
        cash_to_debt = cash / debt if pd.notna(cash) and pd.notna(debt) and debt > 0 else np.nan
        implied_capex = operating_cf - fcf if pd.notna(operating_cf) and pd.notna(fcf) else np.nan
        capex_to_revenue = implied_capex / revenue if pd.notna(implied_capex) and pd.notna(revenue) and revenue > 0 else np.nan
        target_upside = target / price - 1 if pd.notna(target) and pd.notna(price) and price > 0 else np.nan

        # 1) Business Quality — 25 points
        business_quality = 0.0
        business_quality += pts(revenue_growth, [(0.25, 6), (0.15, 5), (0.08, 4), (0.03, 2), (0.0, 1)])
        business_quality += pts(earnings_growth, [(0.25, 5), (0.15, 4), (0.08, 3), (0.0, 1)])
        business_quality += pts(fcf_margin, [(0.25, 5), (0.15, 4), (0.08, 3), (0.0, 1)])
        business_quality += pts(op_margin, [(0.30, 4), (0.20, 3), (0.10, 2), (0.0, 1)])
        business_quality += pts(roe, [(0.30, 3), (0.20, 2.5), (0.12, 1.5), (0.0, .5)])
        business_quality += pts(roa, [(0.15, 2), (0.08, 1.5), (0.03, .75), (0.0, .25)])

        # 2) Financial Strength — 20 points. High debt is acceptable when cash
        # generation, EBITDA and liquidity comfortably support it.
        financial_strength = 0.0
        if pd.notna(debt_to_ebitda):
            financial_strength += 7 if debt_to_ebitda <= 1 else 6 if debt_to_ebitda <= 2 else 4.5 if debt_to_ebitda <= 3 else 2.5 if debt_to_ebitda <= 4.5 else 0.5
        elif pd.notna(cash_to_debt):
            financial_strength += 7 if cash_to_debt >= 1 else 5 if cash_to_debt >= .5 else 2
        if pd.notna(debt_to_fcf):
            financial_strength += 5 if debt_to_fcf <= 2 else 4 if debt_to_fcf <= 4 else 2.5 if debt_to_fcf <= 7 else .5
        elif pd.notna(fcf) and fcf > 0:
            financial_strength += 2
        financial_strength += pts(current_ratio, [(2.0, 4), (1.5, 3.5), (1.0, 2.5), (.75, 1)])
        financial_strength += pts(fcf_margin, [(.20, 4), (.10, 3), (.03, 2), (0.0, 1)])

        # 3) Capital Allocation — 15 points. Reward productive reinvestment;
        # penalize weak returns, dilution and spending without growth.
        capital_allocation = 0.0
        capital_allocation += pts(roe, [(.30, 4), (.20, 3), (.12, 2), (0.0, .5)])
        capital_allocation += pts(roa, [(.15, 3), (.08, 2), (.03, 1), (0.0, .25)])
        if pd.notna(implied_capex) and implied_capex > 0:
            growth_investment = (pd.notna(revenue_growth) and revenue_growth >= .08 and pd.notna(op_margin) and op_margin > 0)
            capital_allocation += 4 if growth_investment else 2 if pd.notna(fcf) and fcf > 0 else 0
        elif pd.notna(fcf) and fcf > 0:
            capital_allocation += 3
        dilution_ratio = shares / float_shares if pd.notna(shares) and pd.notna(float_shares) and float_shares > 0 else np.nan
        capital_allocation += 2 if pd.isna(dilution_ratio) or dilution_ratio <= 1.08 else 1 if dilution_ratio <= 1.18 else 0
        capital_allocation += 2 if pd.notna(fcf) and fcf > 0 else 0

        # 4) Future Growth — 20 points. Mostly operating evidence; Wall Street's
        # price target is intentionally excluded.
        future_growth = 0.0
        future_growth += pts(revenue_growth, [(.30, 8), (.20, 7), (.12, 5.5), (.07, 4), (.02, 2), (0.0, 1)])
        future_growth += pts(earnings_growth, [(.30, 7), (.20, 6), (.12, 4.5), (.05, 3), (0.0, 1)])
        future_growth += pts(gross_margin, [(.70, 3), (.50, 2.5), (.30, 1.5), (.15, .75)])
        future_growth += 2 if pd.notna(implied_capex) and implied_capex > 0 and pd.notna(revenue_growth) and revenue_growth > .08 else 0

        # 5) Competitive Advantage — 10 points (measurable moat proxies).
        competitive_advantage = 0.0
        competitive_advantage += pts(gross_margin, [(.70, 3), (.50, 2.5), (.35, 2), (.20, 1)])
        competitive_advantage += pts(op_margin, [(.35, 2.5), (.25, 2), (.15, 1.5), (.05, .75)])
        competitive_advantage += pts(roe, [(.35, 2.5), (.25, 2), (.15, 1), (0.0, .25)])
        competitive_advantage += pts(fcf_margin, [(.25, 2), (.15, 1.5), (.08, 1), (0.0, .25)])

        # 6) Valuation — 10 points. Cheap relative to growth, not merely low P/E.
        valuation = 0.0
        if pd.notna(peg) and peg > 0:
            valuation += 5 if peg <= 1 else 4 if peg <= 1.5 else 2.5 if peg <= 2.2 else 1
        elif pd.notna(forward_pe):
            valuation += 4 if 0 < forward_pe <= 18 else 3 if forward_pe <= 28 else 1.5 if forward_pe <= 40 else .5
        if pd.notna(ev_ebitda):
            valuation += 3 if 0 < ev_ebitda <= 12 else 2 if ev_ebitda <= 20 else 1 if ev_ebitda <= 30 else 0
        if pd.notna(market_cap) and market_cap > 0 and pd.notna(fcf):
            fcf_yield = fcf / market_cap
            valuation += 2 if fcf_yield >= .06 else 1.5 if fcf_yield >= .035 else .75 if fcf_yield > 0 else 0
        else:
            fcf_yield = np.nan

        alpha_business = business_quality + financial_strength + capital_allocation + future_growth + competitive_advantage + valuation
        alpha_business = round(float(np.clip(alpha_business, 0, 100)), 1)

        moat_score = round(float(np.clip(competitive_advantage * 7 + business_quality * 1.2, 0, 100)), 1)
        management_score = round(float(np.clip(capital_allocation * 5 + business_quality, 0, 100)), 1)

        growth_investment_flag = bool(
            pd.notna(implied_capex) and implied_capex > 0
            and pd.notna(revenue_growth) and revenue_growth >= .08
            and pd.notna(op_margin) and op_margin > 0
        )
        debt_quality = (
            "🟢 Well supported" if (pd.notna(debt_to_ebitda) and debt_to_ebitda <= 3 and pd.notna(fcf) and fcf > 0)
            else "🟡 Manageable / monitor" if (pd.notna(debt_to_ebitda) and debt_to_ebitda <= 4.5 and pd.notna(fcf) and fcf > 0)
            else "🔴 Elevated risk" if pd.notna(debt) and debt > 0
            else "⚪ Limited data"
        )
        rating = "★★★★★ Elite" if alpha_business >= 90 else "★★★★ Strong" if alpha_business >= 80 else "★★★ Above Average" if alpha_business >= 70 else "★★ Developing" if alpha_business >= 55 else "★ Speculative"

        strengths = []
        if pd.notna(revenue_growth) and revenue_growth >= .15: strengths.append("rapid revenue growth")
        if pd.notna(fcf_margin) and fcf_margin >= .15: strengths.append("strong free-cash-flow margins")
        if pd.notna(gross_margin) and gross_margin >= .50: strengths.append("high gross margins")
        if growth_investment_flag: strengths.append("productive growth investment")
        if debt_quality == "🟢 Well supported": strengths.append("well-supported debt")
        if not strengths: strengths.append("balanced operating profile")
        thesis = f"{info.get('shortName', ticker)} shows " + ", ".join(strengths[:3]) + "."

        risks = []
        if pd.notna(debt_to_ebitda) and debt_to_ebitda > 4.5: risks.append("high leverage relative to EBITDA")
        if pd.notna(fcf) and fcf < 0: risks.append("negative free cash flow")
        if pd.notna(revenue_growth) and revenue_growth < 0: risks.append("declining revenue")
        if pd.notna(forward_pe) and forward_pe > 40: risks.append("premium valuation")
        if pd.notna(op_margin) and op_margin < 0: risks.append("negative operating margin")
        if growth_investment_flag and pd.notna(fcf_margin) and fcf_margin < .05: risks.append("investment cycle is pressuring near-term free cash flow")
        risk_text = "; ".join(risks[:3]) if risks else "No major quantitative warning identified; review company-specific execution risks."

        next_earnings = pd.NaT
        try:
            cal = stock.calendar
            if isinstance(cal, dict):
                raw_date = cal.get("Earnings Date")
                if isinstance(raw_date, (list, tuple)) and raw_date:
                    next_earnings = pd.Timestamp(raw_date[0])
                elif raw_date is not None:
                    next_earnings = pd.Timestamp(raw_date)
            elif isinstance(cal, pd.DataFrame) and not cal.empty and "Earnings Date" in cal.index:
                next_earnings = pd.Timestamp(cal.loc["Earnings Date"].iloc[0])
        except Exception:
            pass
        days_to_earnings = safe_days_to_date(next_earnings) if pd.notna(next_earnings) else np.nan

        return {
            "Company": info.get("shortName", ticker),
            "Alpha Business Score": alpha_business,
            "Alpha Rating": rating,
            "Business Quality": round(business_quality, 1),
            "Financial Strength": round(financial_strength, 1),
            "Capital Allocation": round(capital_allocation, 1),
            "Future Growth": round(future_growth, 1),
            "Competitive Advantage": round(competitive_advantage, 1),
            "Valuation Score": round(valuation, 1),
            "Moat Score": moat_score,
            "Management Score": management_score,
            "Debt Quality": debt_quality,
            "Growth Investment": growth_investment_flag,
            "Alpha Thesis": thesis,
            "Alpha Risks": risk_text,
            "Revenue Growth %": revenue_growth * 100 if pd.notna(revenue_growth) else np.nan,
            "EPS Growth %": earnings_growth * 100 if pd.notna(earnings_growth) else np.nan,
            "Gross Margin %": gross_margin * 100 if pd.notna(gross_margin) else np.nan,
            "Operating Margin %": op_margin * 100 if pd.notna(op_margin) else np.nan,
            "Profit Margin %": profit_margin * 100 if pd.notna(profit_margin) else np.nan,
            "FCF Margin %": fcf_margin * 100 if pd.notna(fcf_margin) else np.nan,
            "ROE %": roe * 100 if pd.notna(roe) else np.nan,
            "ROA %": roa * 100 if pd.notna(roa) else np.nan,
            "Current Ratio": current_ratio,
            "Debt / EBITDA": debt_to_ebitda,
            "Debt / FCF": debt_to_fcf,
            "Cash / Debt": cash_to_debt,
            "Net Debt": net_debt,
            "Implied Capex": implied_capex,
            "Capex / Revenue %": capex_to_revenue * 100 if pd.notna(capex_to_revenue) else np.nan,
            "FCF Yield %": fcf_yield * 100 if pd.notna(fcf_yield) else np.nan,
            "Institutional Ownership %": inst * 100 if pd.notna(inst) else np.nan,
            "Insider Ownership %": insider * 100 if pd.notna(insider) else np.nan,
            "Forward P/E": forward_pe,
            "PEG": peg,
            "EV / EBITDA": ev_ebitda,
            "Analyst Target Upside %": target_upside * 100 if pd.notna(target_upside) else np.nan,
            "Market Cap": market_cap,
            "Free Cash Flow": fcf,
            "Operating Cash Flow": operating_cf,
            "Total Cash": cash,
            "Total Debt": debt,
            "Short Float %": short_float * 100 if pd.notna(short_float) else np.nan,
            "Sector": info.get("sector") or "",
            "Industry": info.get("industry") or "",
            "Next Earnings": next_earnings,
            "Days to Earnings": days_to_earnings,
            "Catalyst": "Scheduled earnings" if pd.notna(days_to_earnings) and 0 <= days_to_earnings <= 60 else "No scheduled event found",
            "Fundamental Score": alpha_business,
        }
    except Exception:
        return {
            "Company": ticker,
            "Alpha Business Score": 0.0,
            "Alpha Rating": "Data unavailable",
            "Alpha Thesis": "Fundamental data was unavailable.",
            "Alpha Risks": "Score could not be calculated.",
            "Fundamental Score": 0.0,
        }

def ensure_columns(df: pd.DataFrame, defaults: dict[str, object]) -> pd.DataFrame:
    """Add optional columns so technical-only scans still render safely."""
    for column, default in defaults.items():
        if column not in df.columns:
            df[column] = default
    return df


def opportunity_explanation(row: pd.Series) -> str:
    reasons: list[str] = []
    if row.get("Alpha Business Score", 0) >= 75:
        reasons.append("strong business")
    if row.get("Accumulation Score", 0) >= 65:
        reasons.append("institutional accumulation")
    if row.get("Readiness Score", 0) >= 70:
        reasons.append("technically ready")
    distance = row.get("Distance to Breakout %", np.nan)
    if pd.notna(distance) and -3 <= distance <= 1:
        reasons.append("near breakout")
    rsi = row.get("RSI 14", np.nan)
    if pd.notna(rsi) and 38 <= rsi <= 62:
        reasons.append("healthy RSI")
    if not reasons:
        reasons.append(str(row.get("Why", "setup still developing")))
    return ", ".join(reasons[:4])


def pullback_classification(row: pd.Series) -> tuple[str, str]:
    day = row.get("Day Change %", np.nan)
    dist = row.get("Distance From 200D MA %", np.nan)
    rsi = row.get("RSI 14", np.nan)
    business = row.get("Alpha Business Score", 0)
    accumulation = row.get("Accumulation Score", 0)
    slope = row.get("200D MA Slope %", np.nan)

    if business >= 70 and accumulation >= 55 and pd.notna(slope) and slope >= 0 and pd.notna(dist) and -10 <= dist <= 6:
        label = "🟢 Healthy pullback"
        why = "strong business, constructive long-term trend, and price near the 200-day average"
    elif business >= 70 and pd.notna(day) and day <= -3:
        label = "🟡 Emotional selloff"
        why = "large daily decline despite above-average business quality"
    elif pd.notna(rsi) and rsi <= 35 and business >= 60:
        label = "🟡 Oversold watch"
        why = "oversold momentum with acceptable business quality"
    elif pd.notna(slope) and slope < -3 and pd.notna(dist) and dist < -10:
        label = "🔴 Broken trend"
        why = "price is well below a falling 200-day average"
    else:
        label = "🟠 Needs confirmation"
        why = "pullback is present, but trend or accumulation confirmation is incomplete"
    return label, why


def build_heatmap(results: pd.DataFrame) -> pd.DataFrame:
    rows = []
    ai_results = results[results["Ticker"].isin(AI_TICKERS)].copy()
    for group, tickers in AI_GROUPS.items():
        subset = ai_results[ai_results["Ticker"].isin(tickers)]
        if subset.empty:
            continue
        strength = (
            subset["Accumulation Score"].mean() * 0.45
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
            "Average Institutional": round(subset["Accumulation Score"].mean(), 1),
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
        value=True,
        help="Required for Alpha Business Rankings. Turn off only for a fast technical-only scan.",
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

if st.button("🔍 Run Alpha Capital V5.1 scan", type="primary", use_container_width=True):
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
                    subset["Accumulation Score"].mean() * 0.5
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
                accumulation_score=row["Accumulation Score"],
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
            results["Accumulation Score"] = np.minimum(100, results["Accumulation Score"] + ownership_bonus).round(1)

        results["Hidden Gem Score"] = np.nan
        hidden_mask = (
            results["Ticker"].isin(HIDDEN_GEM_TICKERS)
            & (results["Price"] <= 20)
            & (results["Price"] >= 1)
        )
        if hidden_mask.any():
            results.loc[hidden_mask, "Hidden Gem Score"] = results.loc[hidden_mask].apply(hidden_gem_score, axis=1)

        results = ensure_columns(results, {
            "Alpha Business Score": 0.0,
            "Business Quality": 0.0,
            "Future Growth": 0.0,
            "Financial Strength": 0.0,
            "Debt Quality": "⚪ Limited data",
            "Revenue Growth %": np.nan,
            "FCF Margin %": np.nan,
            "Days to Earnings": np.nan,
            "Catalyst": "No scheduled event found",
        })

        # V5.1 flagship score: business quality and technical timing remain visible,
        # but are combined into one decision-friendly ranking.
        results["Heartbeat Score"] = (
            results["Alpha Business Score"].fillna(0) * 0.35
            + results["Opportunity Score"].fillna(0) * 0.25
            + results["Accumulation Score"].fillna(0) * 0.20
            + results["Readiness Score"].fillna(0) * 0.15
            + results["Quality Score"].fillna(0) * 0.05
        ).clip(0, 100).round(1)
        results["Why Opportunity"] = results.apply(opportunity_explanation, axis=1)

        pullback_details = results.apply(pullback_classification, axis=1)
        results["Pullback Type"] = [x[0] for x in pullback_details]
        results["Pullback Why"] = [x[1] for x in pullback_details]

        results = results.sort_values(
            ["Heartbeat Score", "Alpha Business Score", "Accumulation Score"],
            ascending=[False, False, False],
            na_position="last",
        )
        st.session_state["results_v5_1"] = results
        st.session_state["heatmap_v5_1"] = build_heatmap(results)

if "results_v5_1" in st.session_state:
    results = st.session_state["results_v5_1"].copy()

    # Ensure business rankings are business-first, while technical timing stays separate.
    if "Alpha Business Score" not in results.columns:
        results["Alpha Business Score"] = 0.0
    if "Accumulation Score" not in results.columns:
        results["Accumulation Score"] = 0.0

    st.subheader("❤️ Best Opportunities")
    st.caption("V5.1's flagship view combines business quality, opportunity, accumulation, readiness, and technical quality. Use the component scores to see exactly why a stock ranks highly.")
    best = results.sort_values(
        ["Heartbeat Score", "Alpha Business Score", "Accumulation Score"],
        ascending=False,
        na_position="last",
    ).head(15)
    if best.empty:
        st.info("Run a scan to build the Best Opportunities dashboard.")
    else:
        leader = best.iloc[0]
        b1, b2, b3, b4 = st.columns(4)
        b1.metric("Best opportunity", leader["Ticker"])
        b2.metric("Heartbeat Score", f"{leader['Heartbeat Score']:.1f}")
        b3.metric("Business quality", f"{leader.get('Alpha Business Score', 0):.1f}")
        b4.metric("Accumulation", f"{leader.get('Accumulation Score', 0):.1f}")

        best_cols = [
            "Ticker", "Company", "Price", "Heartbeat Score", "Alpha Business Score",
            "Opportunity Score", "Accumulation Score", "Readiness Score",
            "Day Change %", "Distance to Breakout %", "Why Opportunity", "TradingView"
        ]
        best_cols = [c for c in best_cols if c in best.columns]
        st.dataframe(
            best[best_cols], use_container_width=True, hide_index=True,
            column_config={
                "Price": st.column_config.NumberColumn(format="$%.2f"),
                "Heartbeat Score": st.column_config.ProgressColumn(format="%.1f", min_value=0, max_value=100),
                "Alpha Business Score": st.column_config.ProgressColumn(format="%.1f", min_value=0, max_value=100),
                "Opportunity Score": st.column_config.ProgressColumn(format="%.1f", min_value=0, max_value=100),
                "Accumulation Score": st.column_config.ProgressColumn(format="%.1f", min_value=0, max_value=100),
                "Readiness Score": st.column_config.ProgressColumn(format="%.1f", min_value=0, max_value=100),
                "Day Change %": st.column_config.NumberColumn(format="%.2f%%"),
                "Distance to Breakout %": st.column_config.NumberColumn(format="%.2f%%"),
                "TradingView": st.column_config.LinkColumn("Chart", display_text="Open"),
            },
        )

    st.subheader("🏆 Alpha Business Rankings")
    st.caption("Ranks the strongest businesses first. Debt is graded by affordability and cash generation—not by the headline debt balance. Analyst targets are shown for context but do not drive the business score.")

    ranked = results.sort_values(
        ["Alpha Business Score", "Business Quality", "Future Growth", "Financial Strength"],
        ascending=False,
        na_position="last",
    ).head(20)

    if ranked["Alpha Business Score"].max() <= 0:
        st.warning("Fundamental data was not included. Turn on ‘Include fundamentals’ and run the scan again to build Alpha Business Rankings.")
    else:
        top = ranked.iloc[0]
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Top business", top["Ticker"])
        m2.metric("Alpha Business Score", f"{top['Alpha Business Score']:.1f}")
        m3.metric("Debt quality", str(top.get("Debt Quality", "N/A")))
        m4.metric("Accumulation", f"{top.get('Accumulation Score', 0):.1f}")

        business_cols = [
            "Ticker","Company","Alpha Business Score","Alpha Rating","Price","Debt Quality","Growth Investment",
            "Business Quality","Financial Strength","Capital Allocation","Future Growth","Competitive Advantage",
            "Valuation Score","Moat Score","Management Score","Revenue Growth %","FCF Margin %","Debt / EBITDA",
            "FCF Yield %","Accumulation Score","TradingView"
        ]
        business_cols = [c for c in business_cols if c in ranked.columns]
        st.dataframe(
            ranked[business_cols], use_container_width=True, hide_index=True,
            column_config={
                "Alpha Business Score": st.column_config.ProgressColumn(format="%.1f", min_value=0, max_value=100),
                "Business Quality": st.column_config.NumberColumn(format="%.1f / 25"),
                "Financial Strength": st.column_config.NumberColumn(format="%.1f / 20"),
                "Capital Allocation": st.column_config.NumberColumn(format="%.1f / 15"),
                "Future Growth": st.column_config.NumberColumn(format="%.1f / 20"),
                "Competitive Advantage": st.column_config.NumberColumn(format="%.1f / 10"),
                "Valuation Score": st.column_config.NumberColumn(format="%.1f / 10"),
                "Moat Score": st.column_config.ProgressColumn(format="%.1f", min_value=0, max_value=100),
                "Management Score": st.column_config.ProgressColumn(format="%.1f", min_value=0, max_value=100),
                "Accumulation Score": st.column_config.ProgressColumn(format="%.1f", min_value=0, max_value=100),
                "Price": st.column_config.NumberColumn(format="$%.2f"),
                "Revenue Growth %": st.column_config.NumberColumn(format="%.2f%%"),
                "FCF Margin %": st.column_config.NumberColumn(format="%.2f%%"),
                "Debt / EBITDA": st.column_config.NumberColumn(format="%.2fx"),
                "FCF Yield %": st.column_config.NumberColumn(format="%.2f%%"),
                "Growth Investment": st.column_config.CheckboxColumn("Growth investment"),
                "TradingView": st.column_config.LinkColumn("Chart", display_text="Open"),
            }
        )

        selected = st.selectbox("Open a company investment-committee view", ranked["Ticker"].tolist())
        detail = ranked[ranked["Ticker"] == selected].iloc[0]
        st.markdown(f"### {detail.get('Company', selected)} ({selected})")
        st.markdown(f"**{detail.get('Alpha Rating', '')} · Alpha Business Score: {detail.get('Alpha Business Score', 0):.1f}/100**")
        st.markdown(f"**Investment thesis:** {detail.get('Alpha Thesis', 'Not available')}")
        st.markdown(f"**Watch items:** {detail.get('Alpha Risks', 'Not available')}")
        st.markdown(f"**Debt assessment:** {detail.get('Debt Quality', 'N/A')} — Debt/EBITDA: {detail.get('Debt / EBITDA', np.nan):.2f}x | Cash/Debt: {detail.get('Cash / Debt', np.nan):.2f}x")

    st.subheader("🚦 Breakout Watch")
    breakout = results[results["Distance to Breakout %"].between(-5, 1, inclusive="both")].copy()
    breakout = breakout.sort_values(["Readiness Score","Intraday Volume Pace","Distance to Breakout %"], ascending=[False,False,False]).head(15)
    if breakout.empty:
        st.info("No scanned stocks are within 5% below to 1% above their breakout level.")
    else:
        st.dataframe(
            breakout[["Ticker","Price","Breakout Level","Distance to Breakout %","Intraday Volume Pace","Readiness Score","Alert Stage","Status","Why","TradingView"]],
            use_container_width=True, hide_index=True,
            column_config={
                "Price": st.column_config.NumberColumn(format="$%.2f"),
                "Breakout Level": st.column_config.NumberColumn(format="$%.2f"),
                "Distance to Breakout %": st.column_config.NumberColumn(format="%.2f%%"),
                "Intraday Volume Pace": st.column_config.NumberColumn(format="%.2fx"),
                "Readiness Score": st.column_config.ProgressColumn(format="%.1f", min_value=0, max_value=100),
                "TradingView": st.column_config.LinkColumn("Chart", display_text="Open"),
            }
        )

    st.subheader("🧲 Major Pullbacks")
    st.caption("Separates healthier pullbacks from emotional selloffs and broken trends. The ranking favors strong businesses rather than simply rewarding the largest decline.")
    pullbacks = results.copy()
    pullbacks["Pullback Rank"] = (
        pullbacks["Alpha Business Score"].fillna(0) * .45
        + pullbacks["Day Change %"].fillna(0).clip(upper=0).abs().clip(0, 12) / 12 * 25
        + pullbacks["Distance From 200D MA %"].fillna(0).clip(upper=0).abs().clip(0, 20) / 20 * 20
        + pullbacks["Accumulation Score"].fillna(0) * .10
    ).clip(0, 100).round(1)
    pullbacks = pullbacks[(pullbacks["Day Change %"] < 0) | (pullbacks["Distance From 200D MA %"].between(-10, 6))]
    pullbacks = pullbacks.sort_values(["Pullback Rank", "Alpha Business Score"], ascending=False).head(20)
    if pullbacks.empty:
        st.info("No qualifying pullbacks were found.")
    else:
        healthy_count = int(pullbacks["Pullback Type"].eq("🟢 Healthy pullback").sum())
        emotional_count = int(pullbacks["Pullback Type"].eq("🟡 Emotional selloff").sum())
        p1, p2, p3 = st.columns(3)
        p1.metric("Healthy pullbacks", healthy_count)
        p2.metric("Emotional selloffs", emotional_count)
        p3.metric("Top pullback", pullbacks.iloc[0]["Ticker"])
        st.dataframe(
            pullbacks[["Ticker","Price","Pullback Rank","Pullback Type","Day Change %","Distance From 200D MA %","RSI 14","Alpha Business Score","Accumulation Score","Pullback Why","TradingView"]],
            use_container_width=True, hide_index=True,
            column_config={
                "Price": st.column_config.NumberColumn(format="$%.2f"),
                "Pullback Rank": st.column_config.ProgressColumn(format="%.1f", min_value=0, max_value=100),
                "Day Change %": st.column_config.NumberColumn(format="%.2f%%"),
                "Distance From 200D MA %": st.column_config.NumberColumn(format="%.2f%%"),
                "RSI 14": st.column_config.NumberColumn(format="%.1f"),
                "Alpha Business Score": st.column_config.ProgressColumn(format="%.1f", min_value=0, max_value=100),
                "Accumulation Score": st.column_config.ProgressColumn(format="%.1f", min_value=0, max_value=100),
                "TradingView": st.column_config.LinkColumn("Chart", display_text="Open"),
            }
        )

    st.subheader("💎 Hidden Gems Under $20")
    hidden = results[results["Ticker"].isin(HIDDEN_GEM_TICKERS) & results["Price"].between(1,20,inclusive="both")].copy()
    hidden = hidden.sort_values(["Hidden Gem Score","Alpha Business Score","Accumulation Score"], ascending=False).head(20)
    if hidden.empty:
        st.info("No researched under-$20 candidates passed the current filters.")
    else:
        hidden["Why Hidden Gem"] = hidden.apply(opportunity_explanation, axis=1)
        hcols = ["Ticker","Hidden Gem Groups","Price","Hidden Gem Score","Alpha Business Score","Revenue Growth %","FCF Margin %","Debt Quality","Accumulation Score","Catalyst","Days to Earnings","Why Hidden Gem","TradingView"]
        hcols = [c for c in hcols if c in hidden.columns]
        st.dataframe(
            hidden[hcols], use_container_width=True, hide_index=True,
            column_config={
                "Price": st.column_config.NumberColumn(format="$%.2f"),
                "Hidden Gem Score": st.column_config.ProgressColumn(format="%.1f", min_value=0, max_value=100),
                "Alpha Business Score": st.column_config.ProgressColumn(format="%.1f", min_value=0, max_value=100),
                "Accumulation Score": st.column_config.ProgressColumn(format="%.1f", min_value=0, max_value=100),
                "Revenue Growth %": st.column_config.NumberColumn(format="%.2f%%"),
                "FCF Margin %": st.column_config.NumberColumn(format="%.2f%%"),
                "Days to Earnings": st.column_config.NumberColumn(format="%.0f"),
                "TradingView": st.column_config.LinkColumn("Chart", display_text="Open"),
            }
        )

    with st.expander("📋 Full research data", expanded=False):
        st.dataframe(results, use_container_width=True, hide_index=True)

    st.caption("Alpha Capital separates business quality from market timing. A high business score is not a guarantee of future returns, and a breakout or pullback is not automatically a buy signal.")
