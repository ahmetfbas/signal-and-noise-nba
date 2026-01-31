import pandas as pd
import numpy as np

# --------------------------------------------------
# Configuration
# --------------------------------------------------

SHORT_WINDOW = 3   # best correlation, detects hot streaks
LONG_WINDOW = 7    # smoother, represents overall form

INPUT_CSV = "data/derived/team_game_metrics_with_pve.csv"
OUTPUT_CSV = "data/derived/team_game_metrics_with_rpmi.csv"


# --------------------------------------------------
# Core helpers
# --------------------------------------------------

def weighted_pve(values: np.ndarray) -> float:
    """Weighted mean of PvE using linear ramp weights (1..N)."""
    n = len(values)
    weights = np.arange(1, n + 1)
    return np.dot(values, weights) / weights.sum()


def consistency_factor(values: np.ndarray) -> float:
    """Penalize volatility — higher std → smaller multiplier."""
    std = np.std(values, ddof=0)
    return 1 / (1 + std / 10)


def compute_window_rpmi(g: pd.DataFrame, window: int) -> pd.Series:
    """Compute RPMI for a given rolling window."""
    rpmi_vals = [np.nan] * len(g)
    for i in range(window - 1, len(g)):
        window_vals = g.loc[i - window + 1 : i, "pve"].dropna().values
        if len(window_vals) < window:
            continue
        w_pve = weighted_pve(window_vals)
        cons = consistency_factor(window_vals)
        rpmi_vals[i] = round(w_pve * cons, 2)
    return pd.Series(rpmi_vals, index=g.index)


# --------------------------------------------------
# Main computation
# --------------------------------------------------

def compute_rpmi(df: pd.DataFrame) -> pd.DataFrame:
    """Compute short- and long-term RPMI with acceleration delta."""
    df = df.copy()
    df["game_date"] = pd.to_datetime(df["game_date"], errors="coerce")
    df = df.sort_values(["team_id", "game_date"])

    df["rpmi_short"] = np.nan
    df["rpmi_long"] = np.nan
    df["rpmi_accel"] = np.nan
    df["rpmi_delta"] = np.nan

    for team_id, g in df.groupby("team_id"):
        g = g.reset_index()

        rpmi_s = compute_window_rpmi(g, SHORT_WINDOW)
        rpmi_l = compute_window_rpmi(g, LONG_WINDOW)

        df.loc[g["index"], "rpmi_short"] = rpmi_s
        df.loc[g["index"], "rpmi_long"] = rpmi_l
        df.loc[g["index"], "rpmi_accel"] = rpmi_s - rpmi_l

        # delta vs previous game (short-term)
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
    df = pd.read_csv(INPUT_CSV)
    df = compute_rpmi(df)
    df.to_csv(OUTPUT_CSV, index=False)
    print(
        f"✅ Built dual-window RPMI → {OUTPUT_CSV}\n"
        f"   rpmi_short = {SHORT_WINDOW}-game window\n"
        f"   rpmi_long  = {LONG_WINDOW}-game window\n"
        f"   rpmi_accel = rpmi_short - rpmi_long"
    )


if __name__ == "__main__":
    main()
