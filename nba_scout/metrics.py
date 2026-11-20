"""Scouting metrics and filters. Pure pandas, no Streamlit imports."""

from __future__ import annotations

from collections.abc import Sequence

import pandas as pd

NON_SCORING = "Non-Scoring Score"
PER_36 = "Non-Scoring Score Per 36"
POS_ADJ = "Position-Adjusted Score"

# Players below these thresholds are excluded when computing positional
# averages, so a handful of garbage-time minutes cannot distort the baseline.
BASELINE_MIN_GAMES = 10
BASELINE_MIN_MPG = 10.0

SCORING_GROUPS = ["Under 10 PPG", "10–19.9 PPG", "20+ PPG"]


def add_scouting_metrics(
    df: pd.DataFrame,
    baseline_min_games: int = BASELINE_MIN_GAMES,
    baseline_min_mpg: float = BASELINE_MIN_MPG,
) -> pd.DataFrame:
    """Add the three scouting columns.

    * Non-Scoring Score: rebounds + assists + steals + blocks per game
    * Non-Scoring Score Per 36: the same, scaled to 36 minutes
    * Position-Adjusted Score: per-36 score divided by the average per-36
      score of qualified players at the same listed position
    """
    out = df.copy()
    out[NON_SCORING] = out[["TRB", "AST", "STL", "BLK"]].sum(axis=1)

    minutes = out["MP"].where(out["MP"] > 0)
    out[PER_36] = out[NON_SCORING] / minutes * 36

    qualified = (out["G"] >= baseline_min_games) & (out["MP"] >= baseline_min_mpg)
    baseline = out.loc[qualified].groupby("Pos")[PER_36].mean()
    out[POS_ADJ] = out[PER_36] / out["Pos"].map(baseline)
    return out


def filter_players(
    df: pd.DataFrame,
    *,
    min_games: int = 1,
    max_points: float | None = None,
    min_non_scoring: float = 0,
    positions: Sequence[str] | None = None,
    name_query: str = "",
) -> pd.DataFrame:
    """Apply the sidebar filters. Every argument is optional."""
    mask = df["G"] >= min_games
    if max_points is not None:
        mask &= df["PTS"] <= max_points
    mask &= df[NON_SCORING] >= min_non_scoring
    if positions:
        mask &= df["Pos"].isin(positions)
    if name_query.strip():
        mask &= df["Player"].str.contains(name_query.strip(), case=False, regex=False, na=False)
    return df[mask]


def limited_minutes(df: pd.DataFrame, max_minutes: float) -> pd.DataFrame:
    """Players averaging fewer than ``max_minutes`` per game, best first."""
    return df[df["MP"] < max_minutes].sort_values(POS_ADJ, ascending=False)


def scoring_group(points: pd.Series) -> pd.Series:
    """Bucket points per game into the three scoring levels."""
    return pd.cut(
        points,
        bins=[-float("inf"), 10, 20, float("inf")],
        labels=SCORING_GROUPS,
        right=False,
    )
