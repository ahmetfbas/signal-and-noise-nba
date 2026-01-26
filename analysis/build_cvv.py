import pandas as pd
import numpy as np

WINDOW = 5
VOL_SCALE = 10  # normalization factor for PvE volatility


def compute_cvv(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    df["game_date"] = pd.to_datetime(df["game_date"])
    df = df.sort_values(["team_id", "game_date"])

    df["pve_volatility"] = np.nan
    df["consistency"] = np.nan
    df["games_played"] = np.nan

    for team_id, g in df.groupby("team_id"):
        g = g.reset_index()

        for i in range(len(g)):
            games_played = i + 1
            df.loc[g.loc[i, "index"], "games_played"] = games_played

            if i < WINDOW - 1:
                continue

            window = g.loc[i - WINDOW + 1 : i, "pve"].values

            vol = np.std(window, ddof=0)
            normalized_vol = vol / VOL_SCALE
            consistency = round(1 / (1 + normalized_vol), 3)

            df.loc[g.loc[i, "index"], "pve_volatility"] = round(vol, 2)
            df.loc[g.loc[i, "index"], "consistency"] = consistency

    return df


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
# PIPELINE ENTRY POINT
# --------------------------------------------------

def main():
    input_csv = "data/derived/team_game_metrics_with_rpmi.csv"
    output_csv = "data/derived/team_game_metrics_with_rpmi_cvv.csv"

    df = pd.read_csv(input_csv)
    df = compute_cvv(df)

    df["consistency_label"] = df.apply(
        lambda r: consistency_label(r["consistency"], r["games_played"]),
        axis=1
    )

    df.to_csv(output_csv, index=False)


if __name__ == "__main__":
    main()
