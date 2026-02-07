import pandas as pd


def consistency_band(c: float) -> str:
    if pd.isna(c):
        return "Insufficient"
    if c >= 0.65:
        return "High"
    if c >= 0.50:
        return "Medium"
    return "Low"


def pve_band(p: float) -> str:
    if pd.isna(p):
        return "Insufficient"
    if p >= 3.0:
        return "Strong"
    if p >= 1.0:
        return "Positive"
    if p > -1.0:
        return "Neutral"
    if p > -3.0:
        return "Weak"
    return "Very Weak"


def direction_label(row) -> str:
    """
    Orthogonal label: describes outcome shape, not identity.
    """
    pve = row.get("avg_pve_window")
    cw = row.get("consistency_win")
    cl = row.get("consistency_loss")

    if pd.isna(pve) or pd.isna(cw) or pd.isna(cl):
        return "Forming"

    if cw >= 0.60 and pve > 0:
        return "Convincing Wins"
    if cl >= 0.60 and pve < 0:
        return "Resilient Losses"
    return "Mixed Results"


def classify_archetype(row) -> str:
    """
    Archetypes use ONLY:
    - avg_pve_window (quality)
    - consistency / win / loss (stability)
    No RPMI. No fatigue. No single-game effects.
    """
    pve = row.get("avg_pve_window")
    c = row.get("consistency")
    cw = row.get("consistency_win")
    cl = row.get("consistency_loss")

    # Insufficient history
    if pd.isna(pve) or pd.isna(c):
        return "Forming"

    # Methodical Contender: good + stable + stable wins
    if pve >= 2.5 and c >= 0.60 and (not pd.isna(cw) and cw >= 0.60):
        return "Methodical Contender"

    # High-Ceiling: good but volatile
    if pve >= 2.5 and c < 0.55:
        return "High-Ceiling Team"

    # Fragile Winner: positive but wins are not stable
    if pve >= 1.0 and c >= 0.60 and (not pd.isna(cw) and cw < 0.55):
        return "Fragile Winner"

    # Dangerous Underdog: slightly negative but controlled losses
    if pve < 0 and pve >= -2.5 and (not pd.isna(cl) and cl >= 0.60):
        return "Dangerous Underdog"

    # Chaotic Team: very low consistency, mid quality
    if c < 0.45 and abs(pve) < 2.5:
        return "Chaotic Team"

    # Consistently Bad: bad + stable
    if pve <= -2.5 and c >= 0.60:
        return "Consistently Bad"

    return "Inconsistent Profile"
