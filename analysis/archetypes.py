import pandas as pd


def classify_archetype(row) -> str:
    """
    SEASON IDENTITY archetype.

    Uses ONLY season-level metrics.
    Stable, non-windowed, non-reactive.

    Required fields:
      - season_win_rate
      - season_avg_pve
      - season_consistency
    """

    wr = row.get("season_win_rate")
    c = row.get("season_consistency")
    pve = row.get("season_avg_pve")

    if pd.isna(wr) or pd.isna(c):
        return "Forming"

    # --------------------------------------------------
    # CLEAR SEASON CONTENDERS
    # --------------------------------------------------
    if wr >= 0.60:
        if c >= 0.60:
            return "Methodical Contender"
        return "Streak-Driven Contender"

    # --------------------------------------------------
    # CLEAR SEASON LOSERS
    # --------------------------------------------------
    if wr <= 0.40:
        if c >= 0.60:
            return "Consistently Bad"
        return "Struggling Team"

    # --------------------------------------------------
    # MIDDLE TIER (0.40–0.60)
    # --------------------------------------------------
    if c >= 0.60:
        return "Known Quantity"

    if not pd.isna(pve) and abs(pve) >= 3.0:
        return "High-Ceiling Team"

    return "Unstable Middle"
