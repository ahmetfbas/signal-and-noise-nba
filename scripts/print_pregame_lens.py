import pandas as pd
from datetime import date
from analysis.utils import season_record
from analysis.compose_tweet import compose_tweet


SCHEDULE_CSV = "data/derived/game_schedule_today.csv"
METRICS_CSV = "data/derived/team_game_metrics_with_rpmi_cvv.csv"


# -------------------- SAFE HELPERS --------------------

def safe_metric(row, key, default=0.0):
    if row is None or key not in row:
        return default
    val = row[key]
    return val if pd.notna(val) else default


def clip01(x: float) -> float:
    if x is None:
        return 0.0
    return max(0.0, min(1.0, float(x)))


def to_minus1_plus1(x01: float) -> float:
    return clip01(x01) * 2.0 - 1.0


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


# -------------------- DATA HELPERS --------------------

def latest_valid_row(df, team_name):
    team_df = df[df["team_name"] == team_name]
    if team_df.empty:
        return team_df
    return team_df.sort_values("game_date").tail(1)


def format_pregame_lens(home, away, home_record, away_record):
    # Fatigue (0–1)
    away_fatigue = clip01(safe_metric(away, "fatigue_index") / 100.0)
    home_fatigue = clip01(safe_metric(home, "fatigue_index") / 100.0)

    # Momentum (-1..1) from rpmi_delta (~ -10..+10)
    away_momentum = to_minus1_plus1(
        clip01((safe_metric(away, "rpmi_delta") + 10.0) / 20.0)
    )
    home_momentum = to_minus1_plus1(
        clip01((safe_metric(home, "rpmi_delta") + 10.0) / 20.0)
    )

    # Consistency already 0–1
    away_consistency = clip01(safe_metric(away, "consistency"))
    home_consistency = clip01(safe_metric(home, "consistency"))

    vol_label = matchup_volatility_label(
        safe_metric(home, "pve_volatility"),
        safe_metric(away, "pve_volatility"),
    )

    home_team = str(home["team_name"])
    away_team = str(away["team_name"])

    header = f"{away_team} ({away_record}) @ {home_team} ({home_record})"

    lines = [
        f"Momentum: {away_momentum:+.2f} {momentum_emoji(away_momentum)} {away_team} | "
        f"{home_momentum:+.2f} {momentum_emoji(home_momentum)} {home_team}",
        f"Fatigue: {away_fatigue:.2f} {fatigue_emoji(away_fatigue)} {away_team} | "
        f"{home_fatigue:.2f} {fatigue_emoji(home_fatigue)} {home_team}",
        f"Consistency: {away_consistency:.2f} {consistency_emoji(away_consistency)} {away_team} | "
        f"{home_consistency:.2f} {consistency_emoji(home_consistency)} {home_team}",
        f"Volatility: {vol_label}",
    ]

    return header + "\n" + "\n".join(lines)


# -------------------- MAIN --------------------

def main():
    sched = pd.read_csv(SCHEDULE_CSV)
    metrics = pd.read_csv(METRICS_CSV)

    sched["game_date"] = pd.to_datetime(sched["game_date"], errors="coerce").dt.date
    metrics["game_date"] = pd.to_datetime(metrics["game_date"], errors="coerce").dt.date

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
