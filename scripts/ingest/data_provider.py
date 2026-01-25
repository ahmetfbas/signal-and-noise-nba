import os
import time
import requests
from typing import List, Dict
from dotenv import load_dotenv
load_dotenv()

# --------------------------------------------------
# API configuration
# --------------------------------------------------
API_URL = "https://api.balldontlie.io/v1/games"
API_KEY = os.getenv("BALLDONTLIE_API_KEY")

if not API_KEY:
    raise RuntimeError(
        "BALLDONTLIE_API_KEY environment variable is not set"
    )

HEADERS = {
    "Authorization": API_KEY
}

# --------------------------------------------------
# Internal GET helper (rate-limit safe)
# --------------------------------------------------
def _get(params: Dict, timeout: int = 30) -> requests.Response:
    resp = requests.get(
        API_URL,
        headers=HEADERS,
        params=params,
        timeout=timeout
    )

    # Handle rate limiting
    if resp.status_code == 429:
        time.sleep(1)
        resp = requests.get(
            API_URL,
            headers=HEADERS,
            params=params,
            timeout=timeout
        )

    if resp.status_code != 200:
        raise RuntimeError(
            f"BallDontLie API error "
            f"status={resp.status_code} "
            f"params={params} "
            f"body={resp.text}"
        )

    return resp

# --------------------------------------------------
# Public fetch function
# --------------------------------------------------
def fetch_games_range(
    start_date: str,
    end_date: str,
    sleep_sec: float = 0.15
) -> List[Dict]:
    """
    Fetch all games between start_date and end_date (inclusive).

    Dates must be ISO format: YYYY-MM-DD
    Returns raw API game objects (no transformation).
    """

    all_games: List[Dict] = []
    page = 1

    while True:
        params = {
            "start_date": start_date,
            "end_date": end_date,
            "per_page": 100,
            "page": page,
            "sort": "-date"
        }

        payload = _get(params).json()
        data = payload.get("data", [])
        meta = payload.get("meta", {})

        if not data:
            break

        all_games.extend(data)

        total_pages = meta.get("total_pages")
        if total_pages is None or page >= total_pages:
            break

        page += 1
        time.sleep(sleep_sec)

    return all_games
