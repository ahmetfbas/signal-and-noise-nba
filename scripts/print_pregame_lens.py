import pandas as pd
from datetime import datetime, timedelta
from analysis.utils import season_record
from analysis.compose_tweet import compose_tweet


SCHEDULE_CSV = "data/derived/game_schedule_today.csv"
METRICS_CSV = "data/derived/team_game_metrics.csv"


def safe_metric(row, key, default=0.0):
    if row is None:
        return default
    if key not in row:
        return default
    val = row[key]
    return val if pd.notna(val) else default


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
        return "😓"
    if f <= 40:
        return "💪"
    return "😐"


def consistency_emoji(c):
    if pd.isna(c):
        return "—"
    if c >= 0.65:
        return "🔒"
    if c >= 0.50:
        return "⚖️"
    if c >= 0.35:
        return "🌪️"
    return "💥"


def matchup_volatility_label(vol_home, vol_away):
    if pd.isna(vol_home) or pd.isna(vol_away):
        return "UNKNOWN"
    avg_vol = (vol_home + vol_away) / 2
    if avg_vol >= 0.65:
        return "HIGH"
    if avg_vol <= 0.35:
        return "LOW"
    return "MEDIUM"


def latest_valid_row(df, team_name):
    team_df = df[df["team_name"] == team_name].copy()
    if team_df.empty:
        return team_df
    team_df = team_df.sort_values("game_date")
    return team_df.tail(1)


def format_pregame_lens(home, away, home_record, away_record):
    header = f"🏀 {away['team_name']} ({away_record}) @ {home['team_name']} ({home_record})"
    lines = [
        f"Momentum: {momentum_emoji(safe_metric(away, 'rpmi_delta'))} {away['team_name']} | {momentum_emoji(safe_metric(home, 'rpmi_delta'))} {home['team_name']}",
        f"Fatigue: {fatigue_emoji(safe_metric(away, 'fatigue_index'))} {away['team_name']} | {fatigue_emoji(safe_metric(home, 'fatigue_index'))} {home['team_name']}",
        f"Consistency: {consistency_emoji(safe_metric(away, 'consistency'))} {away['team_name']} | {consistency_emoji(safe_metric(home, 'consistency'))} {home['team_name']}",
        f"Volatility: {matchup_volatility_label(safe_metric(home, 'pve_volatility'), safe_metric(away, 'pve_volatility'))}",
    ]
    return header + "\n" + "\n".join(lines)


def main():
    sched = pd.read_csv(SCHEDULE_CSV)
    metrics = pd.read_csv(METRICS_CSV)

    sched["game_date"] = pd.to_datetime(sched["game_date"], errors="coerce").dt.date
    metrics["game_date"] = pd.to_datetime(metrics["game_date"], errors="coerce").dt.date

    name_map = {
        "Hawks": "Atlanta Hawks",
        "Celtics": "Boston Celtics",
        "Nets": "Brooklyn Nets",
        "Hornets": "Charlotte Hornets",
        "Bulls": "Chicago Bulls",
        "Cavaliers": "Cleveland Cavaliers",
        "Mavericks": "Dallas Mavericks",
        "Nuggets": "Denver Nuggets",
        "Pistons": "Detroit Pistons",
        "Warriors": "Golden State Warriors",
        "Rockets": "Houston Rockets",
        "Pacers": "Indiana Pacers",
        "Clippers": "Los Angeles Clippers",
        "Lakers": "Los Angeles Lakers",
        "Grizzlies": "Memphis Grizzlies",
        "Heat": "Miami Heat",
        "Bucks": "Milwaukee Bucks",
        "Timberwolves": "Minnesota Timberwolves",
        "Pelicans": "New Orleans Pelicans",
        "Knicks": "New York Knicks",
        "Thunder": "Oklahoma City Thunder",
        "Magic": "Orlando Magic",
        "76ers": "Philadelphia 76ers",
        "Suns": "Phoenix Suns",
        "Trail Blazers": "Portland Trail Blazers",
        "Kings": "Sacramento Kings",
        "Spurs": "San Antonio Spurs",
        "Raptors": "Toronto Raptors",
        "Jazz": "Utah Jazz",
        "Wizards": "Washington Wizards",
    }

    sched["home_team_name"] = sched["home_team_name"].replace(name_map)
    sched["away_team_name"] = sched["away_team_name"].replace(name_map)

    run_date = sched["game_date"].max()
    cutoff = run_date
    print(f"📅 Using schedule for {run_date}\n")

    for _, game in sched.iterrows():
        home_name = game["home_team_name"]
        away_name = game["away_team_name"]

        home_df = latest_valid_row(metrics, home_name)
        away_df = latest_valid_row(metrics, away_name)

        if home_df.empty or away_df.empty:
            print(f"⚠️ Missing metrics for {away_name} @ {home_name}")
            continue

        home = home_df.iloc[0]
        away = away_df.iloc[0]

        home_w, home_l = season_record(metrics, home["team_name"], cutoff)
        away_w, away_l = season_record(metrics, away["team_name"], cutoff)

        base_text = format_pregame_lens(
            home,
            away,
            f"{home_w}-{home_l}",
            f"{away_w}-{away_l}",
        )

        tweet_main, tweet_ai = compose_tweet(
            board_name=f"{away['team_name']} @ {home['team_name']}",
            data=pd.DataFrame([home, away]),
            header=base_text,
            body_text=None,
            mode="pregame",
        )

        print(tweet_main)
        print("\n↳", tweet_ai)
        print("\n" + "-" * 40 + "\n")


if __name__ == "__main__":
    main()
