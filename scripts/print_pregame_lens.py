import pandas as pd

from analysis.utils import season_record
from analysis.compose_tweet import compose_tweet
from analysis.summarize_pregame_ai import summarize_pregame_matchup


SCHEDULE_CSV = "data/derived/game_schedule_today.csv"
METRICS_CSV = "data/derived/team_game_metrics_with_rpmi_cvv.csv"
IDENTITY_CSV = "data/derived/team_game_metrics_with_archetypes.csv"
ENV_CSV = "data/derived/game_environment_pregame.csv"


# -------------------- SAFE HELPERS --------------------

def safe_metric(row, key, default=0.0):
    if row is None or key not in row:
        return default
    v = row[key]
    return v if pd.notna(v) else default


def clip01(x):
    return max(0.0, min(1.0, float(x))) if x is not None else 0.0


def to_minus1_plus1(x01):
    return clip01(x01) * 2.0 - 1.0


# -------------------- EMOJIS --------------------

def momentum_emoji(x):
    if x > 0.30:
        return "⬆️"
    if x < -0.30:
        return "⬇️"
    return "➡️"


def fatigue_emoji(f01):
    if f01 >= 0.70:
        return "🥵"
    if f01 >= 0.50:
        return "😓"
    if f01 >= 0.35:
        return "😐"
    return "💪"


def consistency_emoji(c):
    if c >= 0.65:
        return "🔒"
    if c >= 0.50:
        return "⚖️"
    if c >= 0.35:
        return "🌪️"
    return "💥"


def environment_emoji(label):
    return {
        "Clean": "🧊",
        "Mixed": "🌫️",
        "Noisy": "🧨",
    }.get(label, "🌫️")


# -------------------- DATA HELPERS --------------------

def latest_pregame_row(df, team_name, cutoff_date):
    t = df[
        (df["team_name"] == team_name)
        & (df["game_date"] < cutoff_date)
    ]
    if t.empty:
        return None
    return t.sort_values("game_date").iloc[-1]


def lookup_environment(env_df, away, home, game_date):
    if env_df.empty:
        return None

    env_df = env_df.copy()
    env_df["game_day"] = pd.to_datetime(env_df["game_date"]).dt.date

    row = env_df[
        (env_df["matchup"] == f"{away} @ {home}")
        & (env_df["game_day"] == game_date)
    ]

    return row.iloc[0] if not row.empty else None


# -------------------- FORMATTER --------------------

def format_pregame_lens(home, away, home_record, away_record, env_row, id_map):
    # Identity
    away_id = id_map.get(away["team_name"], "—")
    home_id = id_map.get(home["team_name"], "—")

    # Fatigue
    away_f = clip01(safe_metric(away, "fatigue_index") / 100.0)
    home_f = clip01(safe_metric(home, "fatigue_index") / 100.0)

    # Momentum
    away_m = to_minus1_plus1(
        (safe_metric(away, "rpmi_delta") + 10.0) / 20.0
    )
    home_m = to_minus1_plus1(
        (safe_metric(home, "rpmi_delta") + 10.0) / 20.0
    )

    # Consistency
    away_c = clip01(safe_metric(away, "consistency"))
    home_c = clip01(safe_metric(home, "consistency"))

    # Environment
    env_label = (
        env_row["environment_label"]
        if env_row is not None and pd.notna(env_row.get("environment_label"))
        else "Mixed"
    )
    env_icon = environment_emoji(env_label)

    # --------------------
    # Header
    # --------------------
    header = (
        f"🏀 Pregame Lens\n\n"
        f"{away['team_name']} ({away_record}) @ {home['team_name']} ({home_record})\n\n"
        f"Identity      {away_id} | {home_id}"
    )

    # --------------------
    # Metrics block
    # --------------------
    metrics = [
        f"Momentum      {away_m:+.2f} {momentum_emoji(away_m)} | {home_m:+.2f} {momentum_emoji(home_m)}",
        f"Fatigue       {away_f:.2f} {fatigue_emoji(away_f)} | {home_f:.2f} {fatigue_emoji(home_f)}",
        f"Consistency   {away_c:.2f} {consistency_emoji(away_c)} | {home_c:.2f} {consistency_emoji(home_c)}",
        f"Environment   {env_label} {env_icon}",
    ]

    body = (
        header
        + "\n\n"                 # ← ONE line break after Identity
        + "\n".join(metrics)     # ← Tight metric stack
        + "\n\n"                 # ← ONE line break before context hook
    )

    return body, {
        "identity": {"away": away_id, "home": home_id},
        "momentum": {"away": away_m, "home": home_m},
        "fatigue": {"away": away_f, "home": home_f},
        "consistency": {"away": away_c, "home": home_c},
        "environment": env_label,
    }


# -------------------- MAIN --------------------

def main():
    sched = pd.read_csv(SCHEDULE_CSV)
    metrics = pd.read_csv(METRICS_CSV)
    env = pd.read_csv(ENV_CSV)
    identity = pd.read_csv(IDENTITY_CSV)

    id_map = dict(zip(identity["team_name"], identity["archetype"]))

    sched["game_date"] = pd.to_datetime(sched["game_date"]).dt.date
    metrics["game_date"] = pd.to_datetime(metrics["game_date"]).dt.date
    env["game_date"] = pd.to_datetime(env["game_date"])

    run_date = sched["game_date"].max()
    print(f"📅 Using schedule for {run_date}\n")

    games_today = (
        sched[sched["game_date"] == run_date]
        .drop_duplicates(subset=["home_team_name", "away_team_name"])
    )

    for _, game in games_today.iterrows():
        home_name = game["home_team_name"]
        away_name = game["away_team_name"]

        home = latest_pregame_row(metrics, home_name, run_date)
        away = latest_pregame_row(metrics, away_name, run_date)

        if home is None or away is None:
            continue

        env_row = lookup_environment(env, away_name, home_name, run_date)

        home_w, home_l = season_record(metrics, home_name, run_date)
        away_w, away_l = season_record(metrics, away_name, run_date)

        text, ai_payload = format_pregame_lens(
            home,
            away,
            f"{home_w}-{home_l}",
            f"{away_w}-{away_l}",
            env_row,
            id_map,
        )

        tweet_main, _ = compose_tweet(
            board_name=f"{away_name} @ {home_name}",
            data=pd.DataFrame([home, away]),
            header=text,
            body_text=None,
            mode="pregame",
        )

        print(tweet_main)

        ai_text = summarize_pregame_matchup(
            matchup_name=f"{away_name} @ {home_name}",
            signals=ai_payload,
        )

        if ai_text:
            print(ai_text)

        print("\n" + "-" * 40 + "\n")


if __name__ == "__main__":
    main()
