import time

def fetch_games(start_date, end_date):
    all_games = []
    page = 1
    PER_PAGE = 100
    MAX_RETRIES = 5

    while True:
        params = {
            "start_date": start_date,
            "end_date": end_date,
            "per_page": PER_PAGE,
            "page": page
        }

        retries = 0
        while True:
            r = requests.get(API_URL, headers=HEADERS, params=params, timeout=30)

            if r.status_code == 200:
                break

            if r.status_code == 429:
                # Rate limited → wait and retry
                wait_time = 2 ** retries
                print(f"Rate limited. Sleeping {wait_time}s...")
                time.sleep(wait_time)
                retries += 1
                if retries >= MAX_RETRIES:
                    raise RuntimeError("Exceeded max retries due to rate limiting.")
                continue

            # Any other error
            raise RuntimeError(r.text)

        payload = r.json()
        data = payload.get("data", [])
        all_games.extend(data)

        # Stop if this was the last page
        if len(data) < PER_PAGE:
            break

        page += 1
        time.sleep(0.4)  # 👈 polite pause between pages

    return all_games
