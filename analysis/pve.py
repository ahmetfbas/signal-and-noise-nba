from datetime import timedelta, date
from typing import List, Dict

from scripts.ingest.data_provider import fetch_games_range
from scripts.utils.utils import (
    game_date,
    is_completed,
    margin_for_team,
    expected_margin_for_team,
)
from analysis.fli import fatigue_index_for_team


# --------------------------------------------------
# Helpers
# --------------------------------------------------

def pick_games_for_date(run_date: date) -> List[Dict]:
    """
    Fetch and return completed games for a specific date.
    """
    games = fetch_games_range(
        run_date.isoformat(),
        run_date.isoformat()
    )

    return [
        g for g in games
        if game_date(g) == run_date and is_completed(g)
    ]


# --------------------------------------------------
# PvE computation (pure, stateless)
# --------------------------------------------------

def compute_pve_for_game(
    game: Dict,
    run_date: date,
    recent_games: List[Dict],
    games_14: List[Dict],
    games_today: List[Dict],
) -> List[Dict]:
    """
    Compute Performance vs Expectation (PvE) for both teams in a game.
    Returns one row per team.
    """

    results = []

    for side in ["home_team", "visitor_team"]:
        team = game[side]
        team_id = team["id"]

        actual_margin = margin_for_team(game, team_id)

        fatigue_index = fatigue_index_for_team(
            team_id=team_id,
            run_date=run_date,
            games_14=games_14,
            games_today=games_today,
        )

        expected_margin = expected_margin_for_team(
            game=game,
            team_id=team_id,
            games=recent_games,
            fatigue_index=fatigue_index,
        )

        results.append({
            "game_id": game["id"],
            "game_date": run_date,
            "team_id": team_id,
            "team_name": team["full_name"],
            "actual_margin": round(actual_margin, 2),
            "expected_margin": round(expected_margin, 2),
            "pve": round(actual_margin - expected_margin, 2),
            "fatigue_index": fatigue_index,
        })

    return results
