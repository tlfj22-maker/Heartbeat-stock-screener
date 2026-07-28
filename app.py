
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

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
      <h1>📈 Troy's Heartbeat Stock Screener</h1>
      <p>Find large-cap stocks forming a tight base above a rising 150-day moving average, then breaking out on unusually heavy volume.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

AI_TICKERS = [
    "NVDA","AVGO","TSM","MU","ANET","ORCL","VRT","ETN","PWR","CEG","KLAC","MRVL",
    "CRDO","CLS","GEV","AMAT","LRCX","COHR","LITE","APH","MOD","FIX","PLTR","ARM"
]
FINANCE_TICKERS = [
    "JPM","BAC","WFC","C","GS","MS","SCHW","BLK","AXP","V","MA","SPGI","CME","ICE","CB"
]
ENERGY_TICKERS = [
    "XOM","CVX","COP","EOG","OXY","SLB","MPC","VLO","KMI","WMB","OKE","PSX","HAL"
]
INDUSTRIAL_TICKERS = [
    "CAT","DE","HON","GE","RTX","LMT","NOC","LHX","EMR","ROK","PH","URI","FAST","GWW"
]
HEALTHCARE_TICKERS = [
    "LLY","UNH","JNJ","ABBV","MRK","AMGN","TMO","DHR","ISRG","BSX","SYK","VRTX"
]
CONSUMER_TICKERS = [
    "AMZN","WMT","COST","HD","LOW","MCD","SBUX","NKE","BKNG","TJX","PG","KO","PEP"
]

UNIVERSES = {
    "AI infrastructure": AI_TICKERS,
    "Financials": FINANCE_TICKERS,
    "Energy & oil": ENERGY_TICKERS,
    "Industrials & defense": INDUSTRIAL_TICKERS,
    "Healthcare": HEALTHCARE_TICKERS,
    "Consumer": CONSUMER_TICKERS,
    "All built-in sectors": sorted(set(
        AI_TICKERS + FINANCE_TICKERS + ENERGY_TICKERS +
        INDUSTRIAL_TICKERS + HEALTHCARE_TICKERS + CONSUMER_TICKERS
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
        df = df.dropna(subset=["Close", "Volume"])
        return df
    except Exception:
        return pd.DataFrame()

def technical_row(ticker: str, df: pd.DataFrame, spy: pd.DataFrame, p: Params) -> Optional[dict]:
    if len(df) < p.ma_days + 35:
        return None

    c = df["Close"].astype(float)
    v = df["Volume"].astype(float)
    ma = c.rolling(p.ma_days).mean()
    av = v.rolling(p.avg_volume_days).mean()
    adv = (c * v).rolling(p.avg_volume_days).mean()

    price = float(c.iloc[-1])
    ma_now = float(ma.iloc[-1])
    av_now = float(av.iloc[-1])
    dollar_vol = float(adv.iloc[-1])

    if np.isnan(ma_now) or np.isnan(av_now) or price < p.min_price or dollar_vol < p.min_avg_dollar_volume:
        return None

    slope_days = 30
    ma_then = float(ma.iloc[-1 - slope_days])
    slope = ma_now / ma_then - 1 if ma_then else np.nan
    distance = price / ma_now - 1 if ma_now else np.nan

    base = c.iloc[-p.base_days:]
    base_low, base_high = float(base.min()), float(base.max())
    base_range = base_high / base_low - 1 if base_low else np.nan

    prior = c.iloc[-(p.breakout_days + 1):-1]
    prior_high = float(prior.max())
    breakout_pct = price / prior_high - 1 if prior_high else np.nan
    breakout = price >= prior_high
    distance_to_breakout = (price / prior_high - 1) * 100 if prior_high else np.nan

    volume_ratio = float(v.iloc[-1]) / av_now if av_now else np.nan

    rs = np.nan
    if not spy.empty:
        sc = spy["Close"].astype(float)
        common = c.index.intersection(sc.index)
        if len(common) > 64:
            rs = (c.loc[common].pct_change(63).iloc[-1] - sc.loc[common].pct_change(63).iloc[-1]) * 100

    tech = 0
    tech += 15 if price > ma_now else 0
    tech += 15 if slope > .02 else 10 if slope > 0 else 3
    tech += 8 if 0 <= distance <= p.max_extension else 4 if price > ma_now else 0
    tech += 12 if base_range <= p.max_base_range else 7 if base_range <= p.max_base_range * 1.5 else 0
    tech += 10 if breakout else 6 if breakout_pct >= -.03 else 0
    tech += 10 if volume_ratio >= p.min_volume_ratio else 6 if volume_ratio >= 1.5 else 2 if volume_ratio >= 1 else 0

    heartbeat = (
        price > ma_now and slope > 0 and distance <= p.max_extension and
        base_range <= p.max_base_range and breakout and volume_ratio >= p.min_volume_ratio
    )
    almost = (
        not heartbeat and price > ma_now and slope >= 0 and
        base_range <= p.max_base_range * 1.35 and breakout_pct >= -.03 and volume_ratio >= 1.2
    )

    setup = "Tier 1 — Heartbeat" if heartbeat else "Tier 2 — Almost there" if almost else "Tier 3 — Watch"

    if heartbeat:
        status = "Confirmed breakout"
    elif price > ma_now and slope >= 0 and breakout_pct >= -.02 and volume_ratio >= 1.2:
        status = "Breakout close — volume building"
    elif price > ma_now and slope >= 0 and breakout_pct >= -.03:
        status = "Near breakout — needs volume"
    elif price > ma_now and slope >= 0:
        status = "Healthy trend — still forming"
    else:
        status = "Not ready"

    reasons = []
    if price > ma_now:
        reasons.append("above 150D MA")
    if slope > 0:
        reasons.append("rising trend")
    if base_range <= p.max_base_range:
        reasons.append("tight base")
    if breakout_pct >= -.03:
        reasons.append("within 3% of breakout")
    if volume_ratio >= p.min_volume_ratio:
        reasons.append(f"volume {volume_ratio:.2f}x")
    elif volume_ratio >= 1.0:
        reasons.append("volume improving")
    reason = ", ".join(reasons[:4]) if reasons else "setup still developing"

    alert_ready = bool(
        price > ma_now and slope >= 0 and base_range <= p.max_base_range * 1.35 and
        breakout_pct >= -.02 and volume_ratio >= p.min_volume_ratio
    )

    return {
        "Ticker": ticker,
        "Setup": setup,
        "Score": round(tech, 1),
        "Price": price,
        "Breakout Level": prior_high,
        "Distance to Breakout %": distance_to_breakout,
        "Volume Ratio": volume_ratio,
        "Status": status,
        "Why": reason,
        "Alert Ready": alert_ready,
        "TradingView": f"https://www.tradingview.com/chart/?symbol={ticker}",
        "MA Slope %": slope * 100,
        "Distance From 150D MA %": distance * 100,
        "Base Range %": base_range * 100,
        "Breakout %": breakout_pct * 100,
        "RS vs SPY 3M %": rs,
        "Avg Dollar Volume": dollar_vol,
    }

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
            "Fundamental Score": score,
        }
    except Exception:
        return {"Fundamental Score": 0}

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
        placeholder="NVDA, AVGO, MU, JPM, XOM",
    )
    include_fund = st.checkbox("Include fundamentals and analyst data", value=True)

params = Params(
    min_volume_ratio=volume_ratio,
    base_days=base_days,
    max_base_range=max_base,
    breakout_days=breakout_days,
    min_avg_dollar_volume=min_dollar_vol * 1_000_000,
)

tickers = [clean_ticker(t) for t in custom.split(",") if t.strip()] if custom.strip() else UNIVERSES[universe_name]

if st.button("🔍 Run heartbeat scan", type="primary", use_container_width=True):
    with st.spinner(f"Scanning {len(tickers)} stocks…"):
        spy_raw = download_prices(("SPY",))
        spy = frame_for(spy_raw, "SPY", 1)
        raw = download_prices(tuple(tickers))

        rows = []
        bar = st.progress(0)
        for i, ticker in enumerate(tickers):
            df = frame_for(raw, ticker, len(tickers))
            row = technical_row(ticker, df, spy, params)
            if row:
                if include_fund:
                    f = fundamentals(ticker)
                    row.update(f)
                    row["Score"] = round(row["Score"] + f.get("Fundamental Score", 0), 1)
                rows.append(row)
            bar.progress((i + 1) / len(tickers))
        bar.empty()

    results = pd.DataFrame(rows)
    if results.empty:
        st.warning("No usable results were returned. Try another universe or loosen the filters.")
    else:
        results = results.sort_values(
            ["Setup", "Score"],
            ascending=[True, False]
        )
        st.session_state["results"] = results

if "results" in st.session_state:
    results = st.session_state["results"]

    t1 = int((results["Setup"] == "Tier 1 — Heartbeat").sum())
    t2 = int((results["Setup"] == "Tier 2 — Almost there").sum())
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Tier 1 matches", t1)
    m2.metric("Tier 2 candidates", t2)
    m3.metric("Stocks ranked", len(results))
    m4.metric("Best score", f"{results['Score'].max():.1f}")

    filter_setups = st.multiselect(
        "Show",
        ["Tier 1 — Heartbeat", "Tier 2 — Almost there", "Tier 3 — Watch"],
        default=["Tier 1 — Heartbeat", "Tier 2 — Almost there", "Tier 3 — Watch"],
    )
    shown = results[results["Setup"].isin(filter_setups)].copy()

    if shown.empty:
        st.info("Nothing is currently in the selected tiers.")
    else:
        preferred = [
            "Ticker","Setup","Score","Status","Why","Price","Breakout Level","Distance to Breakout %","Volume Ratio","Alert Ready","TradingView","MA Slope %",
            "Distance From 150D MA %","Base Range %","Breakout %","RS vs SPY 3M %",
            "Revenue Growth %","EPS Growth %","FCF Margin %","Gross Margin %",
            "Institutional Ownership %","Insider Ownership %","Forward P/E",
            "Analyst Target Upside %","Market Cap"
        ]
        cols = [c for c in preferred if c in shown.columns]
        display = shown[cols].copy()

        if "Market Cap" in display.columns:
            display["Market Cap"] = display["Market Cap"].apply(
                lambda x: f"${x/1e9:.1f}B" if pd.notna(x) else ""
            )

        st.dataframe(
            display,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Price": st.column_config.NumberColumn(format="$%.2f"),
                "Volume Ratio": st.column_config.NumberColumn(format="%.2fx"),
                "Breakout Level": st.column_config.NumberColumn(format="$%.2f"),
                "Distance to Breakout %": st.column_config.NumberColumn(format="%.2f%%"),
                "Score": st.column_config.ProgressColumn(min_value=0, max_value=100, format="%.1f"),
                "Alert Ready": st.column_config.CheckboxColumn(),
                "TradingView": st.column_config.LinkColumn("Chart", display_text="Open"),
            },
        )

        st.download_button(
            "⬇️ Download results",
            shown.to_csv(index=False).encode("utf-8"),
            "heartbeat_results.csv",
            "text/csv",
            use_container_width=True,
        )

        st.subheader("Chart inspection")
        chosen = st.selectbox("Choose a stock", shown["Ticker"].tolist())
        chart_raw = download_prices((chosen,), period="1y")
        chart_df = frame_for(chart_raw, chosen, 1)

        if not chart_df.empty:
            price_chart = pd.DataFrame({
                chosen: chart_df["Close"],
                "150-day moving average": chart_df["Close"].rolling(150).mean(),
            })
            st.line_chart(price_chart, height=320)

            vol_chart = pd.DataFrame({
                "Daily volume": chart_df["Volume"],
                "50-day average": chart_df["Volume"].rolling(50).mean(),
            }).tail(120)
            st.bar_chart(vol_chart, height=260)

st.markdown(
    """
    <div class="note">
      <b>Important:</b> This is a research tool, not a guarantee that a stock will rise.
      Volume spikes can come from earnings, index rebalancing, news, or short covering.
      Always inspect the chart and upcoming earnings date before acting.
    </div>
    """,
    unsafe_allow_html=True,
)
