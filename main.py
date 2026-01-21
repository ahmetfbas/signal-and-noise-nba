import os
import requests
from datetime import datetime, timedelta
from collections import defaultdict

API_URL = "https://api.balldontlie.io/v1/games"
API_KEY = os.getenv("BALLDONTLIE_API_KEY")

if not API_KEY:
    raise ValueError("BALLDONTLIE_API_KEY environment variable not set")

HEADERS = {"Authorization": API_KEY}

# ---------------- API ----------------
def fetch_games(start_date: str, end_date: str):
    all_games = []
    page = 1

    while True:
        params = {
            "start_date": start_date,
            "end_date": end_date,
            "per_page": 100,
            "page": page
        }

        resp = requests.get(API_URL, headers=HEADERS, params=params)
        if resp.status_code != 200:
            raise RuntimeError(f"API error {resp.status_code}: {resp.text}")

        payload = resp.json()
        all_games.extend(payload.get("data", []))

        if page >= payload.get("meta", {}).get("total_pages", 1):
            break

        page += 1

    return all_games


def game_datetime(game):
    return datetime.fromisoformat(game["date"].replace("Z", "+00:00"))


def game_day(game):
    return game_datetime(game).date().isoformat()


# ---------------- PRINT ----------------
def print_games_grouped_by_day(games, title):
    print(f"\n{title}")
    print("=" * len(title))

    if not games:
        print("No games.")
        return

    by_day = defaultdict(list)
    for g in games:
        by_day[game_day(g)].append(g)

    for day in sorted(by_day.keys()):
        print(f"📅 {day} — {len(by_day[day])} games")
        for g in by_day[day]:
            away = g["visitor_team"]["full_name"]
            home = g["home_team"]["full_name"]
            tip = game_datetime(g).strftime("%Y-%m-%d %H:%M UTC")
            print(f"  {away} @ {home} | tipoff: {tip}")
        print("-" * 60)


# ---------------- MAIN ----------------
def main():
    today = datetime.utcnow().date()
    yesterday = today - timedelta(days=1)

    start_date = (today - timedelta(days=6)).isoformat()  # last 7 days total
    end_date = today.isoformat()

    print(f"Yesterday : {yesterday.isoformat()}")
    print(f"Today     : {today.isoformat()}")

    games_last_7 = fetch_games(start_date, end_date)
    # Extra history for 14-day density (same date logic style)
    start_14 = (today - timedelta(days=13)).isoformat()  # last 14 calendar days incl today
    games_last_14 = fetch_games(start_14, today.isoformat())

    print_games_grouped_by_day(
        games_last_7,
        f"NBA API — Games from LAST 7 days ({start_date} → {end_date})"
    )
    # ---------------- DENSITY (ONLY TEAMS PLAYING TODAY) ----------------
    print("\nDENSITY — Teams playing today (G7 + G14 → D7 + D14 → blended D)\n")

    # Collect teams playing today from games_last_7 (already fetched)
    teams_today = {}
    for g in games_last_7:
        if game_datetime(g).date() == today:
            home = g["home_team"]
            away = g["visitor_team"]
            teams_today[home["id"]] = home["full_name"]
            teams_today[away["id"]] = away["full_name"]

    # Compute density for those teams
    for team_id, team_name in teams_today.items():
        # Counts are STRICTLY BEFORE today
        g7 = count_games_in_window(
            team_id,
            games_last_7,
            today - timedelta(days=7),
            today
        )

        g14 = count_games_in_window(
            team_id,
            games_last_14,
            today - timedelta(days=14),
            today
        )

        d7 = density_7d_score(g7)
        d14 = density_14d_score(g14)
        D = round(0.65 * d7 + 0.35 * d14, 1)

        print(
            f"{team_name}\n"
            f"  G7  (last 7, before today):  {g7}  → D7={d7}\n"
            f"  G14 (last 14, before today): {g14} → D14={d14}\n"
            f"  Blended Density D = 0.65*D7 + 0.35*D14 = {D}\n"
        )



if __name__ == "__main__":
    main()
