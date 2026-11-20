"""Load and clean a Basketball-Reference per-game export."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

STAT_COLUMNS = [
    "Age", "G", "GS", "MP", "FG", "FGA", "3P", "3PA", "2P", "2PA",
    "FT", "FTA", "ORB", "DRB", "TRB", "AST", "STL", "BLK", "TOV", "PF", "PTS",
]


def _find_header_row(path: Path) -> int:
    """Return the line index of the real CSV header.

    Basketball-Reference exports start with a citation blurb and blank lines,
    so the header is the first line that begins with ``Rk,``.
    """
    with open(path, encoding="utf-8") as handle:
        for index, line in enumerate(handle):
            if line.startswith("Rk,"):
                return index
    raise ValueError(f"No 'Rk,' header row found in {path}")


def _label_team(team: str) -> str:
    """Turn Basketball-Reference's '2TM' / '3TM' into readable text."""
    if isinstance(team, str) and team.endswith("TM") and team[:-2].isdigit():
        return f"{team[:-2]} teams"
    return team


def load_player_stats(path: str | Path) -> pd.DataFrame:
    """Read the export and return exactly one row per player.

    Cleaning steps:
      * skip the citation blurb above the header and the footer below the data
      * drop the "League Average" row (it has no rank)
      * keep one row per player. Traded players have a season-total row
        followed by one row per team, so the first row for each rank is kept
      * coerce stat columns to numbers
    """
    path = Path(path)
    raw = pd.read_csv(path, skiprows=_find_header_row(path))

    raw["Rk"] = pd.to_numeric(raw["Rk"], errors="coerce")
    players = raw.dropna(subset=["Rk", "Player"]).copy()
    players = players.drop_duplicates(subset="Rk", keep="first")

    for column in STAT_COLUMNS:
        players[column] = pd.to_numeric(players[column], errors="coerce")

    players["Team"] = players["Team"].map(_label_team)
    return players.reset_index(drop=True)
