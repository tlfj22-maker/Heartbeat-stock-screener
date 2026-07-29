from __future__ import annotations

from pathlib import Path
import shutil
import sys


HELPERS = r'''
def add_pullback_explanations(df: pd.DataFrame, mode: str) -> pd.DataFrame:
    """Add plain-English explanations without changing the underlying scan."""
    out = df.copy()

    def explain(row: pd.Series) -> str:
        reasons: list[str] = []
        business = float(row.get("Alpha Business Score", 0) or 0)
        accumulation = float(row.get("Accumulation Score", 0) or 0)
        rsi = row.get("RSI 14", np.nan)
        day_change = row.get("Day Change %", np.nan)
        distance_200 = row.get("Distance From 200D MA %", np.nan)
        slope_200 = row.get("200D MA Slope %", np.nan)

        if business >= 85:
            reasons.append("elite business")
        elif business >= 75:
            reasons.append("strong business")

        if accumulation >= 75:
            reasons.append("strong accumulation")
        elif accumulation >= 60:
            reasons.append("positive accumulation")

        if mode == "daily":
            if pd.notna(day_change):
                if day_change <= -8:
                    reasons.append("very large daily selloff")
                elif day_change <= -4:
                    reasons.append("sharp daily selloff")
                elif day_change < 0:
                    reasons.append("down today")
        else:
            if pd.notna(distance_200):
                if -5 <= distance_200 <= 3:
                    reasons.append("near 200D support")
                elif distance_200 < -5:
                    reasons.append("below 200D average")
                elif 3 < distance_200 <= 8:
                    reasons.append("pulling back toward support")
            if pd.notna(slope_200) and slope_200 > 0:
                reasons.append("rising 200D trend")

        if pd.notna(rsi):
            if rsi <= 35:
                reasons.append("oversold RSI")
            elif rsi <= 45:
                reasons.append("cooling RSI")

        return ", ".join(reasons[:4]) if reasons else "developing pullback setup"

    out["Why"] = out.apply(explain, axis=1)
    return out


def add_hidden_gem_explanations(df: pd.DataFrame) -> pd.DataFrame:
    """Explain why each under-$20 candidate may be overlooked."""
    out = df.copy()

    def explain(row: pd.Series) -> str:
        reasons: list[str] = []
        market_cap = row.get("Market Cap", np.nan)
        revenue_growth = row.get("Revenue Growth %", np.nan)
        fcf = row.get("Free Cash Flow", np.nan)
        days = row.get("Days to Earnings", np.nan)
        accumulation = row.get("Accumulation Score", np.nan)
        short_float = row.get("Short Float %", np.nan)

        if pd.notna(market_cap):
            if market_cap < 2_000_000_000:
                reasons.append("small-cap")
            elif market_cap < 10_000_000_000:
                reasons.append("mid-cap")

        if pd.notna(revenue_growth) and revenue_growth >= 20:
            reasons.append("rapid growth")
        elif pd.notna(revenue_growth) and revenue_growth > 0:
            reasons.append("positive growth")

        if pd.notna(fcf) and fcf > 0:
            reasons.append("positive free cash flow")

        if pd.notna(accumulation) and accumulation >= 70:
            reasons.append("institutional accumulation")

        if pd.notna(days) and 3 <= days <= 45:
            reasons.append("near earnings catalyst")

        if pd.notna(short_float) and short_float >= 10:
            reasons.append("high short interest")

        return ", ".join(reasons[:4]) if reasons else "under-$20 overlooked candidate"

    out["Why Hidden"] = out.apply(explain, axis=1)
    return out
'''


NEW_UI = r'''
if "results_v5" in st.session_state:
    results = st.session_state["results_v5"].copy()

    if "Alpha Business Score" not in results.columns:
        results["Alpha Business Score"] = 0.0
    if "Accumulation Score" not in results.columns:
        results["Accumulation Score"] = 0.0

    st.subheader("🏆 Alpha Business Rankings")
    st.caption(
        "Strongest businesses first. Technical timing is shown separately so a great "
        "company is not confused with a stock that merely moved today."
    )

    ranked = results.sort_values(
        ["Alpha Business Score", "Business Quality", "Future Growth", "Financial Strength"],
        ascending=False,
        na_position="last",
    ).head(20)

    if ranked["Alpha Business Score"].max() <= 0:
        st.warning(
            "Fundamental data was not included. Turn on ‘Include fundamentals’ and run "
            "the scan again to build Alpha Business Rankings."
        )
    else:
        top = ranked.iloc[0]
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Top business", top["Ticker"])
        m2.metric("Alpha Business Score", f"{top['Alpha Business Score']:.1f}")
        m3.metric("Debt quality", str(top.get("Debt Quality", "N/A")))
        m4.metric("Accumulation", f"{top.get('Accumulation Score', 0):.1f}")

        business_cols = [
            "Ticker","Company","Alpha Business Score","Alpha Rating","Price","Debt Quality",
            "Growth Investment","Business Quality","Financial Strength","Capital Allocation",
            "Future Growth","Competitive Advantage","Valuation Score","Moat Score",
            "Management Score","Revenue Growth %","FCF Margin %","Debt / EBITDA",
            "FCF Yield %","Accumulation Score","TradingView"
        ]
        business_cols = [c for c in business_cols if c in ranked.columns]

        st.dataframe(
            ranked[business_cols],
            use_container_width=True,
            hide_index=True,
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
            },
        )

        selected = st.selectbox("Open a company investment-committee view", ranked["Ticker"].tolist())
        detail = ranked[ranked["Ticker"] == selected].iloc[0]
        debt_ebitda = detail.get("Debt / EBITDA", np.nan)
        cash_debt = detail.get("Cash / Debt", np.nan)
        debt_ebitda_text = f"{debt_ebitda:.2f}x" if pd.notna(debt_ebitda) else "N/A"
        cash_debt_text = f"{cash_debt:.2f}x" if pd.notna(cash_debt) else "N/A"

        st.markdown(f"### {detail.get('Company', selected)} ({selected})")
        st.markdown(f"**{detail.get('Alpha Rating', '')} · Alpha Business Score: {detail.get('Alpha Business Score', 0):.1f}/100**")
        st.markdown(f"**Investment thesis:** {detail.get('Alpha Thesis', 'Not available')}")
        st.markdown(f"**Watch items:** {detail.get('Alpha Risks', 'Not available')}")
        st.markdown(
            f"**Debt assessment:** {detail.get('Debt Quality', 'N/A')} — "
            f"Debt/EBITDA: {debt_ebitda_text} | Cash/Debt: {cash_debt_text}"
        )

    st.subheader("🚦 Breakout Watch")
    st.caption(
        "Stocks within 5% below to 1% above resistance, ranked by readiness, "
        "volume confirmation, and breakout proximity."
    )

    breakout = results[results["Distance to Breakout %"].between(-5, 1, inclusive="both")].copy()
    breakout = breakout.sort_values(
        ["Readiness Score", "Intraday Volume Pace", "Distance to Breakout %"],
        ascending=[False, False, False],
    ).head(15)

    if breakout.empty:
        st.info("No scanned stocks are within 5% below to 1% above their breakout level.")
    else:
        breakout_cols = [
            "Ticker","Price","Breakout Level","Distance to Breakout %",
            "Intraday Volume Pace","Readiness Score","Alert Stage","Status","Why","TradingView"
        ]
        breakout_cols = [c for c in breakout_cols if c in breakout.columns]
        st.dataframe(
            breakout[breakout_cols],
            use_container_width=True,
            hide_index=True,
            column_config={
                "Price": st.column_config.NumberColumn(format="$%.2f"),
                "Breakout Level": st.column_config.NumberColumn(format="$%.2f"),
                "Distance to Breakout %": st.column_config.NumberColumn(format="%.2f%%"),
                "Intraday Volume Pace": st.column_config.NumberColumn(format="%.2fx"),
                "Readiness Score": st.column_config.ProgressColumn(format="%.1f", min_value=0, max_value=100),
                "TradingView": st.column_config.LinkColumn("Chart", display_text="Open"),
            },
        )

    st.subheader("🧲 Major Pullbacks")
    st.caption(
        "Separated into two logical views: sudden daily selloffs and deeper technical "
        "pullbacks. Business quality remains the largest ranking factor."
    )

    daily_tab, technical_tab = st.tabs(["🔻 Major Daily Selloffs", "🧲 Technical Pullbacks"])

    with daily_tab:
        daily = results[results["Day Change %"] < 0].copy()
        daily["Selloff Score"] = daily["Day Change %"].abs().clip(0, 15) / 15 * 100
        daily["RSI Discount Score"] = (55 - daily["RSI 14"].fillna(55)).clip(0, 30) / 30 * 100
        daily["Daily Pullback Rank"] = (
            daily["Alpha Business Score"].fillna(0) * 0.45
            + daily["Accumulation Score"].fillna(0) * 0.15
            + daily["Selloff Score"] * 0.25
            + daily["RSI Discount Score"] * 0.15
        ).round(1)

        daily = add_pullback_explanations(daily, "daily")
        daily = daily.sort_values(
            ["Daily Pullback Rank", "Alpha Business Score", "Day Change %"],
            ascending=[False, False, True],
        ).head(15)

        if daily.empty:
            st.info("No declining stocks were found in this scan.")
        else:
            daily_cols = [
                "Ticker","Price","Day Change %","Daily Pullback Rank","RSI 14",
                "Alpha Business Score","Accumulation Score","Why","Debt Quality","TradingView"
            ]
            daily_cols = [c for c in daily_cols if c in daily.columns]
            st.dataframe(
                daily[daily_cols],
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Price": st.column_config.NumberColumn(format="$%.2f"),
                    "Day Change %": st.column_config.NumberColumn(format="%.2f%%"),
                    "Daily Pullback Rank": st.column_config.ProgressColumn("Pullback Rank", format="%.1f", min_value=0, max_value=100),
                    "RSI 14": st.column_config.NumberColumn(format="%.1f"),
                    "Alpha Business Score": st.column_config.ProgressColumn(format="%.1f", min_value=0, max_value=100),
                    "Accumulation Score": st.column_config.ProgressColumn(format="%.1f", min_value=0, max_value=100),
                    "TradingView": st.column_config.LinkColumn("Chart", display_text="Open"),
                },
            )

    with technical_tab:
        technical = results[
            results["Distance From 200D MA %"].between(-15, 8, inclusive="both")
        ].copy()
        technical["200D Support Score"] = (
            100 - technical["Distance From 200D MA %"].abs().clip(0, 15) / 15 * 100
        )
        technical["RSI Discount Score"] = (
            (55 - technical["RSI 14"].fillna(55)).clip(0, 30) / 30 * 100
        )
        technical["Trend Health Score"] = np.select(
            [
                technical["200D MA Slope %"].fillna(-99) >= 2,
                technical["200D MA Slope %"].fillna(-99) > 0,
                technical["200D MA Slope %"].fillna(-99) >= -2,
            ],
            [100, 75, 40],
            default=10,
        )
        technical["Technical Pullback Rank"] = (
            technical["Alpha Business Score"].fillna(0) * 0.45
            + technical["Accumulation Score"].fillna(0) * 0.15
            + technical["200D Support Score"] * 0.20
            + technical["RSI Discount Score"] * 0.10
            + technical["Trend Health Score"] * 0.10
        ).round(1)

        technical = add_pullback_explanations(technical, "technical")
        technical = technical.sort_values(
            ["Technical Pullback Rank", "Alpha Business Score"],
            ascending=[False, False],
        ).head(15)

        if technical.empty:
            st.info("No stocks are currently near the selected 200-day pullback zone.")
        else:
            technical_cols = [
                "Ticker","Price","Distance From 200D MA %","Technical Pullback Rank",
                "200D MA Slope %","RSI 14","Alpha Business Score","Accumulation Score",
                "Why","Debt Quality","TradingView"
            ]
            technical_cols = [c for c in technical_cols if c in technical.columns]
            st.dataframe(
                technical[technical_cols],
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Price": st.column_config.NumberColumn(format="$%.2f"),
                    "Distance From 200D MA %": st.column_config.NumberColumn(format="%.2f%%"),
                    "Technical Pullback Rank": st.column_config.ProgressColumn("Pullback Rank", format="%.1f", min_value=0, max_value=100),
                    "200D MA Slope %": st.column_config.NumberColumn(format="%.2f%%"),
                    "RSI 14": st.column_config.NumberColumn(format="%.1f"),
                    "Alpha Business Score": st.column_config.ProgressColumn(format="%.1f", min_value=0, max_value=100),
                    "Accumulation Score": st.column_config.ProgressColumn(format="%.1f", min_value=0, max_value=100),
                    "TradingView": st.column_config.LinkColumn("Chart", display_text="Open"),
                },
            )

    st.subheader("💎 Hidden Gems Under $20")
    st.caption(
        "Under-$20 candidates ranked by business evidence, accumulation, growth, "
        "cash flow, valuation context, and nearby catalysts."
    )

    hidden = results[
        results["Ticker"].isin(HIDDEN_GEM_TICKERS)
        & results["Price"].between(1, 20, inclusive="both")
    ].copy()
    hidden = add_hidden_gem_explanations(hidden)
    hidden = hidden.sort_values(
        ["Hidden Gem Score", "Alpha Business Score", "Accumulation Score"],
        ascending=False,
    ).head(20)

    if hidden.empty:
        st.info("No researched under-$20 candidates passed the current filters.")
    else:
        hcols = [
            "Ticker","Hidden Gem Groups","Price","Hidden Gem Score","Alpha Business Score",
            "Revenue Growth %","FCF Margin %","Debt Quality","Accumulation Score",
            "Why Hidden","Catalyst","Days to Earnings","TradingView"
        ]
        hcols = [c for c in hcols if c in hidden.columns]
        st.dataframe(
            hidden[hcols],
            use_container_width=True,
            hide_index=True,
            column_config={
                "Price": st.column_config.NumberColumn(format="$%.2f"),
                "Hidden Gem Score": st.column_config.ProgressColumn(format="%.1f", min_value=0, max_value=100),
                "Alpha Business Score": st.column_config.ProgressColumn(format="%.1f", min_value=0, max_value=100),
                "Accumulation Score": st.column_config.ProgressColumn(format="%.1f", min_value=0, max_value=100),
                "Revenue Growth %": st.column_config.NumberColumn(format="%.2f%%"),
                "FCF Margin %": st.column_config.NumberColumn(format="%.2f%%"),
                "Days to Earnings": st.column_config.NumberColumn(format="%.0f"),
                "TradingView": st.column_config.LinkColumn("Chart", display_text="Open"),
            },
        )

    with st.expander("📋 Full research data", expanded=False):
        st.dataframe(results, use_container_width=True, hide_index=True)

    st.caption(
        "Alpha Capital separates business quality from market timing. Rankings are "
        "research tools—not guarantees or automatic buy signals."
    )
'''


def main() -> None:
    source = Path(sys.argv[1] if len(sys.argv) > 1 else "app.py")
    if not source.exists():
        raise SystemExit(
            f"Could not find {source}. Put this file beside app.py, or run:\n"
            f"python {Path(__file__).name} path/to/app.py"
        )

    text = source.read_text(encoding="utf-8")
    ui_marker = 'if "results_v5" in st.session_state:'
    helper_marker = "def build_heatmap(results: pd.DataFrame) -> pd.DataFrame:"

    if ui_marker not in text:
        raise SystemExit("Could not find the V5 results display section.")
    if helper_marker not in text:
        raise SystemExit("Could not find build_heatmap().")

    if "def add_pullback_explanations(" not in text:
        text = text.replace(helper_marker, HELPERS.strip() + "\n\n\n" + helper_marker, 1)

    text = text[:text.index(ui_marker)] + NEW_UI.strip() + "\n"
    text = text.replace("<h1>📈 Alpha Capital V5</h1>", "<h1>📈 Alpha Capital V5.1</h1>", 1)
    text = text.replace("🔍 Run Alpha Capital V5 scan", "🔍 Run Alpha Capital V5.1 scan", 1)

    backup = source.with_suffix(source.suffix + ".v5_backup")
    output = source.with_name("heartbeat_app_v5_1.py")

    shutil.copy2(source, backup)
    output.write_text(text, encoding="utf-8")
    compile(text, str(output), "exec")

    print(f"Created: {output}")
    print(f"Backup:  {backup}")
    print("Rename heartbeat_app_v5_1.py to app.py, or point Streamlit to it.")


if __name__ == "__main__":
    main()
