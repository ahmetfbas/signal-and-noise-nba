from datetime import date
import pandas as pd

SCHEDULE_PATH = "data/derived/game_schedule_today.csv"
METRICS_PATH = "data/derived/team_game_metrics.csv"

# -----------------------------
# Emoji + helpers
# -----------------------------

def fatigue_emoji(tier: str) -> str:
    return {
        "Critical": "🥵",
        "High": "😓",
        "Elevated": "😐",
        "Low": "💪",
    }.get(tier, "⚪")


def travel_bucket(miles: float) -> str:
    if pd.isna(miles):
        return "Unknown travel"
    if miles >= 1500:
        return "Heavy travel"
    if miles >= 700:
        return "Moderate travel"
    return "Low travel"


def rest_label(days: float) -> str:
    if pd.isna(days):
        return "Unknown rest"

    days = int(days)

    if days == 1:
        return "B2B"

    rest_days = days - 1
    if rest_days == 1:
        return "1 day rest"

    return f"{rest_days} days rest"


def density_label(games_7: float) -> str:
    if pd.isna(games_7):
        return "Unknown schedule"
    return f"{int(games_7)} games in last 7"


# -----------------------------
# Main
# -----------------------------

def main():
    today = date.today()

    # Load schedule
    try:
        sched = pd.read_csv(SCHEDULE_PATH)
    except FileNotFoundError:
        print("⚠️ Schedule file missing.")
        return

    sched["game_date"] = pd.to_datetime(
        sched["game_date"], errors="coerce"
    ).dt.date

    games_today = sched[sched["game_date"] == today]

    if games_today.empty:
        print(f"No games found for {today}.")
        return

    # Load fatigue metrics
    metrics = pd.read_csv(METRICS_PATH)
    metrics["game_date"] = pd.to_datetime(
        metrics["game_date"], errors="coerce"
    ).dt.date

    # Latest fatigue snapshot per team
    latest = (
        metrics.sort_values("game_date", ascending=False)
        .drop_duplicates(subset=["team_name"])
    )

    for _, g in games_today.iterrows():

        home = g["home_team_name"]
        away = g["away_team_name"]

        h = latest[latest["team_name"] == home]
        a = latest[latest["team_name"] == away]

        if h.empty or a.empty:
            continue

        h = h.iloc[0]
        a = a.iloc[0]

        away_lines = [
            density_label(a["games_last_7"]),
            rest_label(a["days_since_last_game"]),
            travel_bucket(a["travel_miles"]),
        ]

        home_lines = [
            density_label(h["games_last_7"]),
            rest_label(h["days_since_last_game"]),
            travel_bucket(h["travel_miles"]),
        ]

        # Interpretation logic
        if a["fatigue_index"] > h["fatigue_index"] + 10:
            interp = "🔎 Away side enters noticeably more taxed."
        elif h["fatigue_index"] > a["fatigue_index"] + 10:
            interp = "🔎 Home side enters noticeably more taxed."
        else:
            interp = "🔎 No major fatigue edge, execution likely decides."

        # -----------------------------
        # PRINT BLOCK (Thread-Ready)
        # -----------------------------
        print("🧠 Fatigue Watch\n")

        print(
            f"{away} @ {home} ({today})\n\n"
            f"{away}: {a['fatigue_tier']} ({a['fatigue_index']:.1f}) {fatigue_emoji(a['fatigue_tier'])}\n"
            f"• {away_lines[0]}\n"
            f"• {away_lines[1]}\n"
            f"• {away_lines[2]}\n\n"
            f"{home}: {h['fatigue_tier']} ({h['fatigue_index']:.1f}) {fatigue_emoji(h['fatigue_tier'])}\n"
            f"• {home_lines[0]}\n"
            f"• {home_lines[1]}\n"
            f"• {home_lines[2]}\n\n"
            f"{interp}\n"
        )

        print("-" * 40 + "\n")


if __name__ == "__main__":
    main()
