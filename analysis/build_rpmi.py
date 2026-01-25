import pandas as pd
import numpy as np


WINDOW = 5
WEIGHTS = np.array([1, 2, 3, 4, 5])
WEIGHT_SUM = WEIGHTS.sum()


def weighted_pve(values):
    return np.dot(values, WEIGHTS) / WEIGHT_SUM


def consistency_factor(values):
    std = np.std(values, ddof=0)
    return 1 / (1 + std / 10)


def compute_rpmi(df):
    df = df.copy()
    df["game_date"] = pd.to_datetime(df["game_date"])
    df = df.sort_values(["team_id", "game_date"])

    df["rpmi"] = np.nan
    df["rpmi_delta"] = np.nan

    for team_id, g in df.groupby("team_id"):
        g = g.reset_index()

        for i in range(WINDOW - 1, len(g)):
            window = g.loc[i - WINDOW + 1 : i, "pve"].values

            w_pve = weighted_pve(window)
            cons = consistency_factor(window)
            rpmi = round(w_pve * cons, 2)

            df.loc[g.loc[i, "index"], "rpmi"] = rpmi

            if i > WINDOW - 1:
                prev = df.loc[g.loc[i - 1, "index"], "rpmi"]
                df.loc[g.loc[i, "index"], "rpmi_delta"] = (
                    None if pd.isna(prev) else round(rpmi - prev, 2)
                )

    return df


def momentum_label(rpmi):
    if pd.isna(rpmi):
        return "Insufficient"
    if rpmi >= 15:
        return "🔥 Strong Positive"
    if rpmi >= 5:
        return "↑ Improving"
    if rpmi > -5:
        return "→ Neutral"
    if rpmi > -15:
        return "↓ Slipping"
    return "🚨 Strong Negative"


if __name__ == "__main__":
    input_csv = "data/derived/team_game_metrics.csv"
    output_csv = "data/derived/team_game_metrics_with_rpmi.csv"

    df = pd.read_csv(input_csv)
    df = compute_rpmi(df)

    df["rpmi_label"] = df["rpmi"].apply(momentum_label)

    df.to_csv(output_csv, index=False)

    print(f"Saved RPMI-enhanced dataset to {output_csv}")
