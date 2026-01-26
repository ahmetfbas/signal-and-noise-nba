import pandas as pd
import numpy as np

# --------------------------------------------------
# Configuration
# --------------------------------------------------

WINDOW = 5
WEIGHTS = np.array([1, 2, 3, 4, 5], dtype=float)
WEIGHT_SUM = WEIGHTS.sum()


# --------------------------------------------------
# Core math
# --------------------------------------------------

def weighted_pve(values: np.ndarray) -> float:
    return float(np.dot(values, WEIGHTS) / WEIGHT_SUM)


def consistency_factor(values: np.ndarray) -> float:
    std = np.std(values, ddof=0)
    return 1.0 / (1.0 + std / 10.0)


# --------------------------------------------------
# RPMI computation
# --------------------------------------------------

def compute_rpmi(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    df["game_date"] = pd.to_datetime(df["game_date"], utc=True)
    df = df.sort_values(["team_id", "game_date"])

    df["rpmi"] = np.nan
    df["rpmi_delta"] = np.nan

    for team_id, g in df.groupby("team_id"):
        g = g.reset_index().rename(columns={"index": "orig_index"})

        for i in range(WINDOW - 1, len(g)):
            window = g.loc[i - WINDOW + 1 : i, "pve"].values

            w_pve = weighted_pve(window)
            cons = consistency_factor(window)
            rpmi = round(w_pve * cons, 2)

            row_idx = g.loc[i, "orig_index"]
            df.loc[row_idx, "rpmi"] = rpmi

            prev_idx = g.loc[i - 1, "orig_index"]
            prev_rpmi = df.loc[prev_idx, "rpmi"]

            if not pd.isna(prev_rpmi):
                df.loc[row_idx, "rpmi_delta"] = round(rpmi - prev_rpmi, 2)

    return df


# --------------------------------------------------
# Labeling
# --------------------------------------------------

def momentum_label(rpmi: float) -> str:
    if pd.isna(rpmi):
        return "Insufficient"
    if rpmi >= 15:
        return "Strong Positive"
    if rpmi >= 5:
        return "↑ Improving"
    if rpmi > -5:
        return "→ Neutral"
    if rpmi > -15:
        return "↓ Slipping"
    return "Strong Negative"


# --------------------------------------------------
# CLI
# --------------------------------------------------

if __name__ == "__main__":
    INPUT_CSV = "data/derived/team_game_metrics.csv"
    OUTPUT_CSV = "data/derived/team_game_metrics_with_rpmi.csv"

    df = pd.read_csv(INPUT_CSV)
    df = compute_rpmi(df)

    df["rpmi_label"] = df["rpmi"].apply(momentum_label)

    df.to_csv(OUTPUT_CSV, index=False)

    print(f"Saved RPMI-enhanced dataset to {OUTPUT_CSV}")
