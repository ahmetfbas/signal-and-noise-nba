import pandas as pd
from datetime import datetime, timedelta
from analysis.compose_tweet import compose_tweet


# --------------------------------------------------
# Paths
# --------------------------------------------------
METRICS_CSV = "data/derived/team_game_metrics_with_rpmi_cvv.csv"


# --------------------------------------------------
# Helpers
# --------------------------------------------------
def signal_dot(expected_margin_home, actual_margin_home):
    """
    Compare expected vs actual performance for quick visual signal.
    """
    if pd.isna(expected_margin_home) or pd.isna(actual_margin_home):
        return "🟡"

    aligned = expected_margin_home * actual_margin_home > 0
    if aligned:
        return "🟢"
    if abs(actual_margin_home) <= 4:
        return "🟡"
    return "🔴"


def format_postgame(home, away):
    matchup = f"{away['team_name']} @ {home['team_name']}"
    dot = signal_dot(
        home.get("expected_margin"),
        home.get("actual_margin"),
    )

    home_pts = int(home["team_points"])
    away_pts = int(home["opponent_points"])

    if home_pts > away_pts:
        scoreline = f"{home['team_name']} {home_pts} – {away_pts} {away['team_name']}"
    else:
        scoreline = f"{away['team_name']} {away_pts} – {home_pts} {home['team_name']}"

    # Matchup-level volatility
    vol_home = home.get("pve_volatility")
    vol_away = away.get("pve_volatility")
    vol_avg = (
        (vol_home + vol_away) / 2
        if pd.notna(vol_home) and pd.notna(vol_away)
        else None
    )

    volatility_label = (
        "high volatility game"
        if vol_avg is not None and vol_avg >= 0.65
        else "low volatility game"
        if vol_avg is not None and vol_avg <= 0.35
        else "medium volatility game"
    )

    # Momentum trend (home perspective)
    delta = home.get("rpmi_delta", 0.0)
    momentum_trend = (
        "momentum rising"
        if delta > 0.25
        else "momentum falling"
        if delta < -0.25
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
