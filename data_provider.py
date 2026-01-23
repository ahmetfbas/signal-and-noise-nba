# api.py
import os
import time
import requests

API_URL = "https://api.balldontlie.io/v1/games"
API_KEY = os.getenv("BALLDONTLIE_API_KEY")

if not API_KEY:
    raise ValueError("BALLDONTLIE_API_KEY environment variable not set")

HEADERS = {"Authorization": API_KEY}


def _get(params, timeout=30):
    resp = requests.get(API_URL, headers=HEADERS, params=params, timeout=timeout)
    if resp.status_code == 429:
        time.sleep(1)
        resp = requests.get(API_URL, headers=HEADERS, params=params, timeout=timeout)
    if resp.status_code != 200:
        raise RuntimeError(f"API error {resp.status_code}: {resp.text}")
    return resp


def fetch_games_range(start_date: str, end_date: str, sleep_sec: float = 0.15):
    all_games = []
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
