# scripts/print_momentum_board.py
import pandas as pd

INPUT_CSV = "data/derived/team_game_metrics_with_rpmi.csv"


def momentum_label(rpmi: float):
    if pd.isna(rpmi):
        return None, None
    if rpmi >= 5:
        return "🟢", "Strong"
    if rpmi >= 2:
        return "🟢", "Positive"
    if rpmi >= -2:
        return "🟠", "Flat"
    return "🔴", "Fading"


def main():
    df = pd.read_csv(INPUT_CSV)
    df["game_date"] = pd.to_datetime(df["game_date"]).dt.date

    # Latest record per team
    latest = (
        df.sort_values("game_date", ascending=False)
        .drop_duplicates(subset=["team_id"])
        .sort_values("rpmi", ascending=False)
    )

    # Filter out teams with missing rpmi
    latest = latest[~latest["rpmi"].isna()]

    print("Weekly Momentum Board 🔄\n")

    for _, row in latest.iterrows():
        emoji, label = momentum_label(row["rpmi"])
        if emoji and label:  # skip if None
            print(f"{emoji} {row['team_name']} — {label}")


if __name__ == "__main__":
    main()
