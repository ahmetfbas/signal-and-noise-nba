import argparse
import os
import numpy as np
import pandas as pd

INPUT_CSV = "data/derived/team_game_metrics_with_rpmi_cvv.csv"
FACTS_CSV = "data/core/team_game_facts.csv"          # for historical matchups
OUT_CSV = "data/derived/game_environment_pregame_backtest.csv"

# thresholds (use your current ones)
CLEAN_THR = 0.25
NOISY_THR = 0.55

VOL_SCALE = 15.0
FATIGUE_LOW = 30.0
FATIGUE_HIGH = 80.0


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


def main(days: int):
    if not os.path.exists(INPUT_CSV):
        raise FileNotFoundError(INPUT_CSV)
    if not os.path.exists(FACTS_CSV):
        raise FileNotFoundError(FACTS_CSV)

    metrics = pd.read_csv(INPUT_CSV)
    facts = pd.read_csv(FACTS_CSV)

    metrics["game_date"] = pd.to_datetime(metrics["game_date"], errors="coerce").dt.date
    facts["game_date"] = pd.to_datetime(facts["game_date"], errors="coerce").dt.date

    facts = facts.dropna(subset=["game_date"]).copy()

    all_dates = sorted(facts["game_date"].unique())
    if not all_dates:
        raise RuntimeError("No dates in facts.")

    # pick last N dates
    test_dates = all_dates[-days:] if days > 0 else all_dates

    out_rows = []

    for run_date in test_dates:
        # pregame state strictly before run_date
        pre = metrics[metrics["game_date"] < run_date].copy()
        if pre.empty:
            continue

        latest = (
            pre.sort_values(["team_name", "game_date"])
               .groupby("team_name", as_index=False)
               .tail(1)
        )

        # reconstruct matchups for that date from facts (home/away)
        day = facts[facts["game_date"] == run_date].copy()
        if day.empty:
            continue

        # expect columns: home_away, team_name, opponent_name
        # build unique matchups from HOME rows
        home_rows = day[day["home_away"] == "H"].copy()
        if home_rows.empty:
            continue

        for _, g in home_rows.iterrows():
            home = g["team_name"]
            away = g["opponent_name"]

            h = latest[latest["team_name"] == home]
            a = latest[latest["team_name"] == away]
            if h.empty or a.empty:
                continue

            h = h.iloc[0]
            a = a.iloc[0]

            load_risk = max(norm_fatigue(h["fatigue_index"]), norm_fatigue(a["fatigue_index"]))
            behavior_risk = max(norm_volatility(h.get("pve_volatility")), norm_volatility(a.get("pve_volatility")))

            matchup_risk = safe_avg([
                norm_asym((h.get("fatigue_index") - a.get("fatigue_index")), 40.0),
                norm_asym((h.get("consistency") - a.get("consistency")), 0.30),
            ])

            risk_score = safe_avg([
                (0.45 * load_risk) if not pd.isna(load_risk) else np.nan,
                (0.35 * behavior_risk) if not pd.isna(behavior_risk) else np.nan,
                (0.20 * matchup_risk) if not pd.isna(matchup_risk) else np.nan,
            ])

            out_rows.append({
                "game_date": run_date,
                "matchup": f"{away} @ {home}",
                "environment_risk": None if pd.isna(risk_score) else round(risk_score, 3),
                "environment_label": classify_environment(risk_score),
                "drivers": build_drivers(load_risk, behavior_risk, matchup_risk),
                "load_risk": None if pd.isna(load_risk) else round(load_risk, 3),
                "behavior_risk": None if pd.isna(behavior_risk) else round(behavior_risk, 3),
                "matchup_risk": None if pd.isna(matchup_risk) else round(matchup_risk, 3),
            })

    out = pd.DataFrame(out_rows)
    out = out.sort_values(["game_date", "matchup"]).reset_index(drop=True)
    out.to_csv(OUT_CSV, index=False)

    print(f"✅ Wrote {len(out)} rows → {OUT_CSV}")
    if not out.empty:
        print("Label distribution:", out["environment_label"].value_counts().to_dict())
        print("Date range:", out["game_date"].min(), "→", out["game_date"].max())


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--days", type=int, default=60)
    args = ap.parse_args()
    main(args.days)
