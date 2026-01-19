import os
import requests
from datetime import datetime, timedelta

API_URL = "https://api.balldontlie.io/v1/games"
API_KEY = os.getenv("BALLDONTLIE_API_KEY")

HEADERS = {
    "Authorization": API_KEY
}

def fetch_games(start_date, end_date):
    params = {
        "start_date": start_date,
        "end_date": end_date,
        "per_page": 100
    }

    response = requests.get(API_URL, headers=HEADERS, params=params)

    if response.status_code != 200:
        print("API error:", response.status_code)
        print(response.text)
        return []

    return response.json()["data"]

def count_games(team_id, games):
    return sum(
        1 for g in games
        if g["home_team"]["id"] == team_id or g["visitor_team"]["id"] == team_id
    )

def schedule_density_score(g7, g14):
    d7 = g7 / 7
    d14 = g14 / 14
    d_raw = 0.6 * d7 + 0.4 * d14
    return round(100 * d_raw, 1)

def density_label(D):
    if D < 35:
        return "Light"
    elif D < 50:
        return "Moderate"
    elif D < 65:
        return "Heavy"
    else:
        return "Extreme"
        
def format_tweet(games_output):
    lines = ["Tonight’s NBA fatigue context 🧠", ""]
    lines.extend(games_output)
    return "\n".join(lines)


def main():
    today = datetime.utcnow().date()
    today_str = today.isoformat()

    games_today = fetch_games(today_str, today_str)

    if not games_today:
        print("No NBA games today.")
        return

    games_7d = fetch_games((today - timedelta(days=7)).isoformat(), today_str)
    games_14d = fetch_games((today - timedelta(days=14)).isoformat(), today_str)

    tweet_lines = []

    for game in games_today:
        home = game["home_team"]
        away = game["visitor_team"]

        away_7d = count_games(away["id"], games_7d)
        away_14d = count_games(away["id"], games_14d)
        home_7d = count_games(home["id"], games_7d)
        home_14d = count_games(home["id"], games_14d)

        away_D = schedule_density_score(away_7d, away_14d)
        home_D = schedule_density_score(home_7d, home_14d)

        tweet_lines.append(f"{away['full_name']} @ {home['full_name']}")
        tweet_lines.append(
            f"• {away['full_name']}: {density_label(away_D)} (D={away_D})"
        )
        tweet_lines.append(
            f"• {home['full_name']}: {density_label(home_D)} (D={home_D})"
        )
        tweet_lines.append("")

    tweet = format_tweet(tweet_lines)
    print(tweet)


if __name__ == "__main__":
    main()
