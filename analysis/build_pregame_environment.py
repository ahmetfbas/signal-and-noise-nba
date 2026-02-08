import os
import numpy as np
import pandas as pd

INPUT_CSV = "data/derived/team_game_metrics_with_rpmi_cvv.csv"
SCHEDULE_CSV = "data/derived/game_schedule_today.csv"
OUTPUT_CSV = "data/derived/game_environment_pregame.csv"

# --------------------------------------------------
# Thresholds
# --------------------------------------------------
CLEAN_THR = 0.25
NOISY_THR = 0.55

VOL_SCALE = 15.0
FATIGUE_LOW = 30.0
FATIGUE_HIGH = 80.0


# --------------------------------------------------
# Helpers
# --------------------------------------------------
def clip01(x):
    return float(np.clip(x, 0.0, 1.0))


def safe_avg(vals):
    v = [x for x in vals if not pd.isna(x)]
    return np.nan if not v else float(np.mean(v))


def norm_fatigue(f):
    if pd.isna(f):
        return np.nan
    return clip01((float(f) - FATIGUE_LOW) / (FATIGUE_HIGH - FATIGUE_LOW))


def norm_volatility(v):
    if pd.isna(v):
        return np.nan
    return clip01(float(v) / VOL_SCALE)


def norm_asym(x, scale):
    if pd.isna(x):
        return np.nan
    return clip01(abs(float(x)) / scale)


def classify_environment(score):
    if pd.isna(score):
        return "—"
    if score <= CLEAN_THR:
        return "Clean"
    if score >= NOISY_THR:
        return "Noisy"
    return "Mixed"


def build_drivers(load_risk, behavior_risk, matchup_risk):
    drivers = []
    if not pd.isna(load_risk) and load_risk >= 0.60:
        drivers.append("fatigue load")
    if not pd.isna(behavior_risk) and behavior_risk >= 0.60:
        drivers.append("volatile teams")
    if not pd.isna(matchup_risk) and matchup_risk >= 0.60:
        drivers.append("mismatch")
    return ", ".join(drivers) if drivers else "stable conditions"


# --------------------------------------------------
# Main
# --------------------------------------------------
def main():
    if not os.path.exists(INPUT_CSV):
        raise FileNotFoundError("Metrics CSV missing")
    if not os.path.exists(SCHEDULE_CSV):
        raise FileNotFoundError("Schedule CSV missing")

    metrics = pd.read_csv(INPUT_CSV)
    sched = pd.read_csv(SCHEDULE_CSV)

    metrics["game_date"] = pd.to_datetime(metrics["game_date"], errors="coerce").dt.date
    sched["game_date"] = pd.to_datetime(sched["game_date"], errors="coerce").dt.date

    run_date = sched["game_date"].max()

    # ✅ pregame state must be strictly BEFORE run_date
    pre = metrics[metrics["game_date"] < run_date].copy()
    if pre.empty:
        raise RuntimeError(f"No pregame metrics found before {run_date}.")

    latest = (
        pre.sort_values(["team_name", "game_date"])
           .groupby("team_name", as_index=False)
           .tail(1)
    )

    # ✅ schedule often has 2 rows per game; keep unique matchups
    games_today = (
        sched[sched["game_date"] == run_date]
        .drop_duplicates(subset=["home_team_name", "away_team_name"])
        .copy()
    )

    rows = []
    for _, g in games_today.iterrows():
        home = g["home_team_name"]
        away = g["away_team_name"]

        h = latest[latest["team_name"] == home]
        a = latest[latest["team_name"] == away]
        if h.empty or a.empty:
            continue

        h = h.iloc[0]
        a = a.iloc[0]

        load_risk = np.nanmax([
            norm_fatigue(h["fatigue_index"]),
            norm_fatigue(a["fatigue_index"]),
        ])

        behavior_risk = np.nanmax([
            norm_volatility(h.get("pve_volatility")),
            norm_volatility(a.get("pve_volatility")),
        ])

        matchup_risk = safe_avg([
            norm_asym((h.get("fatigue_index") - a.get("fatigue_index")), 40.0),
            norm_asym((h.get("consistency") - a.get("consistency")), 0.30),
        ])

        risk_score = safe_avg([
            (0.45 * load_risk) if not pd.isna(load_risk) else np.nan,
            (0.35 * behavior_risk) if not pd.isna(behavior_risk) else np.nan,
            (0.20 * matchup_risk) if not pd.isna(matchup_risk) else np.nan,
        ])

        rows.append({
            "game_date": run_date,
            "matchup": f"{away} @ {home}",
            "environment_risk": None if pd.isna(risk_score) else round(risk_score, 3),
            "environment_label": classify_environment(risk_score),
            "drivers": build_drivers(load_risk, behavior_risk, matchup_risk),
            "load_risk": None if pd.isna(load_risk) else round(load_risk, 3),
            "behavior_risk": None if pd.isna(behavior_risk) else round(behavior_risk, 3),
            "matchup_risk": None if pd.isna(matchup_risk) else round(matchup_risk, 3),
        })

    out = pd.DataFrame(rows).sort_values(["game_date", "matchup"])
    out.to_csv(OUTPUT_CSV, index=False)

    print(f"✅ Wrote {len(out)} rows → {OUTPUT_CSV}")
    print(f"Run date: {run_date}")
    if not out.empty:
        print("Labels:", out["environment_label"].value_counts().to_dict())


if __name__ == "__main__":
    main()
