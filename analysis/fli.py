# analysis/fli.py

# --------------------------------------------------
# Density scoring
# --------------------------------------------------

def density_7d_score(g7: int) -> int:
    if g7 <= 2:
        return 10
    if g7 == 3:
        return 40
    if g7 == 4:
        return 75
    return 95


def density_14d_score(g14: int) -> int:
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
    if days_since_last_game == 1:
        return 0.00
    if days_since_last_game == 2:
        return 0.10
    if days_since_last_game == 3:
        return 0.22
    if days_since_last_game == 4:
        return 0.35
    return 0.50


def travel_load(travel_miles):
    """
    Travel penalty scale.
    None = no travel history (season opener / unknown).
    """
    if travel_miles is None:
        return 0
    if travel_miles < 300:
        return 1
    if travel_miles < 800:
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

    b2b = 1 if days_since_last_game == 1 else 0

    TRAVEL_WEIGHT = 4
    B2B_BONUS = 8
    COMBO_BONUS = 6

    raw = (
        density_score
        + (B2B_BONUS if b2b else 0)
        + travel_load_score * TRAVEL_WEIGHT
        + (COMBO_BONUS if b2b and travel_load_score >= 2 else 0)
    )

    return round(raw * (1 - recovery_offset(days_since_last_game)), 1)


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
    return round(
        0.65 * density_7d_score(games_last_7)
        + 0.35 * density_14d_score(games_last_14),
        1
    )


def fatigue_components_from_row(
    games_last_7: int,
    games_last_14: int,
    days_since_last_game: int,
    travel_miles
) -> dict:
    """
    Stateless fatigue computation.
    Recovery is already applied inside fatigue_index.
    """

    density = compute_density_score(games_last_7, games_last_14)
    travel = travel_load(travel_miles)
    fatigue = fatigue_index(density, days_since_last_game, travel)

    return {
        "games_last_7": games_last_7,
        "games_last_14": games_last_14,
        "density_score": density,
        "days_since_last_game": days_since_last_game,
        "travel_miles": travel_miles,
        "travel_load": travel,
        "fatigue_index": fatigue,
        "fatigue_tier": fatigue_tier(fatigue),
    }
