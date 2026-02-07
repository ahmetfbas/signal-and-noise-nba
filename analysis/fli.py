# analysis/fli.py
from __future__ import annotations

import math
from typing import Any, Dict, Optional


# --------------------------------------------------
# Internal helpers
# --------------------------------------------------

def _is_missing(x: Any) -> bool:
    return x is None or (isinstance(x, float) and math.isnan(x))


def _clamp_int(x: Any, low: int = 0, high: Optional[int] = None) -> int:
    try:
        v = int(x)
    except Exception:
        v = 0
    if v < low:
        v = low
    if high is not None and v > high:
        v = high
    return v


# --------------------------------------------------
# Density scoring
# --------------------------------------------------

def density_7d_score(g7: int) -> int:
    g7 = _clamp_int(g7, low=0)
    if g7 <= 2:
        return 10
    if g7 == 3:
        return 40
    if g7 == 4:
        return 75
    return 95


def density_14d_score(g14: int) -> int:
    g14 = _clamp_int(g14, low=0)
    if g14 <= 4:
        return 10
    if g14 == 5:
        return 35
    if g14 == 6:
        return 55
    if g14 == 7:
        return 75
    return 95


# --------------------------------------------------
# Recovery & travel
# --------------------------------------------------

def recovery_offset(days_since_last_game: int) -> float:
    """
    Models recovery benefit after rest days.
    Applied ONLY inside fatigue_index.
    """
    d = _clamp_int(days_since_last_game, low=1, high=14)

    if d == 1:
        return 0.00
    if d == 2:
        return 0.10
    if d == 3:
        return 0.22
    if d == 4:
        return 0.35
    return 0.50


def travel_load(travel_miles: Any) -> int:
    """
    Travel penalty scale.
    Missing/unknown travel -> 0
    """
    if _is_missing(travel_miles):
        return 0

    try:
        miles = float(travel_miles)
    except Exception:
        return 0

    if miles < 0:
        miles = 0.0

    if miles < 300:
        return 1
    if miles < 800:
        return 2
    return 3


# --------------------------------------------------
# Core fatigue calculation
# --------------------------------------------------

def fatigue_index(
    density_score: float,
    days_since_last_game: int,
    travel_load_score: int
) -> float:
    """
    Combines schedule density, travel, and rest recovery
    into a unified fatigue index.
    """

    d = _clamp_int(days_since_last_game, low=1, high=14)
    tl = _clamp_int(travel_load_score, low=0, high=3)
    b2b = 1 if d == 1 else 0

    TRAVEL_WEIGHT = 4
    B2B_BONUS = 8
    COMBO_BONUS = 6

    raw = (
        float(density_score)
        + (B2B_BONUS if b2b else 0)
        + tl * TRAVEL_WEIGHT
        + (COMBO_BONUS if b2b and tl >= 2 else 0)
    )

    score = raw * (1 - recovery_offset(d))
    if score < 0:
        score = 0.0

    # Optional hard cap for stability
    if score > 100:
        score = 100.0

    return round(score, 1)


def fatigue_tier(score: float) -> str:
    if score < 30:
        return "Low"
    if score < 50:
        return "Elevated"
    if score < 70:
        return "High"
    return "Critical"


# --------------------------------------------------
# Public helpers (row-based)
# --------------------------------------------------

def compute_density_score(games_last_7: int, games_last_14: int) -> float:
    g7 = _clamp_int(games_last_7, low=0)
    g14 = _clamp_int(games_last_14, low=0)

    # enforce consistency
    if g14 < g7:
        g14 = g7

    return round(
        0.65 * density_7d_score(g7)
        + 0.35 * density_14d_score(g14),
        1
    )


def fatigue_components_from_row(
    games_last_7: int,
    games_last_14: int,
    days_since_last_game: int,
    travel_miles: Any
) -> Dict[str, Any]:
    """
    Stateless fatigue computation.
    Recovery is already applied inside fatigue_index.
    """

    g7 = _clamp_int(games_last_7, low=0)
    g14 = _clamp_int(games_last_14, low=0)
    if g14 < g7:
        g14 = g7

    d = _clamp_int(days_since_last_game, low=1, high=14)

    density = compute_density_score(g7, g14)
    tl = travel_load(travel_miles)
    fatigue = fatigue_index(density, d, tl)

    return {
        "games_last_7": g7,
        "games_last_14": g14,
        "density_score": density,
        "days_since_last_game": d,
        "travel_miles": None if _is_missing(travel_miles) else float(travel_miles),
        "travel_load": tl,
        "fatigue_index": fatigue,
        "fatigue_tier": fatigue_tier(fatigue),
    }
