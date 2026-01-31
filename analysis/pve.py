import pandas as pd
from typing import Dict
from analysis.utils import clamp


def expected_margin_breakdown_from_rows(
    *,
    team_id: int,
    opponent_id: int,
    is_home: bool,
    recent_games: pd.DataFrame,
    fatigue_index: float,
) -> Dict[str, float]:
    """
    Row-based expected margin calculation with win–loss component.
    Uses calibrated weights based on correlation testing:
      - Home advantage ≈ 4.5 points
      - Fatigue penalty ≈ 3 points (was 6)
    Assumes recent_games already contains only past games (no future leakage).
    """

    # -----------------------------
    # Base form (average margins)
    # -----------------------------
    team_rows = recent_games[recent_games["team_id"] == team_id]
    opp_rows = recent_games[recent_games["team_id"] == opponent_id]

    team_form = team_rows["actual_margin"].mean() if not team_rows.empty else 0.0
    opp_form = opp_rows["actual_margin"].mean() if not opp_rows.empty else 0.0
    base_form_diff = team_form - opp_form

    # -----------------------------
    # Win–Loss component
    # -----------------------------
    def win_rate(rows: pd.DataFrame) -> float:
        if rows.empty:
            return 0.5
        wins = (rows["actual_margin"] > 0).sum()
        total = len(rows)
        return wins / total if total > 0 else 0.5

    team_win_rate = win_rate(team_rows)
    opp_win_rate = win_rate(opp_rows)
    win_diff = (team_win_rate - opp_win_rate) * 6.0  # ±6 pts full range

    # -----------------------------
    # Home / Away adjustment
    # -----------------------------
    HOME_ADVANTAGE = 4.5  # increased from 2.0 based on sensitivity test
    home_away_adj = HOME_ADVANTAGE if is_home else -HOME_ADVANTAGE

    # -----------------------------
    # Fatigue adjustment
    # -----------------------------
    FATIGUE_WEIGHT = 3.0  # reduced from 6.0 for better calibration
    fatigue_norm = clamp(fatigue_index / 100.0, 0.0, 1.0)
    fatigue_adj = -fatigue_norm * FATIGUE_WEIGHT

    # -----------------------------
    # Combine into total expectation
    # -----------------------------
    expected_total = base_form_diff + win_diff + home_away_adj + fatigue_adj

    return {
        "base_form_diff": round(base_form_diff, 2),
        "win_diff": round(win_diff, 2),
        "home_away_adj": round(home_away_adj, 2),
        "fatigue_adj": round(fatigue_adj, 2),
        "expected_total": round(expected_total, 2),
    }
