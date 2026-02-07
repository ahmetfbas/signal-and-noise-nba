import pandas as pd
import math
from typing import Dict
from analysis.utils import clamp


def bounded_sigmoid(x: float, max_margin: float = 12.0) -> float:
    """
    Smoothly bounds expected margin to [-max_margin, +max_margin]
    using tanh to avoid hard cliffs.
    """
    return max_margin * math.tanh(x / max_margin)


def expected_margin_breakdown_from_rows(
    *,
    team_id: int,
    opponent_id: int,
    is_home: bool,
    recent_games: pd.DataFrame,
    fatigue_index: float,
) -> Dict[str, float]:
    """
    Row-based expected margin calculation (defensive & bounded).

    Rules enforced:
    - Ignore zero-margin games (broken ingestion / placeholders)
    - Ignore today & future games
    - Bound expectations smoothly (sigmoid)
    """

    # --------------------------------------------------
    # Defensive filtering (CRITICAL)
    # --------------------------------------------------
    today = pd.Timestamp.utcnow().normalize()

    recent_games = recent_games.copy()
    recent_games["game_date"] = pd.to_datetime(
        recent_games["game_date"],
        utc=True,
        errors="coerce"
    )

    recent_games = recent_games[
        (recent_games["game_date"].notna()) &
        (recent_games["game_date"] < today) &
        (recent_games["actual_margin"].notna()) &
        (recent_games["actual_margin"] != 0)
    ]

    # --------------------------------------------------
    # Base form (average margin)
    # --------------------------------------------------
    team_rows = recent_games[recent_games["team_id"] == team_id]
    opp_rows = recent_games[recent_games["team_id"] == opponent_id]

    team_form = team_rows["actual_margin"].mean() if not team_rows.empty else 0.0
    opp_form = opp_rows["actual_margin"].mean() if not opp_rows.empty else 0.0
    base_form_diff = team_form - opp_form

    # --------------------------------------------------
    # Win–loss component (bounded psychological signal)
    # --------------------------------------------------
    def win_rate(rows: pd.DataFrame) -> float:
        if rows.empty:
            return 0.5
        wins = (rows["actual_margin"] > 0).sum()
        total = len(rows)
        return wins / total if total > 0 else 0.5

    team_win_rate = win_rate(team_rows)
    opp_win_rate = win_rate(opp_rows)

    # bounded influence: ±6 points
    win_diff = (team_win_rate - opp_win_rate) * 6.0

    # --------------------------------------------------
    # Home / Away adjustment
    # --------------------------------------------------
    HOME_ADVANTAGE = 4.5
    home_away_adj = HOME_ADVANTAGE if is_home else -HOME_ADVANTAGE

    # --------------------------------------------------
    # Fatigue adjustment
    # --------------------------------------------------
    FATIGUE_WEIGHT = 3.0
    fatigue_norm = clamp(fatigue_index / 100.0, 0.0, 1.0)
    fatigue_adj = -fatigue_norm * FATIGUE_WEIGHT

    # --------------------------------------------------
    # Linear expectation (pre-bounding)
    # --------------------------------------------------
    expected_raw = (
        base_form_diff
        + win_diff
        + home_away_adj
        + fatigue_adj
    )

    # --------------------------------------------------
    # SOFT BOUND (sigmoid)
    # --------------------------------------------------
    expected_total = bounded_sigmoid(expected_raw, max_margin=12.0)

    return {
        "base_form_diff": round(base_form_diff, 2),
        "win_diff": round(win_diff, 2),
        "home_away_adj": round(home_away_adj, 2),
        "fatigue_adj": round(fatigue_adj, 2),
        "expected_raw": round(expected_raw, 2),
        "expected_total": round(expected_total, 2),
    }
