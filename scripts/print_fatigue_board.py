# scripts/print_fatigue_dashboard.py

from datetime import date
import pandas as pd
from analysis.compose_tweet import compose_tweet

SCHEDULE_PATH = "data/derived/game_schedule_today.csv"
METRICS_PATH = "data/derived/team_game_metrics_with_rpmi_cvv.csv"


def fatigue_emoji(tier: str) -> str:
    """Match fatigue emojis with pregame lens style."""
    return {
        "Critical": "😓",   # exhausted
        "High": "😓",       # tired
        "Elevated": "😐",   # moderate fatigue
        "Medium": "😐",     # balanced
        "Low": "💪",        # rested / fresh
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

    # Normalize team names
    name_map = {
            "Hawks": "Atlanta Hawks",
            "Celtics": "Boston Celtics",
            "Nets": "Brooklyn Nets",
            "Hornets": "Charlotte Hornets",
            "Bulls": "Chicago Bulls",
            "Cavaliers": "Cleveland Cavaliers",
            "Mavericks": "Dallas Mavericks",
            "Nuggets": "Denver Nuggets",
            "Pistons": "Detroit Pistons",
            "Warriors": "Golden State Warriors",
            "Rockets": "Houston Rockets",
            "Pacers": "Indiana Pacers",
            "Clippers": "Los Angeles Clippers",
            "Lakers": "Los Angeles Lakers",
            "Grizzlies": "Memphis Grizzlies",
            "Heat": "Miami Heat",
            "Bucks": "Milwaukee Bucks",
            "Timberwolves": "Minnesota Timberwolves",
            "Pelicans": "New Orleans Pelicans",
            "Knicks": "New York Knicks",
            "Thunder": "Oklahoma City Thunder",
            "Magic": "Orlando Magic",
            "76ers": "Philadelphia 76ers",
            "Suns": "Phoenix Suns",
            "Trail Blazers": "Portland Trail Blazers",
            "Kings": "Sacramento Kings",
            "Spurs": "San Antonio Spurs",
            "Raptors": "Toronto Raptors",
            "Jazz": "Utah Jazz",
            "Wizards": "Washington Wizards",
        }
    sched["home_team_name"] = sched["home_team_name"].replace(name_map)
    sched["away_team_name"] = sched["away_team_name"].replace(name_map)

    # Collect tonight’s teams
    teams_playing = pd.unique(
        sched[["home_team_name", "away_team_name"]].values.ravel()
    )

    # Latest fatigue data for those teams
    latest_fatigue = (
        metrics[metrics["team_name"].isin(teams_playing)]
        .sort_values("game_date", ascending=False)
        .drop_duplicates(subset=["team_name"])
        .sort_values("fatigue_index", ascending=False)
    )

    print(f"😴 Tonight’s Fatigue Board ({today})\n")

    for _, row in latest_fatigue.iterrows():
        emoji = fatigue_emoji(row.get("fatigue_tier", ""))
        print(
            f"{emoji} {row['team_name']:<25} — {row.get('fatigue_tier', 'N/A'):>9} "
            f"({row['fatigue_index']:.1f})"
        )

    # --- AI Commentary ---
    print("\n" + "=" * 45 + "\n")

    header = f"😴 Tonight’s Fatigue Board ({today})"
    body_text = (
        "This board compares each team's recent schedule load, travel stress, "
        "and recovery days to show who's running on fumes and who's fully rested."
    )

    tweet_main, tweet_ai = compose_tweet(
        board_name="Fatigue Board",
        data=latest_fatigue.head(10),
        header=header,
        body_text=body_text,
        mode="board",
    )

    print(tweet_main)
    print(f"\n↳ {tweet_ai}\n")


if __name__ == "__main__":
    main()
