# scripts/print_fatigue_board.py

from datetime import date
import pandas as pd

INPUT_CSV = "data/derived/team_game_metrics.csv"


def fatigue_emoji(tier: str) -> str:
    return {
        "Critical": "🔴",
        "High": "🔴",
        "Elevated": "🟠",
        "Low": "🟢",
    }.get(tier, "⚪")


def main():
    df = pd.read_csv(INPUT_CSV)

    df["game_date"] = pd.to_datetime(df["game_date"]).dt.date
    today = date.today()

    df_today = df[df["game_date"] == today]

    if df_today.empty:
        print("No games tonight.")
        return

    df_today = df_today.drop_duplicates(subset=["team_id"])
    df_today = df_today.sort_values("fatigue_index", ascending=False)

    print("Tonight’s fatigue board 💤\n")

    for _, row in df_today.iterrows():
        emoji = fatigue_emoji(row["fatigue_tier"])
        team = row["team_name"]
        tier = row["fatigue_tier"]
        print(f"{emoji} {team} — {tier}")


if __name__ == "__main__":
    main()
