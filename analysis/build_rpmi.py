import pandas as pd
import numpy as np
import os

# --------------------------------------------------
# Configuration
# --------------------------------------------------

SHORT_WINDOW = 3   # short-term momentum (hot streaks)
LONG_WINDOW = 7    # longer-term form

INPUT_CSV = "data/derived/team_game_metrics_with_pve.csv"
OUTPUT_CSV = "data/derived/team_game_metrics_with_rpmi.csv"


# --------------------------------------------------
# Core helpers
# --------------------------------------------------

def momentum_contribution(actual_margin: float, pve: float) -> float:
    """
    Convert a single game into a momentum contribution.

    Rules:
    - Wins matter more than losses (psychological effect)
    - PvE modifies magnitude, not direction
    - Loss + positive PvE is heavily compressed
    - Blowout wins vs weak teams already limited via PvE
    """

    # Exclude draws entirely (should already be filtered, but safe)
    if actual_margin == 0 or pd.isna(actual_margin) or pd.isna(pve):
        return np.nan

    win = actual_margin > 0

    if win:
        # Wins always positive
        # PvE amplifies, but softly
        return 1.0 + np.tanh(pve / 10.0)

    else:
        # Losses always negative
        if pve > 0:
            # "Good loss" → very small credit, close to zero
            return -0.3 + np.tanh(pve / 20.0)
        else:
            # Bad loss → full penalty
            return -1.0 + np.tanh(pve / 10.0)


def weighted_mean(values: np.ndarray) -> float:
    """Recency-weighted mean (linear ramp)."""
    n = len(values)
    weights = np.arange(1, n + 1)
    return float(np.dot(values, weights) / weights.sum())


def compute_window_rpmi(g: pd.DataFrame, window: int) -> pd.Series:
    """Compute RPMI over a rolling window."""
    out = [np.nan] * len(g)

    for i in range(window - 1, len(g)):
        window_vals = g.loc[i - window + 1 : i, "momentum_unit"].dropna().values
        if len(window_vals) < window:
            continue

        out[i] = round(weighted_mean(window_vals), 2)

    return pd.Series(out, index=g.index)


# --------------------------------------------------
# Main computation
# --------------------------------------------------

def compute_rpmi(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["game_date"] = pd.to_datetime(df["game_date"], errors="coerce")
    df = df.sort_values(["team_id", "game_date"])

    # --------------------------------------------------
    # Exclusions
    # --------------------------------------------------
    df = df[df["actual_margin"] != 0]

    # --------------------------------------------------
    # Per-game momentum unit
    # --------------------------------------------------
    df["momentum_unit"] = df.apply(
        lambda r: momentum_contribution(r["actual_margin"], r["pve"]),
        axis=1,
    )

    df["rpmi_short"] = np.nan
    df["rpmi_long"] = np.nan
    df["rpmi_accel"] = np.nan
    df["rpmi_delta"] = np.nan

    # --------------------------------------------------
    # Rolling windows per team
    # --------------------------------------------------
    for team_id, g in df.groupby("team_id"):
        g = g.reset_index()

        rpmi_s = compute_window_rpmi(g, SHORT_WINDOW)
        rpmi_l = compute_window_rpmi(g, LONG_WINDOW)

        df.loc[g["index"], "rpmi_short"] = rpmi_s
        df.loc[g["index"], "rpmi_long"] = rpmi_l
        df.loc[g["index"], "rpmi_accel"] = rpmi_s - rpmi_l

        # Game-to-game momentum change (short window)
        for i in range(1, len(g)):
            prev = rpmi_s.iloc[i - 1]
            curr = rpmi_s.iloc[i]
            if not pd.isna(prev) and not pd.isna(curr):
                df.loc[g.loc[i, "index"], "rpmi_delta"] = round(curr - prev, 2)

    return df


# --------------------------------------------------
# Entrypoint
# --------------------------------------------------

def main():
    if not os.path.exists(INPUT_CSV):
        raise FileNotFoundError("PvE output missing — RPMI cannot run.")

    df = pd.read_csv(INPUT_CSV)
    if df.empty:
        raise RuntimeError("RPMI input is empty — PvE must run successfully first.")

    out = compute_rpmi(df)
    out.to_csv(OUTPUT_CSV, index=False)

    print(
        f"✅ Built dual-window RPMI → {OUTPUT_CSV}\n"
        f"   rpmi_short = {SHORT_WINDOW}-game window\n"
        f"   rpmi_long  = {LONG_WINDOW}-game window\n"
        f"   rpmi_accel = rpmi_short - rpmi_long\n"
        f"   logic: win-first, PvE-modulated, no volatility penalty"
    )


if __name__ == "__main__":
    main()
