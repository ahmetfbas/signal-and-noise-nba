import pandas as pd
import numpy as np

INPUT_CSV = "data/derived/team_game_metrics_with_rpmi_cvv.csv"
OUTPUT_CSV = "data/derived/game_environment.csv"

# --------------------------------------------------
# Configuration
# --------------------------------------------------

CLEAN_THR = 0.33
NOISY_THR = 0.67
MIN_GAMES_FOR_MATURE = 10


# --------------------------------------------------
# Normalization helpers
# --------------------------------------------------

def clip01(x):
    return float(np.clip(x, 0.0, 1.0))


def norm_fatigue(f):
    if pd.isna(f):
        return np.nan
    return clip01((float(f) - 30.0) / 50.0)


def norm_volatility(vol):
    if pd.isna(vol):
        return np.nan
    return clip01((float(vol) - 8.0) / 12.0)


def norm_asym_fatigue(f_home, f_away):
    if pd.isna(f_home) or pd.isna(f_away):
        return np.nan
    return clip01(abs(float(f_home) - float(f_away)) / 40.0)


def norm_asym_consistency(c_home, c_away):
    if pd.isna(c_home) or pd.isna(c_away):
        return np.nan
    return clip01(abs(float(c_home) - float(c_away)) / 0.30)


def safe_weighted_avg(pairs):
    vals, wts = [], []
    for v, w in pairs:
        if pd.isna(v):
            continue
        vals.append(float(v))
        wts.append(float(w))
    if not wts:
        return np.nan, 0.0
    return float(np.average(vals, weights=wts)), float(sum(wts))


# --------------------------------------------------
# Classification logic
# --------------------------------------------------

def classify_environment(noise_score, maturity_ok):
    if not maturity_ok or pd.isna(noise_score):
        return "Forming"
    if noise_score <= CLEAN_THR:
        return "Clean"
    if noise_score >= NOISY_THR:
        return "Noisy"
    return "Mixed"


def build_drivers(fatigue_avg, vol_avg, asymmetry_score, maturity_ok):
    if not maturity_ok:
        return "early-season/low-history"

    drivers = []
    if not pd.isna(fatigue_avg) and fatigue_avg >= 0.60:
        drivers.append("high fatigue load")
    if not pd.isna(vol_avg) and vol_avg >= 0.60:
        drivers.append("high volatility")
    if not pd.isna(asymmetry_score) and asymmetry_score >= 0.60:
        drivers.append("asymmetry mismatch")

    return ", ".join(drivers) if drivers else "stable conditions"


# --------------------------------------------------
# Main builder
# --------------------------------------------------

def main():
    df = pd.read_csv(INPUT_CSV)
    df["game_date"] = pd.to_datetime(df["game_date"], utc=True)

    # enforce exactly 2 rows per game
    valid_games = df.groupby("game_id").size()
    df = df[df["game_id"].isin(valid_games[valid_games == 2].index)].copy()

    rows = []

    for game_id, g in df.groupby("game_id"):
        home = g[g["home_away"] == "H"].iloc[0]
        away = g[g["home_away"] == "A"].iloc[0]

        # maturity = number of prior games per team
        gp_home = df[
            (df["team_id"] == home["team_id"]) &
            (df["game_date"] < home["game_date"])
        ].shape[0]

        gp_away = df[
            (df["team_id"] == away["team_id"]) &
            (df["game_date"] < away["game_date"])
        ].shape[0]

        maturity_ok = (
            gp_home >= MIN_GAMES_FOR_MATURE and
            gp_away >= MIN_GAMES_FOR_MATURE
        )

        # risks
        f_home = norm_fatigue(home["fatigue_index"])
        f_away = norm_fatigue(away["fatigue_index"])
        fatigue_avg, _ = safe_weighted_avg([(f_home, 1), (f_away, 1)])

        v_home = norm_volatility(home.get("pve_volatility"))
        v_away = norm_volatility(away.get("pve_volatility"))
        vol_avg, _ = safe_weighted_avg([(v_home, 1), (v_away, 1)])

        asym_f = norm_asym_fatigue(home["fatigue_index"], away["fatigue_index"])
        asym_c = norm_asym_consistency(home.get("consistency"), away.get("consistency"))
        asymmetry_score, _ = safe_weighted_avg([(asym_f, 1), (asym_c, 1)])

        noise_score, _ = safe_weighted_avg([
            (fatigue_avg, 0.45),
            (vol_avg, 0.35),
            (asymmetry_score, 0.20),
        ])

        rows.append({
            "game_id": game_id,
            "game_date": home["game_date"],
            "matchup": f"{away['team_name']} @ {home['team_name']}",

            "noise_score": None if pd.isna(noise_score) else round(noise_score, 3),
            "environment_label": classify_environment(noise_score, maturity_ok),
            "drivers": build_drivers(fatigue_avg, vol_avg, asymmetry_score, maturity_ok),

            "fatigue_home": home["fatigue_index"],
            "fatigue_away": away["fatigue_index"],
            "fatigue_risk_avg": None if pd.isna(fatigue_avg) else round(fatigue_avg, 3),

            "vol_home": home.get("pve_volatility"),
            "vol_away": away.get("pve_volatility"),
            "vol_risk_avg": None if pd.isna(vol_avg) else round(vol_avg, 3),

            "asymmetry_score": None if pd.isna(asymmetry_score) else round(asymmetry_score, 3),

            "expected_margin_home": home.get("expected_margin"),
            "expected_margin_away": away.get("expected_margin"),

            "games_played_home": gp_home,
            "games_played_away": gp_away,
            "maturity_ok": maturity_ok,
        })

    out = pd.DataFrame(rows).sort_values(["game_date", "game_id"])
    out.to_csv(OUTPUT_CSV, index=False)


if __name__ == "__main__":
    main()
