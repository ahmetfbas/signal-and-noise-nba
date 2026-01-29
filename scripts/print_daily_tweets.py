from datetime import date, timedelta
import pandas as pd
import os


# --------------------------------------------------
# PATHS
# --------------------------------------------------

ENV_PATH = "data/derived/game_environment.csv"
SCHEDULE_PATH = "data/derived/game_schedule_today.csv"


# --------------------------------------------------
# HELPERS
# --------------------------------------------------

def ensure_csv(path: str, columns: list):
    """
    Create empty CSV with headers if file does not exist.
    """
    if not os.path.exists(path):
        df = pd.DataFrame(columns=columns)
        df.to_csv(path, index=False)


# --------------------------------------------------
# POST-GAME
# --------------------------------------------------

def print_postgame():
    ensure_csv(
        ENV_PATH,
        [
            "game_id",
            "game_date",
            "matchup",
            "environment_label",
        ],
    )

    env = pd.read_csv(ENV_PATH)

    print("\n=== POST-GAME THREAD ===\n")

    if env.empty:
        print("No completed games found.\n")
        return

    env["game_date"] = pd.to_datetime(env["game_date"]).dt.date
    today = date.today()

    last_game_date = env[env["game_date"] < today]["game_date"].max()


    if pd.isna(last_game_date):
        print("No completed games found for last night.\n")
        return

    games = env[env["game_date"] == last_game_date]

    for _, g in games.iterrows():
        label = "🟢" if g["environment_label"] == "Clean" else "🔁"

        print(f'{g["matchup"]} {label}')
        print("Result: final")
        print("The setup leaned one way, and the result followed.\n")


# --------------------------------------------------
# PRE-GAME
# --------------------------------------------------

def print_pregame():
    ensure_csv(
        SCHEDULE_PATH,
        [
            "game_id",
            "game_date",
            "home_team_id",
            "home_team_name",
            "away_team_id",
            "away_team_name",
            "matchup",
        ],
    )

    schedule = pd.read_csv(SCHEDULE_PATH)

    print("\n=== PRE-GAME THREAD ===\n")

    if schedule.empty:
        print("No scheduled games found for today.\n")
        return

    for _, g in schedule.iterrows():
        print(f'{g["matchup"]} — pregame lens')
        print("Momentum: TBD")
        print("Fatigue: TBD")
        print("Consistency: TBD")
        print("Volatility: TBD\n")


# --------------------------------------------------
# MAIN
# --------------------------------------------------

def main():
    print_postgame()
    print_pregame()


if __name__ == "__main__":
    main()
