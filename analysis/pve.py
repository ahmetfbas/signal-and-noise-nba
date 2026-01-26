import pandas as pd
from typing import Dict

from scripts.utils.utils import (
    clamp,
)


# --------------------------------------------------
# Core helpers (row-based)
# --------------------------------------------------

def expected_margin_breakdown_from_rows(
    *,
    team_id: int,
    opponent_id: int,
    is_home: bool,
    recent_games: pd.DataFrame,
    fatigue_index: float,
) -> Dict[str, float]:
    """
    Row-based expected margin calculation.
    Assumes recent_games already contains only past games.
    """

    # -----------------------------
    # Base form (adjusted margins)
    # -----------------------------
    team_rows = recent_games[
        (recent_games["team_id"] == team_id)
    ]

    opp_rows = recent_games[
        (recent_games["team_id"] == opponent_id)
    ]

    team_form = team_rows["actual_margin"].mean() if not team_rows.empty else 0.0
    opp_form = opp_rows["actual_margin"].mean() if not opp_rows.empty else 0.0

    base_form_diff = team_form - opp_form

    # -----------------------------
    # Home / Away adjustment
    # -----------------------------
    HOME_ADVANTAGE = 2.0
    home_away_adj = HOME_ADVANTAGE if is_home else -HOME_ADVANTAGE

    # -----------------------------
    # Fatigue adjustment
    # -----------------------------
    FATIGUE_WEIGHT = 6.0
    fatigue_norm = min(fatigue_index / 100.0, 1.0)
    fatigue_adj = -fatigue_norm * FATIGUE_WEIGHT

    expected_total = base_form_diff + home_away_adj + fatigue_adj

    return {
        "base_form_diff": round(base_form_diff, 2),
        "home_away_adj": round(home_away_adj, 2),
        "fatigue_adj": round(fatigue_adj, 2),
        "expected_total": round(expected_total, 2),
    }
