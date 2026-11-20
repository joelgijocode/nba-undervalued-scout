from pathlib import Path

import pytest

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

CSV = Path(__file__).parent.parent / "data" / "nba_stats.csv"


@pytest.fixture(scope="module")
def players():
    return add_scouting_metrics(load_player_stats(CSV))


def test_one_row_per_player(players):
    assert players["Player"].is_unique
    assert "League Average" not in set(players["Player"])


def test_traded_player_uses_season_total(players):
    luka = players[players["Player"] == "Luka Dončić"].iloc[0]
    assert luka["Team"] == "2 teams"
    assert luka["G"] == 50


def test_per_36_formula(players):
    sga = players[players["Player"] == "Shai Gilgeous-Alexander"].iloc[0]
    assert sga[NON_SCORING] == pytest.approx(5.0 + 6.4 + 1.7 + 1.0)
    assert sga[PER_36] == pytest.approx(14.1 / 34.2 * 36)


def test_position_baseline_averages_one(players):
    qualified = players[(players["G"] >= 10) & (players["MP"] >= 10)]
    means = qualified.groupby("Pos")[POS_ADJ].mean()
    assert means.round(6).eq(1.0).all()


def test_filters_combine(players):
    result = filter_players(
        players, min_games=20, max_points=15, min_non_scoring=8, positions=["C"]
    )
    assert not result.empty
    assert (result["G"] >= 20).all() and (result["PTS"] <= 15).all()
    assert (result["Pos"] == "C").all()


def test_name_search_is_literal(players):
    assert len(filter_players(players, name_query="caruso")) == 1
    assert filter_players(players, name_query="(").empty  # no regex errors


def test_limited_minutes_cutoff(players):
    result = limited_minutes(players[players["G"] >= 20], 15)
    assert (result["MP"] < 15).all()


def test_scoring_groups(players):
    groups = scoring_group(players["PTS"].dropna())
    assert groups.notna().all()
    assert str(scoring_group(players["PTS"].iloc[:1]).iloc[0]) == "20+ PPG"
