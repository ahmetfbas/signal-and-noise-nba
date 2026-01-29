# scripts/print_pregame_lens.py
import pandas as pd
from datetime import datetime

SCHEDULE_CSV = "data/derived/game_schedule_today.csv"
METRICS_CSV = "data/derived/team_game_metrics_with_rpmi_cvv.csv"


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


def matchup_volatility_label(vol_home, vol_away):
    if pd.isna(vol_home) or pd.isna(vol_away):
        return "UNKNOWN"
    avg_vol = (vol_home + vol_away) / 2
    if avg_vol >= 0.65:
        return "HIGH"
    if avg_vol <= 0.35:
        return "LOW"
    return "MEDIUM"


def format_pregame_lens(home, away):
    matchup = f"{away['team_name']} @ {home['team_name']}"
    volatility = matchup_volatility_label(home["pve_volatility"], away["pve_volatility"])
    return (
        f"{matchup} — pregame lens\n\n"
        f"Momentum:      {momentum_emoji(away['rpmi_delta'])} {away['team_name']} | "
        f"{momentum_emoji(home['rpmi_delta'])} {home['team_name']}\n"
        f"Fatigue:       {fatigue_emoji(away['fatigue_index'])} {away['team_name']} | "
        f"{fatigue_emoji(home['fatigue_index'])} {home['team_name']}\n"
        f"Consistency:   {consistency_emoji(away['consistency'])} {away['team_name']} | "
        f"{consistency_emoji(home['consistency'])} {home['team_name']}\n"
        f"Volatility:    {volatility}"
    )


def main():
    sched = pd.read_csv(SCHEDULE_CSV)
    metrics = pd.read_csv(METRICS_CSV)
    metrics["game_date"] = pd.to_datetime(metrics["game_date"]).dt.date

    for _, game in sched.iterrows():
        home_name = game["home_team_name"]
        away_name = game["away_team_name"]

        home = metrics[metrics["team_name"] == home_name].sort_values("game_date").tail(1)
        away = metrics[metrics["team_name"] == away_name].sort_values("game_date").tail(1)

        if home.empty or away.empty:
            continue

        print(format_pregame_lens(home.iloc[0], away.iloc[0]))
        print("\n" + "-" * 40 + "\n")


if __name__ == "__main__":
    main()
