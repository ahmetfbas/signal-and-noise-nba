import requests
from datetime import datetime

def get_todays_games():
    today = datetime.utcnow().strftime("%Y-%m-%d")

    url = "https://api.balldontlie.io/v1/games"
    params = {
        "dates[]": today,
        "per_page": 100
    }

    response = requests.get(url, params=params)

    if response.status_code != 200:
        print("API error:", response.status_code)
        print(response.text)
        return []

    data = response.json()
    return data["data"]

def main():
    games = get_todays_games()

    if not games:
        print("No NBA games today.")
        return

    print("Today's NBA games:")
    for game in games:
        home = game["home_team"]["full_name"]
        away = game["visitor_team"]["full_name"]
        print(f"- {away} @ {home}")

if __name__ == "__main__":
    main()
