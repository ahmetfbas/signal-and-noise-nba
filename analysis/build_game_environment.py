import pandas as pd
import numpy as np
import os

INPUT_CSV = "data/derived/team_game_metrics_with_rpmi_cvv.csv"
FACTS_CSV = "data/core/team_game_facts.csv"
OUTPUT_CSV = "data/derived/game_environment.csv"

# --------------------------------------------------
# Configuration (aligned with CVV / FLI)
# --------------------------------------------------

CLEAN_THR = 0.35
NOISY_THR = 0.65
MIN_GAMES_FOR_MATURE = 10

VOL_SCALE = 15.0      # aligned with CVV
FATIGUE_LOW = 30.0
FATIGUE_HIGH = 80.0


# --------------------------------------------------
# Normalization helpers
# --------------------------------------------------

def clip01(x):
    return float(np.clip(x, 0.0, 1.0))


def norm_fatigue(f):
    if pd.isna(f):
        return np.nan
    return clip01((float(f) - FATIGUE_LOW) / (FATIGUE_HIGH - FATIGUE_LOW))


def norm_volatility(vol):
    if pd.isna(vol):
        return np.nan
    return clip01(float(vol) / VOL_SCALE)


def norm_asym(x, scale):
    if pd.isna(x):
        return np.nan
    return clip01(abs(float(x)) / scale)


def safe_avg(values):
    vals = [v for v in values if not pd.isna(v)]
    return np.nan if not vals else float(np.mean(vals))


# --------------------------------------------------
# Classification logic
# --------------------------------------------------

def classify_environment(risk_score, maturity_ok):
    if not maturity_ok or pd.isna(risk_score):
        return "Forming"
    if risk_score <= CLEAN_THR:
        return "Clean"
    if risk_score >= NOISY_THR:
        return "Noisy"
    return "Mixed"


def build_drivers(load_risk, behavior_risk, matchup_risk, maturity_ok):
    if not maturity_ok:
        return "early-season/low-history"

    drivers = []
    if load_risk >= 0.60:
        drivers.append("fatigue load")
    if behavior_risk >= 0.60:
        drivers.append("volatile teams")
    if matchup_risk >= 0.60:
        drivers.append("stability mismatch")

    return ", ".join(drivers) if drivers else "stable conditions"


# --------------------------------------------------
# Main builder
# --------------------------------------------------

def main():
    if not os.path.exists(INPUT_CSV):
        raise FileNotFoundError("CVV output missing — game environment cannot run.")

    if not os.path.exists(FACTS_CSV):
        raise FileNotFoundError("Facts CSV missing — maturity check impossible.")

    df = pd.read_csv(INPUT_CSV)
    facts = pd.read_csv(FACTS_CSV)

    df["game_date"] = pd.to_datetime(df["game_date"], utc=True)
    facts["game_date"] = pd.to_datetime(facts["game_date"], utc=True)

    valid_games = df.groupby("game_id").size()
    df = df[df["game_id"].isin(valid_games[valid_games == 2].index)].copy()

    rows = []

    for game_id, g in df.groupby("game_id"):
        home = g[g["home_away"] == "H"].iloc[0]
        away = g[g["home_away"] == "A"].iloc[0]

        # -----------------------------
        # Maturity check
        # -----------------------------
        gp_home = facts[
            (facts["team_id"] == home["team_id"])
            & (facts["game_date"] < home["game_date"])
        ].shape[0]

        gp_away = facts[
            (facts["team_id"] == away["team_id"])
            & (facts["game_date"] < away["game_date"])
        ].shape[0]

        maturity_ok = gp_home >= MIN_GAMES_FOR_MATURE and gp_away >= MIN_GAMES_FOR_MATURE

        # -----------------------------
        # Load risk (fatigue)
        # -----------------------------
        f_home = norm_fatigue(home["fatigue_index"])
        f_away = norm_fatigue(away["fatigue_index"])
        load_risk = safe_avg([f_home, f_away])

        # -----------------------------
        # Behavior risk (volatility)
        # -----------------------------
        v_home = norm_volatility(home.get("pve_volatility"))
        v_away = norm_volatility(away.get("pve_volatility"))
        behavior_risk = safe_avg([v_home, v_away])

        # -----------------------------
        # Matchup risk (asymmetry)
        # -----------------------------
        asym_f = norm_asym(home["fatigue_index"] - away["fatigue_index"], 40.0)
        asym_c = norm_asym(home.get("consistency") - away.get("consistency"), 0.30)
        matchup_risk = safe_avg([asym_f, asym_c])

        # -----------------------------
        # Overall environment risk
        # -----------------------------
        risk_score = safe_avg([
            0.45 * load_risk if not pd.isna(load_risk) else np.nan,
            0.35 * behavior_risk if not pd.isna(behavior_risk) else np.nan,
            0.20 * matchup_risk if not pd.isna(matchup_risk) else np.nan,
        ])

        rows.append({
            "game_id": game_id,
            "game_date": home["game_date"],
            "matchup": f"{away['team_name']} @ {home['team_name']}",

            "environment_risk": None if pd.isna(risk_score) else round(risk_score, 3),
            "environment_label": classify_environment(risk_score, maturity_ok),
            "drivers": build_drivers(load_risk, behavior_risk, matchup_risk, maturity_ok),

            "load_risk": None if pd.isna(load_risk) else round(load_risk, 3),
            "behavior_risk": None if pd.isna(behavior_risk) else round(behavior_risk, 3),
            "matchup_risk": None if pd.isna(matchup_risk) else round(matchup_risk, 3),

            "fatigue_home": home["fatigue_index"],
            "fatigue_away": away["fatigue_index"],

            "vol_home": home.get("pve_volatility"),
            "vol_away": away.get("pve_volatility"),

            "games_played_home": gp_home,
            "games_played_away": gp_away,
            "maturity_ok": maturity_ok,
        })

    out = pd.DataFrame(rows).sort_values(["game_date", "game_id"])
    out.to_csv(OUTPUT_CSV, index=False)
    print(f"✅ Wrote {len(out)} rows → {OUTPUT_CSV}")


if __name__ == "__main__":
    main()
