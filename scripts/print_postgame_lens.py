import pandas as pd
from datetime import datetime, timedelta

INPUT_CSV = "data/derived/team_game_metrics_with_rpmi_cvv.csv"


# --------------------------------------------------
# Helpers
# --------------------------------------------------

def signal_dot(expected_margin_home, actual_margin_home):
    if pd.isna(expected_margin_home):
        return "🟡"
    aligned = expected_margin_home * actual_margin_home > 0
    if aligned:
        return "🟢"
    if abs(actual_margin_home) <= 4:
        return "🟡"
    return "🔴"


# --------------------------------------------------
# Formatter
# --------------------------------------------------

def format_postgame(home, away):
    matchup = f"{away['team_name']} @ {home['team_name']}"
    actual_margin_home = home["actual_margin"]
    expected_margin = home.get("expected_margin")
    dot = signal_dot(expected_margin, actual_margin_home)

    winner = home if actual_margin_home > 0 else away
    loser = away if actual_margin_home > 0 else home

    score = f"{winner['team_name']} def. {loser['team_name']}, margin {abs(int(actual_margin_home))}"

    # Placeholder for AI summary
    context = "[AI summary will be generated here]"

    return f"{matchup} {dot}\n{score}\n\n{context}"


# --------------------------------------------------
# Main
# --------------------------------------------------

def main():
    df = pd.read_csv(INPUT_CSV)
    df["game_date"] = pd.to_datetime(df["game_date"]).dt.date

    yesterday = datetime.utcnow().date() - timedelta(days=1)
    games = df[df["game_date"] == yesterday]

    if games.empty:
        print("No games last night.")
        return

    print("\n=== POST-GAME THREAD ===\n")

    for game_id, g in games.groupby("game_id"):
        if len(g) != 2:
            continue

        home = g[g["home_away"] == "H"].iloc[0]
        away = g[g["home_away"] == "A"].iloc[0]

        print(format_postgame(home, away))
        print("\n" + "-" * 36 + "\n")


if __name__ == "__main__":
    main()
