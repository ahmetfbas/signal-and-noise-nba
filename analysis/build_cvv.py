import pandas as pd
import numpy as np

# --------------------------------------------------
# Configuration
# --------------------------------------------------

WINDOW = 5

# Typical PvE std range is ~5–20 points in NBA.
# Scaling by 10 keeps consistency in a smooth 0–1 range.
VOL_SCALE = 10.0


# --------------------------------------------------
# Core computation
# --------------------------------------------------

def compute_cvv(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    df["game_date"] = pd.to_datetime(df["game_date"], utc=True)
    df = df.sort_values(["team_id", "game_date"])

    df["pve_volatility"] = np.nan
    df["consistency"] = np.nan
    df["games_played"] = np.nan

    for team_id, g in df.groupby("team_id"):
        g = g.reset_index()

        for i, row in g.iterrows():
            games_played = i + 1
            df.loc[row["index"], "games_played"] = games_played

            # not enough history yet
            if i < WINDOW - 1:
                continue

            window = g.loc[i - WINDOW + 1 : i, "pve"].values

            # volatility in raw points
            vol = float(np.std(window, ddof=0))

            # normalized volatility
            normalized_vol = vol / VOL_SCALE

            # consistency score (higher = more stable)
            cons = 1.0 / (1.0 + normalized_vol)

            df.loc[row["index"], "pve_volatility"] = round(vol, 2)
            df.loc[row["index"], "consistency"] = cons

    # ensure clean dtype
    df["games_played"] = df["games_played"].astype("Int64")

    return df


# --------------------------------------------------
# Labeling helpers
# --------------------------------------------------

def consistency_label(consistency, games_played):
    if pd.isna(consistency):
        return "Insufficient"
    if games_played < 10:
        return "Forming"
    if consistency >= 0.65:
        return "Very Consistent"
    if consistency >= 0.50:
        return "Consistent"
    if consistency >= 0.35:
        return "Volatile"
    return "Very Volatile"


# --------------------------------------------------
# CLI
# --------------------------------------------------

if __name__ == "__main__":
    input_csv = "data/derived/team_game_metrics_with_rpmi.csv"
    output_csv = "data/derived/team_game_metrics_with_rpmi_cvv.csv"

    df = pd.read_csv(input_csv)
    df = compute_cvv(df)

    df["consistency_label"] = df.apply(
        lambda r: consistency_label(r["consistency"], r["games_played"]),
        axis=1
    )

    df.to_csv(output_csv, index=False)
