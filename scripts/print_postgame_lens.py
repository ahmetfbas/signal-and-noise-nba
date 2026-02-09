import pandas as pd
from datetime import datetime, timedelta
from analysis.compose_tweet import compose_tweet


# --------------------------------------------------
# Paths
# --------------------------------------------------
FACTS_CSV = "data/core/team_game_facts.csv"
METRICS_CSV = "data/derived/team_game_metrics_with_rpmi_cvv.csv"


# --------------------------------------------------
# Thresholds (tightened & intentional)
# --------------------------------------------------
FATIGUE_GAP = 0.12
MOMENTUM_GAP = 0.35
CONSISTENCY_GAP = 0.18


# --------------------------------------------------
# Helpers
# --------------------------------------------------
def favorite_team(home_sig, away_sig):
    """Favorite based on season win rate."""
    if home_sig.get("win_rate", 0) > away_sig.get("win_rate", 0):
        return "home"
    if away_sig.get("win_rate", 0) > home_sig.get("win_rate", 0):
        return "away"
    return None


def asymmetry(metric_home, metric_away, threshold, lower_is_better=False):
    """
    Returns 'home', 'away', or None.
    """
    if pd.isna(metric_home) or pd.isna(metric_away):
        return None

    diff = metric_home - metric_away
    if abs(diff) < threshold:
        return None

    if lower_is_better:
        return "home" if diff < 0 else "away"
    return "home" if diff > 0 else "away"


def evaluate_pregame_signals(home_facts, away_facts, home_sig, away_sig):
    """
    Structured evaluation passed to AI.
    AI is NOT allowed to invent anything outside this object.
    """

    home_pts = home_facts["team_points"]
    away_pts = away_facts["team_points"]
    winner = "home" if home_pts > away_pts else "away"

    evaluation = {
        "winner": winner,
        "fatigue": {},
        "momentum": {},
        "consistency": {},
        "favorite": {},
    }

    # --- Fatigue ---
    f_home = home_sig.get("fatigue_index")
    f_away = away_sig.get("fatigue_index")
    f_edge = asymmetry(f_home, f_away, FATIGUE_GAP, lower_is_better=True)

    evaluation["fatigue"] = {
        "edge": f_edge,
        "aligned": f_edge == winner if f_edge else None,
        "home": f_home,
        "away": f_away,
    }

    # --- Momentum ---
    m_home = home_sig.get("rpmi_delta")
    m_away = away_sig.get("rpmi_delta")
    m_edge = asymmetry(m_home, m_away, MOMENTUM_GAP)

    evaluation["momentum"] = {
        "edge": m_edge,
        "aligned": m_edge == winner if m_edge else None,
        "home": m_home,
        "away": m_away,
    }

    # --- Consistency ---
    c_home = home_sig.get("consistency")
    c_away = away_sig.get("consistency")
    c_edge = asymmetry(c_home, c_away, CONSISTENCY_GAP)

    evaluation["consistency"] = {
        "edge": c_edge,
        "aligned": c_edge == winner if c_edge else None,
        "home": c_home,
        "away": c_away,
    }

    # --- Favorite ---
    fav = favorite_team(home_sig, away_sig)
    evaluation["favorite"] = {
        "side": fav,
        "aligned": fav == winner if fav else None,
    }

    return evaluation


def format_postgame(home_facts, away_facts):
    matchup = f"{away_facts['team_name']} @ {home_facts['team_name']}"

    home_pts = int(home_facts["team_points"])
    away_pts = int(away_facts["team_points"])

    if home_pts > away_pts:
        scoreline = (
            f"{home_facts['team_name']} {home_pts} – "
            f"{away_pts} {away_facts['team_name']}"
        )
    else:
        scoreline = (
            f"{away_facts['team_name']} {away_pts} – "
            f"{home_pts} {home_facts['team_name']}"
        )

    header = f"{matchup}\n{scoreline}"
    return header


# --------------------------------------------------
# Main
# --------------------------------------------------
def main(target_date: str = None):
    facts = pd.read_csv(FACTS_CSV)
    metrics = pd.read_csv(METRICS_CSV)

    facts["game_date"] = pd.to_datetime(facts["game_date"]).dt.date
    metrics["game_date"] = pd.to_datetime(metrics["game_date"]).dt.date

    if target_date:
        target = datetime.strptime(target_date, "%Y-%m-%d").date()
    else:
        target = datetime.utcnow().date() - timedelta(days=1)

    games = facts[facts["game_date"] == target]

    if games.empty:
        print(f"No games found for {target}.")
        return

    print(f"\n=== POST-GAME THREAD ({target}) ===\n")

    for game_id, g in games.groupby("game_id"):
        if len(g) != 2:
            continue

        home_facts = g[g["home_away"] == "H"].iloc[0]
        away_facts = g[g["home_away"] == "A"].iloc[0]

        home_sig = metrics[
            (metrics["game_id"] == game_id)
            & (metrics["team_id"] == home_facts["team_id"])
        ]
        away_sig = metrics[
            (metrics["game_id"] == game_id)
            & (metrics["team_id"] == away_facts["team_id"])
        ]

        if home_sig.empty or away_sig.empty:
            continue

        home_sig = home_sig.iloc[0]
        away_sig = away_sig.iloc[0]

        evaluation = evaluate_pregame_signals(
            home_facts, away_facts, home_sig, away_sig
        )

        header = format_postgame(home_facts, away_facts)

        tweet_main, _ = compose_tweet(
            board_name=f"{away_facts['team_name']} @ {home_facts['team_name']}",
            data=evaluation,
            header=header,
            body_text=None,
            mode="postgame",
        )

        print(tweet_main)
        print("\n" + "-" * 40 + "\n")


if __name__ == "__main__":
    main()
