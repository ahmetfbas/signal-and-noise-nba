# scripts/print_fatigue_dashboard.py

from datetime import date
import pandas as pd

SCHEDULE_PATH = "data/derived/game_schedule_today.csv"
METRICS_PATH = "data/derived/team_game_metrics_with_rpmi_cvv.csv"


def fatigue_emoji(tier: str) -> str:
    return {
        "Critical": "🔴",
        "High": "🔴",
        "Elevated": "🟠",
        "Medium": "🟡",
        "Low": "🟢",
    }.get(tier, "⚪")


def main():
    # Load schedule
    try:
        sched = pd.read_csv(SCHEDULE_PATH)
        sched["game_date"] = pd.to_datetime(sched["game_date"], errors="coerce").dt.date
    except FileNotFoundError:
        print("⚠️ No schedule file found.")
        return

    today = date.today()
    games_today = sched[sched["game_date"] == today]

    if games_today.empty:
        print(f"No games found for {today}.")
        return

    # Load fatigue metrics
    metrics = pd.read_csv(METRICS_PATH)
    metrics["game_date"] = pd.to_datetime(metrics["game_date"], errors="coerce").dt.date

    # Normalize team names between files
    name_map = {
        "Heat": "Miami Heat",
        "Bulls": "Chicago Bulls",
        "Hornets": "Charlotte Hornets",
        "Spurs": "San Antonio Spurs",
        "Pacers": "Indiana Pacers",
        "Hawks": "Atlanta Hawks",
        "76ers": "Philadelphia 76ers",
        "Pelicans": "New Orleans Pelicans",
        "Grizzlies": "Memphis Grizzlies",
        "Timberwolves": "Minnesota Timberwolves",
        "Rockets": "Houston Rockets",
        "Mavericks": "Dallas Mavericks",
    }
    sched["home_team_name"] = sched["home_team_name"].replace(name_map)
    sched["away_team_name"] = sched["away_team_name"].replace(name_map)

    # Collect tonight’s teams
    teams_playing = pd.unique(
        sched[["home_team_name", "away_team_name"]].values.ravel()
    )

    # Get the latest fatigue data per team
    latest_fatigue = (
        metrics[metrics["team_name"].isin(teams_playing)]
        .sort_values("game_date", ascending=False)
        .drop_duplicates(subset=["team_name"])
        .sort_values("fatigue_index", ascending=False)
    )

    print("😴 Tonight’s Fatigue Board\n")

    for _, row in latest_fatigue.iterrows():
        emoji = fatigue_emoji(row.get("fatigue_tier", ""))
        print(f"{emoji} {row['team_name']} — {row.get('fatigue_tier', 'N/A')} "
              f"({row['fatigue_index']:.1f})")


if __name__ == "__main__":
    main()
