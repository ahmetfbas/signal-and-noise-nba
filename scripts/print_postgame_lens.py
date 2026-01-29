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


def volatility_phrase(vol):
    if pd.isna(vol):
        return None
    if vol >= 0.65:
        return "volatility took over"
    if vol <= 0.35:
        return "conditions stayed controlled"
    return None


# --------------------------------------------------
# Context writer
# --------------------------------------------------

def write_context(home, away):
    actual_margin = home["team_points"] - away["team_points"]
    expected_margin = home["expected_margin"]

    winner = home if actual_margin > 0 else away
    loser = away if actual_margin > 0 else home

    lines = []

    # Alignment
    if not pd.isna(expected_margin) and actual_margin * expected_margin > 0:
        lines.append(
            f"The setup leaned {winner['team_name']}, and the result followed."
        )
    else:
        lines.append(
            "The pregame edge pointed elsewhere, but the game bent off script."
        )

    # Fatigue
    if winner["fatigue_index"] < loser["fatigue_index"]:
        lines.append(
            f"They entered fresher and converted that edge."
        )
    else:
        lines.append(
            f"They pushed through fatigue and found enough execution."
        )

    # Volatility
    vol = (winner["pve_volatility"] + loser["pve_volatility"]) / 2
    v_phrase = volatility_phrase(vol)
    if v_phrase:
        lines.append(v_phrase.capitalize() + ".")

    return "\n".join(lines)


# --------------------------------------------------
# Formatter
# --------------------------------------------------

def format_postgame(home, away):
    matchup = f"{away['team_name'][:3]} @ {home['team_name'][:3]}"

    actual_margin_home = home["team_points"] - away["team_points"]
    dot = signal_dot(home["expected_margin"], actual_margin_home)

    winner = home if actual_margin_home > 0 else away
    loser = away if actual_margin_home > 0 else home

    header = f"{matchup} {dot}"
    score = f"{winner['team_name'][:3]} def. {loser['team_name'][:3]}, {winner['team_points']}–{loser['team_points']}"

    context = write_context(home, away)

    return f"{header}\n{score}\n\n{context}"


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
