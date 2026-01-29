# scripts/print_momentum_board.py

from datetime import date
import pandas as pd

INPUT_CSV = "data/derived/team_game_metrics_with_rpmi.csv"


def momentum_label(rpmi: float) -> str:
    if pd.isna(rpmi):
        return "⚪", "Unknown"
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
    today = date.today()

    # only teams playing today
    df_today = df[df["game_date"] == today]

    if df_today.empty:
        print("No games tonight.")
        return

    # safety: one row per team
    df_today = df_today.drop_duplicates(subset=["team_id"])

    # sort by momentum (highest first)
    df_today = df_today.sort_values("rpmi", ascending=False)

    print("Tonight’s momentum board 🔄\n")

    for _, row in df_today.iterrows():
        emoji, label = momentum_label(row["rpmi"])
        team = row["team_name"]
        print(f"{emoji} {team} — {label}")


if __name__ == "__main__":
    main()
