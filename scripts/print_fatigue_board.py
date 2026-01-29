from datetime import date
import pandas as pd

SCHEDULE_PATH = "data/derived/game_schedule_today.csv"
METRICS_PATH = "data/derived/team_game_metrics.csv"


def fatigue_emoji(tier: str) -> str:
    return {
        "Critical": "🔴",
        "High": "🔴",
        "Elevated": "🟠",
        "Low": "🟢",
    }.get(tier, "⚪")


def main():
    # Load tonight’s schedule
    try:
        sched = pd.read_csv(SCHEDULE_PATH)
    except FileNotFoundError:
        print("⚠️ No schedule file found.")
        return

    sched["game_date"] = pd.to_datetime(sched["game_date"]).dt.date
    today = date.today()

    games_today = sched[sched["game_date"] == today]
    if games_today.empty:
        print("No games tonight.")
        return

    # Load fatigue metrics
    metrics = pd.read_csv(METRICS_PATH)
    metrics["game_date"] = pd.to_datetime(metrics["game_date"]).dt.date

    # Collect teams in tonight’s games
    teams_playing = pd.unique(
        games_today[["home_team_name", "away_team_name"]].values.ravel()
    )

    # Get latest fatigue data for those teams
    latest_fatigue = (
        metrics.sort_values("game_date", ascending=False)
        .drop_duplicates(subset=["team_name"])
        .query("team_name in @teams_playing")
        .sort_values("fatigue_index", ascending=False)
    )

    print("Tonight’s fatigue board 💤\n")

    for _, row in latest_fatigue.iterrows():
        emoji = fatigue_emoji(row["fatigue_tier"])
        print(f"{emoji} {row['team_name']} — {row['fatigue_tier']}")


if __name__ == "__main__":
    main()
