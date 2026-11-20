"""Reusable Streamlit components."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st

from .metrics import NON_SCORING, PER_36, POS_ADJ

CSS_PATH = Path(__file__).parent.parent / "assets" / "style.css"


def inject_css() -> None:
    st.markdown(f"<style>{CSS_PATH.read_text(encoding='utf-8')}</style>", unsafe_allow_html=True)


def hero(title: str, tagline: str, kicker: str) -> None:
    st.markdown(
        f"""
        <div class="hero">
            <div class="hero-kicker">{kicker}</div>
            <h1>{title}</h1>
            <p>{tagline}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def kpi_row(count: int, avg_points: float | None, best_score: float | None) -> None:
    """Three headline numbers above the leaderboard."""
    cols = st.columns(3)
    cols[0].metric("Players found", f"{count}")
    cols[1].metric("Average points", "–" if avg_points is None else f"{avg_points:.1f}")
    cols[2].metric("Best score / 36", "–" if best_score is None else f"{best_score:.1f}")


def leaderboard(df: pd.DataFrame, *, score_column: str, show_position: bool = True) -> None:
    """Render a ranked table with in-cell bars for the key score."""
    columns = ["Player", "Team"] + (["Pos"] if show_position else []) + [
        "G", "MP", "PTS", "TRB", "AST", "STL", "BLK", NON_SCORING, PER_36,
    ]
    if score_column == POS_ADJ:
        columns.append(POS_ADJ)

    one_decimal = st.column_config.NumberColumn(format="%.1f")
    config = {
        "Player": st.column_config.TextColumn(pinned=True),
        "G": st.column_config.NumberColumn("Games", format="%d"),
        "MP": st.column_config.NumberColumn("Min", format="%.1f"),
        "PTS": st.column_config.NumberColumn("Pts", format="%.1f"),
        "TRB": st.column_config.NumberColumn("Reb", format="%.1f"),
        "AST": st.column_config.NumberColumn("Ast", format="%.1f"),
        "STL": st.column_config.NumberColumn("Stl", format="%.1f"),
        "BLK": st.column_config.NumberColumn("Blk", format="%.1f"),
        NON_SCORING: one_decimal,
        PER_36: one_decimal,
        POS_ADJ: one_decimal,
    }
    if score_column in columns and not df.empty:
        config[score_column] = st.column_config.ProgressColumn(
            score_column,
            format="%.2f" if score_column == POS_ADJ else "%.1f",
            min_value=0.0,
            max_value=float(df[score_column].max()),
        )

    st.dataframe(
        df[columns],
        hide_index=True,
        column_config=config,
        height=min(640, 38 * (len(df) + 1) + 3),
    )


def empty_state(message: str = "No players match these filters. Try loosening them.") -> None:
    st.info(message, icon="🔍")
