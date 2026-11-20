"""Undervalued NBA Player Scout: a Streamlit dashboard.

Run with:  streamlit run app.py
"""

from __future__ import annotations

import math
from pathlib import Path

import pandas as pd
import streamlit as st

from nba_scout import charts, ui
from nba_scout.data import load_player_stats
from nba_scout.metrics import (
    NON_SCORING,
    PER_36,
    POS_ADJ,
    add_scouting_metrics,
    filter_players,
    limited_minutes,
    scoring_group,
)

DATA_PATH = Path(__file__).parent / "data" / "nba_stats.csv"
SEASON = "2024–25"
POSITIONS = ["PG", "SG", "SF", "PF", "C"]
DEFAULTS = {"min_games": 20, "max_points": 15, "min_contribution": 8,
            "positions": POSITIONS, "player_search": ""}

st.set_page_config(page_title="Undervalued NBA Player Scout",
                   page_icon="assets/favicon.png",
                   layout="wide")
ui.inject_css()


@st.cache_data
def load_data() -> pd.DataFrame:
    return add_scouting_metrics(load_player_stats(DATA_PATH))


def reset_filters() -> None:
    for key, value in DEFAULTS.items():
        st.session_state[key] = list(
            value) if isinstance(value, list) else value


df = load_data()

# ---------------------------------------------------------------- header
ui.hero(
    title="Undervalued NBA Player Scout",
    tagline="Discover the players making an impact beyond the scoreboard.",
    kicker=f"NBA analytics / player scouting / {SEASON}",
)

with st.expander("How does the scouting metric work?"):
    st.markdown(
        f"""
- **{NON_SCORING}**: rebounds + assists + steals + blocks per game.
- **{PER_36}**: the same total scaled to 36 minutes, so players with
  different playing time are comparable.
- **{POS_ADJ}**: the per-36 score divided by the average for the player's
  listed position (computed from players with at least 10 games and 10
  minutes per game). Above 1.00 means better than a typical player at that position.

This is an exploratory metric, not an official measure of value. It ignores
efficiency, turnovers, defense beyond steals and blocks, and teammate quality.
"""
    )

# --------------------------------------------------------------- sidebar
for key, value in DEFAULTS.items():
    st.session_state.setdefault(
        key, list(value) if isinstance(value, list) else value)

with st.sidebar:
    st.header("Refine your search")
    st.text_input("Search for a player",
                  placeholder="e.g. Alex Caruso", key="player_search")
    st.multiselect("Positions", POSITIONS, key="positions")
    st.slider("Minimum games played", 1, int(df["G"].max()), key="min_games")
    st.slider("Maximum points per game", 0, math.ceil(
        df["PTS"].max()), key="max_points")
    st.slider("Minimum non-scoring score", 0, math.ceil(df[NON_SCORING].max()),
              key="min_contribution",
              help="Rebounds + assists + steals + blocks per game.")
    st.button("Reset filters", on_click=reset_filters)
    st.caption("Filters apply to every tab. The Limited Minutes tab ignores the "
               "non-scoring minimum, since low-minute players rarely reach it.")

filters = {
    "min_games": st.session_state["min_games"],
    "max_points": st.session_state["max_points"],
    "positions": st.session_state["positions"],
    "name_query": st.session_state["player_search"],
}
filtered = filter_players(
    df, min_non_scoring=st.session_state["min_contribution"], **filters)

# ------------------------------------------------------------------ tabs
tab_discover, tab_position, tab_minutes, tab_chart, tab_compare = st.tabs(
    ["Undervalued players", "Position-adjusted", "Limited minutes",
     "Scoring vs. non-scoring", "Compare players"]
)

with tab_discover:
    st.subheader("Potential undervalued players")
    st.caption("Players who contribute through rebounds, assists, steals and blocks "
               "without leading the scoring column. Ranked by non-scoring score per 36 minutes.")
    if filtered.empty:
        ui.empty_state()
    else:
        ui.kpi_row(len(filtered),
                   filtered["PTS"].mean(), filtered[PER_36].max())
        st.write("")
        ui.leaderboard(filtered.sort_values(PER_36, ascending=False),
                       score_column=PER_36, show_position=True)
        st.download_button(
            "Download results (CSV)",
            data=filtered.sort_values(
                PER_36, ascending=False).to_csv(index=False),
            file_name="nba_scouting_results.csv",
            mime="text/csv",
        )

with tab_position:
    st.subheader("Top position-adjusted contributors")
    st.caption("Ranks players against the average at their own position, so a guard "
               "with big rebounding numbers is compared with other guards. "
               "1.00 is the positional average.")
    if filtered.empty:
        ui.empty_state()
    else:
        ui.leaderboard(filtered.sort_values(
            POS_ADJ, ascending=False), score_column=POS_ADJ)

with tab_minutes:
    st.subheader("Most productive in limited minutes")
    max_minutes = st.slider("Maximum minutes per game", 5, 48, 15)
    st.caption(f"Players averaging fewer than {max_minutes} minutes per game, ranked by "
               "position-adjusted score.")
    bench = limited_minutes(filter_players(df, **filters), max_minutes)
    if bench.empty:
        ui.empty_state(
            f"No players average under {max_minutes} minutes with these filters.")
    else:
        ui.leaderboard(bench, score_column=POS_ADJ)

with tab_chart:
    st.subheader("Scoring vs. non-scoring contributions")
    if filtered.empty:
        ui.empty_state()
    else:
        plot_df = filtered.assign(
            **{"Scoring Group": scoring_group(filtered["PTS"])})
        st.plotly_chart(charts.scoring_scatter(plot_df))
        st.caption("Higher on the chart means more rebounds, assists, steals and blocks "
                   "per 36 minutes. The eight highest players are labeled.")

with tab_compare:
    st.subheader("Player comparison")
    names = sorted(df["Player"])
    default_a = names.index(
        "Shai Gilgeous-Alexander") if "Shai Gilgeous-Alexander" in names else 0
    default_b = names.index(
        "Nikola Jokić") if "Nikola Jokić" in names else min(1, len(names) - 1)
    left, right = st.columns(2)
    first_name = left.selectbox("First player", names, index=default_a)
    second_name = right.selectbox("Second player", names, index=default_b)

    if first_name == second_name:
        st.warning("Choose two different players to compare.")
    else:
        first = df[df["Player"] == first_name].iloc[0]
        second = df[df["Player"] == second_name].iloc[0]
        stats = ["PTS", "TRB", "AST", "STL", "BLK", PER_36]
        table = pd.DataFrame({
            "Statistic": stats,
            first_name: [first[s] for s in stats],
            second_name: [second[s] for s in stats],
        })
        st.dataframe(
            table.style.format({first_name: "{:.1f}", second_name: "{:.1f}"})
            .highlight_max(subset=[first_name, second_name], axis=1, color="#14532D"),
            hide_index=True,
        )
        wins_first = sum(first[s] > second[s] for s in stats)
        wins_second = sum(second[s] > first[s] for s in stats)
        if wins_first == wins_second:
            st.info(
                f"{first_name} and {second_name} are tied across these categories.")
        else:
            leader = first_name if wins_first > wins_second else second_name
            st.success(f"{leader} leads in more statistical categories "
                       f"({max(wins_first, wins_second)} of {len(stats)}).")
        st.plotly_chart(charts.comparison_bars(first, second))

st.markdown(
    '<div class="app-footer">Data: <a href="https://www.basketball-reference.com/leagues/'
    f'NBA_2025_per_game.html">Basketball-Reference</a> (Sports Reference), {SEASON} per-game '
    "stats. Traded players are shown with their season totals.</div>",
    unsafe_allow_html=True,
)
