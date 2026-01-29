# scripts/print_consistency_board.py

import pandas as pd

INPUT_CSV = "data/derived/team_game_metrics_with_rpmi_cvv.csv"


def consistency_label(consistency: float):
    if pd.isna(consistency):
        return None, None
    if consistency >= 0.65:
        return "🟢", "Very Consistent"
    if consistency >= 0.50:
        return "🟢", "Consistent"
    if consistency >= 0.35:
        return "⚠️", "Volatile"
    return "🔴", "Very Volatile"


def main():
    df = pd.read_csv(INPUT_CSV)
    df["game_date"] = pd.to_datetime(df["game_date"]).dt.date

    # Latest record per team
    latest = (
        df.sort_values("game_date", ascending=False)
        .drop_duplicates(subset=["team_id"])
        .sort_values("consistency", ascending=False)
    )

    # Filter out teams with missing consistency
    latest = latest[~latest["consistency"].isna()]

    print("Weekly Consistency Board 📊\n")

    for _, row in latest.iterrows():
        emoji, label = consistency_label(row["consistency"])
        if emoji and label:
            print(f"{emoji} {row['team_name']} — {label}")


if __name__ == "__main__":
    main()
