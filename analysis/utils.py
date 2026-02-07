import math
from datetime import datetime
from typing import Dict, List, Optional, Tuple

import pandas as pd


# --------------------------------------------------
# Game helpers (pure parsing / logic)
# --------------------------------------------------

def game_datetime(g: Dict) -> datetime:
    """Parse API UTC datetime safely."""
    return datetime.fromisoformat(g["date"].replace("Z", "+00:00"))


def game_date(g: Dict):
    """Canonical game date = UTC calendar date."""
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


def margin_for_team(g: Dict, team_id: int) -> Optional[float]:
    """Return margin for team; None if game incomplete."""
    if not is_completed(g):
        return None

    is_home = g["home_team"]["id"] == team_id
    team_score = g["home_team_score"] if is_home else g["visitor_team_score"]
    opp_score = g["visitor_team_score"] if is_home else g["home_team_score"]

    return float(team_score - opp_score)


# --------------------------------------------------
# Math helpers
# --------------------------------------------------

def clamp(x: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, x))


# --------------------------------------------------
# Debug helpers (NO alternative logic)
# --------------------------------------------------

def recent_team_margins(
    team_id: int,
    games: List[Dict],
    limit: int = 10,
) -> List[Tuple[datetime.date, float]]:
    """
    Return recent (date, margin) pairs for inspection.
    No adjustment, no weighting.
    """
    rows = []

    for g in games:
        if not is_completed(g) or not team_in_game(g, team_id):
            continue

        m = margin_for_team(g, team_id)
        if m is not None:
            rows.append((game_date(g), m))

    rows.sort(key=lambda x: x[0])
    return rows[-limit:]


def print_recent_games_debug(
    team_id: int,
    team_name: str,
    games: List[Dict],
    limit: int = 5,
) -> None:
    """Pure debug print. No modeling."""
    rows = recent_team_margins(team_id, games, limit)

    print(f"\nRecent games — {team_name}")
    print("-" * 60)

    if not rows:
        print("No completed games.")
        return

    for d, m in rows:
        print(f"{d} | margin: {m:>6.1f}")


# --------------------------------------------------
# Travel helpers (used by FLI)
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
    """Great-circle distance in miles."""
    R = 3958.8
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)

    a = (
        math.sin(dp / 2) ** 2
        + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    )

    return round(2 * R * math.atan2(math.sqrt(a), math.sqrt(1 - a)), 1)


def travel_miles(city_a: Optional[str], city_b: Optional[str]) -> Optional[float]:
    if not city_a or not city_b:
        return None
    if city_a not in CITY_COORDS or city_b not in CITY_COORDS:
        return None

    return haversine_miles(*CITY_COORDS[city_a], *CITY_COORDS[city_b])


# --------------------------------------------------
# Season record helper (safe, aligned)
# --------------------------------------------------

def season_record(
    df: pd.DataFrame,
    team_name: str,
    cutoff_date,
) -> Tuple[int, int]:
    """
    Season W–L record up to cutoff_date.
    Uses actual_margin from pipeline.
    """
    cutoff = pd.to_datetime(cutoff_date)

    if cutoff.month < 7:
        season_start_year = cutoff.year - 1
    else:
        season_start_year = cutoff.year

    season_start = pd.Timestamp(year=season_start_year, month=10, day=1)

    team_games = df[
        (df["team_name"] == team_name)
        & (pd.to_datetime(df["game_date"]) >= season_start)
        & (pd.to_datetime(df["game_date"]) <= cutoff)
    ]

    wins = int((team_games["actual_margin"] > 0).sum())
    losses = int((team_games["actual_margin"] < 0).sum())

    return wins, losses
