import pandas as pd
from datetime import datetime, timedelta
from analysis.utils import season_record
from analysis.compose_tweet import compose_tweet
from analysis.normalization import clip01, to_minus1_plus1


SCHEDULE_CSV = "data/derived/game_schedule_today.csv"
METRICS_CSV = "data/derived/team_game_metrics.csv"


def safe_metric(row, key, default=0.0):
    if row is None:
        return default
    if key not in row:
        return default
    val = row[key]
    return val if pd.notna(val) else default


# -------------------- EMOJI MAPPERS --------------------

def momentum_emoji(delta):
    if pd.isna(delta):
        return "—"
    if delta > 0.3:
        return "⬆️"
    if delta < -0.3:
        return "⬇️"
    return "➡️"


def fatigue_emoji(f):
    if pd.isna(f):
        return "—"
    if f >= 0.7:
        return "😓"
    if f <= 0.4:
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


# -------------------- HELPERS --------------------

def latest_valid_row(df, team_name):
    team_df = df[df["team_name"] == team_name].copy()
    if team_df.empty:
        return team_df
    team_df = team_df.sort_values("game_date")
    return team_df.tail(1)


def format_pregame_lens(home, away, home_record, away_record):
    # normalize + attach emojis + numbers
    away_fatigue = clip01(safe_metric(away, "fatigue_index") / 100.0)
    home_fatigue = clip01(safe_metric(home, "fatigue_index") / 100.0)

    away_momentum = to_minus1_plus1(clip01((safe_metric(away, "rpmi_delta") + 5.0) / 10.0))
    home_momentum = to_minus1_plus1(clip01((safe_metric(home, "rpmi_delta") + 5.0) / 10.0))

    away_consistency_val = safe_metric(away, "consistency")
    home_consistency_val = safe_metric(home, "consistency")

    away_consistency = clip01(away_consistency_val if pd.notna(away_consistency_val) else 0)
    home_consistency = clip01(home_consistency_val if pd.notna(home_consistency_val) else 0)

    vol_label = matchup_volatility_label(
        safe_metric(home, "pve_volatility"),
        safe_metric(away, "pve_volatility"),
    )

    # Ensure string team names (avoid NaN truncation)
    home_team = str(home.get("team_name", "Unknown"))
    away_team = str(away.get("team_name", "Unknown"))

    header = f"🏀 🏀 {away_team} ({away_record}) @ {home_team} ({home_record})"

    lines = [
        f"Momentum: {away_momentum:+.2f} {momentum_emoji(away_momentum)} {away_team} | {home_momentum:+.2f} {momentum_emoji(home_momentum)} {home_team}",
        f"Fatigue: {away_fatigue:.2f} {fatigue_emoji(away_fatigue)} {away_team} | {home_fatigue:.2f} {fatigue_emoji(home_fatigue)} {home_team}",
        f"Consistency: {away_consistency:.2f} {consistency_emoji(away_consistency)} {away_team} | {home_consistency:.2f} {consistency_emoji(home_consistency)} {home_team}",
        f"Volatility: {vol_label}",
    ]

    return header + "\n" + "\n".join(lines)

# -------------------- MAIN --------------------

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
