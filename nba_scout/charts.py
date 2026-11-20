"""Plotly figures styled for the app's dark theme."""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go

from .metrics import PER_36, SCORING_GROUPS

TEXT = "#F3F7F4"
MUTED = "#A1ADA5"
GRID = "#26352C"

# Categorical slots 1-3, validated for all-pairs separation on a dark surface.
GROUP_COLORS = dict(zip(SCORING_GROUPS, ["#3987e5", "#d95926", "#199e70"]))
PLAYER_COLORS = ["#3987e5", "#d95926"]


def _style(fig: go.Figure, height: int = 520) -> go.Figure:
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font={"color": MUTED, "size": 13},
        height=height,
        margin={"l": 10, "r": 10, "t": 30, "b": 10},
        legend={"orientation": "h", "y": 1.08, "x": 0, "title": {"text": ""}},
        hoverlabel={"bgcolor": "#151C19", "bordercolor": GRID, "font": {"color": TEXT}},
    )
    fig.update_xaxes(gridcolor=GRID, zerolinecolor=GRID)
    fig.update_yaxes(gridcolor=GRID, zerolinecolor=GRID)
    return fig


def scoring_scatter(df: pd.DataFrame, label_top: int = 8) -> go.Figure:
    """Points per game vs. non-scoring production per 36 minutes."""
    fig = go.Figure()
    for group in SCORING_GROUPS:
        subset = df[df["Scoring Group"] == group]
        fig.add_trace(
            go.Scatter(
                x=subset["PTS"],
                y=subset[PER_36],
                mode="markers",
                name=group,
                marker={
                    "size": 10,
                    "color": GROUP_COLORS[group],
                    "line": {"width": 1.5, "color": "#0B100E"},
                },
                customdata=subset[["Player", "Team", "Pos", "G", "MP"]],
                hovertemplate=(
                    "<b>%{customdata[0]}</b> · %{customdata[1]} · %{customdata[2]}<br>"
                    "%{x:.1f} PPG · %{y:.1f} non-scoring / 36<br>"
                    "%{customdata[3]} games · %{customdata[4]:.1f} MPG<extra></extra>"
                ),
            )
        )

    top = df.nlargest(label_top, PER_36)
    fig.add_trace(
        go.Scatter(
            x=top["PTS"],
            y=top[PER_36],
            mode="text",
            text=top["Player"],
            textposition="top center",
            textfont={"size": 11, "color": TEXT},
            showlegend=False,
            hoverinfo="skip",
        )
    )

    if not df.empty:
        fig.add_vline(
            x=df["PTS"].mean(),
            line_dash="dash",
            line_color=MUTED,
            annotation_text="Average points",
            annotation_font_color=MUTED,
            annotation_position="bottom right",
        )

    fig.update_xaxes(title="Points per game")
    fig.update_yaxes(title="Non-scoring score per 36 minutes")
    return _style(fig)


def comparison_bars(first: pd.Series, second: pd.Series) -> go.Figure:
    """Grouped bars of the four non-scoring categories for two players."""
    categories = ["TRB", "AST", "STL", "BLK"]
    labels = ["Rebounds", "Assists", "Steals", "Blocks"]
    fig = go.Figure()
    for player, color in zip((first, second), PLAYER_COLORS):
        fig.add_trace(
            go.Bar(
                x=labels,
                y=[player[c] for c in categories],
                name=player["Player"],
                marker={"color": color},
                hovertemplate="%{x}: %{y:.1f} per game<extra>" + player["Player"] + "</extra>",
            )
        )
    fig.update_layout(barmode="group", bargap=0.35, bargroupgap=0.08)
    fig.update_yaxes(title="Per game")
    return _style(fig, height=380)
