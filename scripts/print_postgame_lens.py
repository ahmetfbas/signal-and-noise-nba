import pandas as pd
from datetime import datetime, timedelta
from analysis.compose_tweet import compose_tweet


# --------------------------------------------------
# Paths
# --------------------------------------------------
METRICS_CSV = "data/derived/team_game_metrics_with_pve.csv"
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

    home_pts = int(home.get("team_points", 0))
    away_pts = int(home.get("opponent_points", 0))

    if home_pts > away_pts:
        winner, loser = home, away
        scoreline = f"{home['team_name']} {home_pts} – {away_pts} {away['team_name']}"
    else:
        winner, loser = away, home
        scoreline = f"{away['team_name']} {away_pts} – {home_pts} {home['team_name']}"

    volatility = home.get("pve_volatility", None)
    volatility_label = (
        "high volatility matchup"
        if pd.notna(volatility) and volatility >= 0.65
        else "low volatility game"
        if pd.notna(volatility) and volatility <= 0.35
        else "medium volatility"
    )

    momentum_trend = (
        "momentum rising"
        if home.get("rpmi_delta", 0) > 0.5
        else "momentum falling"
        if home.get("rpmi_delta", 0) < -0.5
        else "stable form"
    )

    header = f"{matchup} {dot}\n{scoreline}"
    body_text = f"Volatility: {volatility_label.capitalize()} | Trend: {momentum_trend.capitalize()}"

    return header, body_text


# --------------------------------------------------
# Main
# --------------------------------------------------
def main(target_date: str = None):
    df = pd.read_csv(METRICS_CSV)
    df["game_date"] = pd.to_datetime(df["game_date"], errors="coerce").dt.date

    facts = pd.read_csv(
        FACTS_CSV,
        usecols=["game_id", "team_id", "team_name", "team_points", "opponent_points"],
    )
    df = df.merge(facts, on=["game_id", "team_id", "team_name"], how="left")

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

        header, body_text = format_postgame(home, away)

        # Combine into threaded tweet
        tweet_main, tweet_ai = compose_tweet(
            board_name=f"{away['team_name']} @ {home['team_name']}",
            data=pd.DataFrame([home, away]),
            header=header,
            body_text=body_text,
            mode="postgame",
        )

        print(tweet_main)
        print(f"\n↳ {tweet_ai}\n")
        print("-" * 40 + "\n")


if __name__ == "__main__":
    main()
