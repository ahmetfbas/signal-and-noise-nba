import pandas as pd


# --------------------------------------------------
# Direction label (orthogonal, descriptive only)
# --------------------------------------------------

def direction_label(row) -> str:
    cw = row.get("consistency_win")
    cl = row.get("consistency_loss")
    wr = row.get("win_rate_window")

    if pd.isna(wr):
        return "Forming"

    # Clear outcome dominance
    if wr >= 0.65:
        return "Convincing Wins"
    if wr <= 0.35:
        return "Heavy Losses"

    # Middle-tier shape
    if not pd.isna(cl) and cl >= 0.70:
        return "Resilient Losses"

    return "Mixed Results"


# --------------------------------------------------
# Archetype classification (FINAL)
# --------------------------------------------------

def classify_archetype(row) -> str:
    """
    FINAL archetype logic.

    Outcome truth:
      - win_rate_window (HARD veto layer)

    Style / identity:
      - consistency
      - avg_pve_window

    Guarantees:
      - No team with wr < 0.50 can be called a Winner
      - No team with wr > 0.50 can be called Bad
      - PvE never overrides win/loss reality
    """

    wr = row.get("win_rate_window")
    c = row.get("consistency")
    pve = row.get("avg_pve_window")

    if pd.isna(wr) or pd.isna(c):
        return "Forming"

    # --------------------------------------------------
    # CLEAR WINNERS
    # --------------------------------------------------
    if wr >= 0.65:
        if c >= 0.60:
            return "Methodical Contender"
        return "Streaky Winner"

    # --------------------------------------------------
    # CLEAR LOSERS
    # --------------------------------------------------
    if wr <= 0.35:
        if c >= 0.60:
            return "Consistently Bad"
        return "Volatile Struggler"

    # --------------------------------------------------
    # MIDDLE TIER (0.35 < wr < 0.65)
    # --------------------------------------------------
    # These teams are NOT winners or losers by results

    if c >= 0.60:
        return "Known Quantity"

    # Style-driven volatility
    if not pd.isna(pve) and abs(pve) >= 2.5:
        return "High-Ceiling Team"

    return "High-Variance Team"
