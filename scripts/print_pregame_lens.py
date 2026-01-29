import pandas as pd
from datetime import datetime

INPUT_CSV = "data/derived/team_game_metrics.csv"


# --------------------------------------------------
# Emoji helpers
# --------------------------------------------------

def momentum_emoji(delta):
    if pd.isna(delta):
        return "—"
    if delta > 0.5:
        return "⬆️"
    if delta < -0.5:
        return "⬇️"
    return "➡️"


def fatigue_emoji(f):
    if pd.isna(f):
        return "—"
    if f >= 65:
        return "🔴"
    if f <= 40:
        return "🟢"
    return "🟡"


def consistency_emoji(c):
    if pd.isna(c):
        return "—"
    if c >= 0.65:
        return "🟢"
    if c <= 0.40:
        return "⚠️"
    return "🟡"


# --------------------------------------------------
# Matchup volatility (V1: label only)
# --------------------------------------------------

def matchup_volatility_label(vol_home, vol_away):
    if pd.isna(vol_home) or pd.isna(vol_away):
        return "UNKNOWN"

    avg_vol = (vol_home + vol_away) / 2

    if avg_vol >= 0.65:
        return "HIGH"
    if avg_vol <= 0.35:
        return "LOW"
    return "MEDIUM"


# --------------------------------------------------
# Formatter
# --------------------------------------------------

def format_pregame_lens(home, away):
    matchup = f"{away['team_name'][:3]} @ {home['team_name'][:3]}"

    volatility = matchup_volatility_label(
        home["pve_volatility"],
        away["pve_volatility"]
    )

    return (
        f"{matchup} — pregame lens\n\n"
        f"Momentum:      {momentum_emoji(away['rpmi_delta'])} {away['team_name'][:3]} | "
        f"{momentum_emoji(home['rpmi_delta'])} {home['team_name'][:3]}\n"
        f"Fatigue:       {fatigue_emoji(away['fatigue_index'])} {away['team_name'][:3]} | "
        f"{fatigue_emoji(home['fatigue_index'])} {home['team_name'][:3]}\n"
        f"Consistency:   {consistency_emoji(away['consistency'])} {away['team_name'][:3]} | "
        f"{consistency_emoji(home['consistency'])} {home['team_name'][:3]}\n"
        f"Volatility:    {volatility}"
    )


# --------------------------------------------------
# Main
# --------------------------------------------------

def main():
    df = pd.read_csv(INPUT_CSV)
    df["game_date"] = pd.to_datetime(df["game_date"]).dt.date

    today = datetime.utcnow().date()
    games_today = df[df["game_date"] == today]

    for game_id, g in games_today.groupby("game_id"):
        if len(g) != 2:
            continue

        home = g[g["home_away"] == "H"].iloc[0]
        away = g[g["home_away"] == "A"].iloc[0]

        print(format_pregame_lens(home, away))
        print("\n" + "-" * 40 + "\n")


if __name__ == "__main__":
    main()
