from datetime import datetime, timedelta
from utils import (
    fetch_games_range,
    game_date,
    is_completed,
    team_in_game,
    travel_miles
)

def density_7d_score(g7):
    if g7 <= 2: return 10
    if g7 == 3: return 40
    if g7 == 4: return 75
    return 95

def density_14d_score(g14):
    if g14 <= 4: return 10
    if g14 == 5: return 35
    if g14 == 6: return 55
    if g14 == 7: return 75
    return 95

def recovery_offset(days):
    if days == 1: return 0.00
    if days == 2: return 0.10
    if days == 3: return 0.25
    if days == 4: return 0.40
    return 0.55

def travel_load(miles):
    if miles is None: return 1
    if miles < 300: return 1
    if miles < 800: return 2
    return 3

def fatigue_index(density, days_since, travel):
    b2b = 1 if days_since == 1 else 0
    raw = density + (12 if b2b else 0) + travel * 6 + (10 if b2b and travel >= 2 else 0)
    return round(raw * (1 - recovery_offset(days_since)), 1)

def fatigue_tier(score):
    if score < 30: return "Low"
    if score < 50: return "Elevated"
    if score < 70: return "High"
    return "Critical"

def last_game_info(team_id, games, today):
    past = [g for g in games if team_in_game(g, team_id) and game_date(g) < today]
    if not past:
        return None, None
    last = max(past, key=lambda g: game_date(g))
    city = last["home_team"]["city"]
    return game_date(last), city

def count_games(team_id, games, start, end):
    return sum(
        1 for g in games
        if team_in_game(g, team_id)
        and start <= game_date(g) < end
        and is_completed(g)
    )

def main():
    today = datetime.utcnow().date()

    g7_start = today - timedelta(days=7)
    g14_start = today - timedelta(days=14)

    games_14 = fetch_games_range(g14_start.isoformat(), today.isoformat())
    games_today = [g for g in games_14 if game_date(g) == today]

    print("\n🏀 Fatigue & Load — Today\n")

    for g in games_today:
        for team in [g["away_team"] if "away_team" in g else g["visitor_team"], g["home_team"]]:
            tid = team["id"]

            g7 = count_games(tid, games_14, g7_start, today)
            g14 = count_games(tid, games_14, g14_start, today)

            density = round(
                0.65 * density_7d_score(g7) +
                0.35 * density_14d_score(g14),
                1
            )

            last_date, last_city = last_game_info(tid, games_14, today)
            days_since = (today - last_date).days if last_date else 5

            miles = travel_miles(last_city, g["home_team"]["city"])
            travel = travel_load(miles)

            fatigue = fatigue_index(density, days_since, travel)

            print(f"🧪 {team['full_name']}")
            print(f"  l7_games = {g7}")
            print(f"  l14_games = {g14}")
            print(f"  schedule_density = {density}")
            print(f"  days_since_last = {days_since}")
            print(f"  travel_miles = {miles}")
            print(f"  travel_load = {travel}")
            print(f"  fatigue_index = {fatigue}")
            print(f"  tier = {fatigue_tier(fatigue)}\n")

if __name__ == "__main__":
    main()
