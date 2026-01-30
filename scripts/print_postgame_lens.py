# scripts/print_postgame_lens.py

import pandas as pd
from datetime import datetime, timedelta

# --------------------------------------------------
# Paths
# --------------------------------------------------
METRICS_CSV = "data/derived/team_game_metrics_with_rpmi_cvv.csv"
FACTS_CSV = "data/core/team_game_facts.csv"


# --------------------------------------------------
# Helpers
# --------------------------------------------------

def signal_dot(expected_margin_home, actual_margin_home):
    """Compare expected vs actual performance for quick visual signal."""
    if pd.isna(expected_margin_home) or pd.isna(actual_margin_home):
        return "🟡"  # unknown
    aligned = expected_margin_home * actual_margin_home > 0
    if aligned:
        return "🟢"  # met expectation
    if abs(actual_margin_home) <= 4:
        return "🟡"  # close game
    return "🔴"  # missed expectation


def format_postgame(home, away):
    matchup = f"{away['team_name']} @ {home['team_name']}"
    dot = signal_dot(home.get("expected_margin"), home.get("actual_margin"))

    # Use merged true scores
    home_pts = int(home.get("team_points", 0))
    away_pts = int(home.get("opponent_points", 0))

    # Winner / loser detection
    if home_pts > away_pts:
        winner, loser = home, away
        scoreline = f"{home['team_name']} {home_pts} – {away_pts} {away['team_name']}"
    else:
        winner, loser = away, home
        scoreline = f"{away['team_name']} {away_pts} – {home_pts} {home['team_name']}"

    # Volatility & momentum context
    volatility = home.get("pve_volatility", None)
    volatility_label = (
        "high volatility matchup"
        if pd.notna(volatility) and volatility >= 0.65
        else "low volatility game" if pd.notna(volatility) and volatility <= 0.35
        else "medium volatility"
    )

    momentum_trend = (
        "momentum rising" if home.get("rpmi_delta", 0) > 0.5 else
        "momentum falling" if home.get("rpmi_delta", 0) < -0.5 else
        "stable form"
    )

    context = (
        f"[AI summary placeholder — {winner['team_name']} maintained {momentum_trend}, "
        f"while {loser['team_name']} faced {volatility_label}.]"
    )

    return f"{matchup} {dot}\n{scoreline}\n\n{context}"


# --------------------------------------------------
# Main
# --------------------------------------------------

def main(target_date: str = None):
    # Load base metrics
    df = pd.read_csv(METRICS_CSV)
    df["game_date"] = pd.to_datetime(df["game_date"], errors="coerce").dt.date

    # Load real scores and merge
    facts = pd.read_csv(
        FACTS_CSV,
        usecols=["game_id", "team_id", "team_name", "team_points", "opponent_points"],
    )
    df = df.merge(facts, on=["game_id", "team_id", "team_name"], how="left")

    # Determine target date
    if target_date:
        target = datetime.strptime(target_date, "%Y-%m-%d").date()
    else:
        target = datetime.utcnow().date() - timedelta(days=1)

    games = df[df["game_date"] == target]

    if games.empty:
        print(f"No games found for {target}.")
        return

    print(f"\n=== POST-GAME THREAD ({target}) ===\n")

    for game_id, g in games.groupby("game_id"):
        if len(g) != 2:
            continue

        home = g[g["home_away"] == "H"].iloc[0]
        away = g[g["home_away"] == "A"].iloc[0]

        print(format_postgame(home, away))
        print("\n" + "-" * 36 + "\n")


if __name__ == "__main__":
    main()
