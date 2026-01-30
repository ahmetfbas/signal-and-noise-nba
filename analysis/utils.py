import math
from datetime import datetime, date
from typing import Dict, List
import pandas as pd
from pathlib import Path


# --------------------------------------------------
# Game helpers (pure logic, no I/O)
# --------------------------------------------------

def game_datetime(g: Dict) -> datetime:
    return datetime.fromisoformat(g["date"].replace("Z", "+00:00"))


def game_date(g: Dict):
    return game_datetime(g).date()


def is_completed(g: Dict) -> bool:
    return (
        g.get("home_team_score") is not None
        and g.get("visitor_team_score") is not None
    )


def team_in_game(g: Dict, team_id: int) -> bool:
    return (
        g["home_team"]["id"] == team_id
        or g["visitor_team"]["id"] == team_id
    )


def margin_for_team(g: Dict, team_id: int) -> float:
    is_home = g["home_team"]["id"] == team_id
    team_score = g["home_team_score"] if is_home else g["visitor_team_score"]
    opp_score = g["visitor_team_score"] if is_home else g["home_team_score"]
    return team_score - opp_score


# --------------------------------------------------
# Math helpers
# --------------------------------------------------

def clamp(x: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, x))


# --------------------------------------------------
# Form & opponent adjustment
# --------------------------------------------------

def build_team_forms(games: List[Dict]) -> Dict[int, float]:
    forms: Dict[int, float] = {}

    teams = {
        g["home_team"]["id"]
        for g in games
        if is_completed(g)
    } | {
        g["visitor_team"]["id"]
        for g in games
        if is_completed(g)
    }

    for team_id in teams:
        margins = [
            margin_for_team(g, team_id)
            for g in games
            if is_completed(g) and team_in_game(g, team_id)
        ]
        forms[team_id] = (
            sum(margins) / len(margins)
            if margins else 0.0
        )

    return forms


def recent_adjusted_margin_from_games(
    team_id: int,
    games: List[Dict],
    opponent_forms: Dict[int, float]
) -> float:
    adjusted = []

    for g in games:
        if not is_completed(g) or not team_in_game(g, team_id):
            continue

        raw_margin = margin_for_team(g, team_id)

        opponent_id = (
            g["visitor_team"]["id"]
            if g["home_team"]["id"] == team_id
            else g["home_team"]["id"]
        )

        opp_form = opponent_forms.get(opponent_id, 0.0)

        K = 10.0
        factor = clamp((opp_form + K) / K, 0.5, 1.5)

        adjusted.append(raw_margin * factor)

    return sum(adjusted) / len(adjusted) if adjusted else 0.0


def expected_margin_base(
    game: Dict,
    team_id: int,
    games: List[Dict]
) -> float:
    opponent_id = (
        game["visitor_team"]["id"]
        if game["home_team"]["id"] == team_id
        else game["home_team"]["id"]
    )

    opponent_forms = build_team_forms(games)

    team_form = recent_adjusted_margin_from_games(
        team_id, games, opponent_forms
    )
    opp_form = recent_adjusted_margin_from_games(
        opponent_id, games, opponent_forms
    )

    return team_form - opp_form


# --------------------------------------------------
# Context adjustments
# --------------------------------------------------

def home_away_adjustment(game: Dict, team_id: int) -> float:
    HOME_ADVANTAGE = 2.0
    return (
        HOME_ADVANTAGE
        if game["home_team"]["id"] == team_id
        else -HOME_ADVANTAGE
    )


def fatigue_adjustment(fatigue_index: float) -> float:
    normalized = min(fatigue_index / 100.0, 1.0)
    FATIGUE_WEIGHT = 6.0
    return -normalized * FATIGUE_WEIGHT


# --------------------------------------------------
# Final expectation
# --------------------------------------------------

def expected_margin_for_team(
    game: Dict,
    team_id: int,
    games: List[Dict],
    fatigue_index: float = 0.0
) -> float:
    base = expected_margin_base(game, team_id, games)
    ha = home_away_adjustment(game, team_id)
    fatigue = fatigue_adjustment(fatigue_index)

    return base + ha + fatigue


def expected_margin_breakdown(
    game: Dict,
    team_id: int,
    games: List[Dict],
    fatigue_index: float = 0.0
) -> Dict[str, float]:
    base = expected_margin_base(game, team_id, games)
    ha = home_away_adjustment(game, team_id)
    fatigue = fatigue_adjustment(fatigue_index)

    return {
        "base_form_diff": round(base, 2),
        "home_away": round(ha, 2),
        "fatigue_adj": round(fatigue, 2),
        "expected_total": round(base + ha + fatigue, 2),
    }


# --------------------------------------------------
# Debug helpers
# --------------------------------------------------

def print_team_past_games_debug(
    team_id: int,
    team_name: str,
    games: List[Dict],
    opponent_forms: Dict[int, float],
    limit: int = 5
) -> None:
    print(f"\nPast games debug — {team_name}")
    print("-" * 70)

    team_games = [
        g for g in games
        if is_completed(g) and team_in_game(g, team_id)
    ]

    team_games = sorted(team_games, key=game_date)

    if not team_games:
        print("No past games found.")
        return

    for g in team_games[-limit:]:
        is_home = g["home_team"]["id"] == team_id
        opponent = g["visitor_team"] if is_home else g["home_team"]

        raw = margin_for_team(g, team_id)
        opp_form = opponent_forms.get(opponent["id"], 0.0)

        K = 10.0
        factor = clamp((opp_form + K) / K, 0.5, 1.5)
        adj = raw * factor

        location = "H" if is_home else "A"

        print(
            f"{game_date(g)} {location} vs {opponent['abbreviation']:3s} | "
            f"raw: {raw:>6.1f} | "
            f"opp_form: {opp_form:>6.1f} | "
            f"factor: {factor:>4.2f} | "
            f"adj: {adj:>6.1f}"
        )


# --------------------------------------------------
# Travel helpers (optional / future use)
# --------------------------------------------------

CITY_COORDS = {
    "Atlanta": (33.7573, -84.3963),
    "Boston": (42.3662, -71.0621),
    "Brooklyn": (40.6826, -73.9754),
    "Charlotte": (35.2251, -80.8392),
    "Chicago": (41.8807, -87.6742),
    "Cleveland": (41.4965, -81.6882),
    "Dallas": (32.7905, -96.8103),
    "Denver": (39.7487, -105.0077),
    "Detroit": (42.3411, -83.0553),
    "Houston": (29.7508, -95.3621),
    "Indianapolis": (39.7639, -86.1555),
    "Los Angeles": (34.0430, -118.2673),
    "Memphis": (35.1382, -90.0506),
    "Miami": (25.7814, -80.1870),
    "Milwaukee": (43.0451, -87.9172),
    "Minneapolis": (44.9795, -93.2760),
    "New Orleans": (29.9490, -90.0821),
    "New York": (40.7505, -73.9934),
    "Oklahoma City": (35.4634, -97.5151),
    "Orlando": (28.5392, -81.3839),
    "Philadelphia": (39.9012, -75.1720),
    "Phoenix": (33.4457, -112.0712),
    "Portland": (45.5316, -122.6668),
    "Sacramento": (38.5802, -121.4997),
    "San Antonio": (29.4269, -98.4375),
    "San Francisco": (37.7680, -122.3877),
    "Toronto": (43.6435, -79.3791),
    "Salt Lake City": (40.7683, -111.9011),
    "Washington": (38.8981, -77.0209),
}


def haversine_miles(lat1, lon1, lat2, lon2) -> float:
    R = 3958.8
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)

    a = (
        math.sin(dp / 2) ** 2
        + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    )

    return round(2 * R * math.atan2(math.sqrt(a), math.sqrt(1 - a)), 1)


def travel_miles(city_a: str, city_b: str):
    if city_a not in CITY_COORDS or city_b not in CITY_COORDS:
        return None
    return haversine_miles(*CITY_COORDS[city_a], *CITY_COORDS[city_b])


# --------------------------------------------------
# Season record helper
# --------------------------------------------------

def season_record(df, team_identifier, cutoff):
    # Decide whether to use ID or name
    key = "team_id" if "team_id" in df.columns and isinstance(team_identifier, (int, float)) else "team_name"

    # Normalize datetimes (avoid tz conflicts)
    df["game_date"] = pd.to_datetime(df["game_date"], errors="coerce").dt.tz_localize(None)
    cutoff = pd.to_datetime(cutoff).tz_localize(None)
    season_start = pd.Timestamp("2025-10-22")

    subset = df[
        (df[key] == team_identifier)
        & (df["game_date"] >= season_start)
        & (df["game_date"] <= cutoff)
    ]

    if "actual_margin" in subset.columns:
        wins = (subset["actual_margin"] > 0).sum()
        losses = (subset["actual_margin"] <= 0).sum()
    else:
        wins = losses = 0

    return int(wins), int(losses)
