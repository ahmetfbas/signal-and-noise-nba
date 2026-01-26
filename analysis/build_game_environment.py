import pandas as pd
import numpy as np

INPUT_CSV = "data/derived/team_game_metrics_with_rpmi_cvv.csv"
OUTPUT_CSV = "data/derived/game_environment.csv"

# Label thresholds
CLEAN_THR = 0.33
NOISY_THR = 0.67

# If rolling metrics are not mature enough, we call the game "Forming"
# because volatility/consistency/RPMI are less trustworthy early.
MIN_GAMES_FOR_MATURE = 10


def clip01(x):
    return float(np.clip(x, 0.0, 1.0))


def norm_fatigue(f):
    """
    Map fatigue_index (roughly 0-120+) to 0-1 risk.
    30 = low-ish, 80 = very high.
    """
    if pd.isna(f):
        return np.nan
    return clip01((float(f) - 30.0) / 50.0)


def norm_volatility(vol):
    """
    Map PvE volatility (std of last WINDOW PvE in points) to 0-1 risk.
    8 = calm, 20 = very volatile (typical NBA ranges).
    """
    if pd.isna(vol):
        return np.nan
    return clip01((float(vol) - 8.0) / 12.0)


def norm_asym_fatigue(f_home, f_away):
    """Asymmetry risk from fatigue mismatch."""
    if pd.isna(f_home) or pd.isna(f_away):
        return np.nan
    return clip01(abs(float(f_home) - float(f_away)) / 40.0)


def norm_asym_consistency(c_home, c_away):
    """Asymmetry risk from consistency mismatch (0.25-0.80 typical)."""
    if pd.isna(c_home) or pd.isna(c_away):
        return np.nan
    return clip01(abs(float(c_home) - float(c_away)) / 0.30)


def safe_weighted_avg(pairs):
    """
    pairs = [(value, weight), ...] where value can be NaN
    returns weighted average over non-NaN values, and the effective weight sum.
    """
    vals = []
    wts = []
    for v, w in pairs:
        if v is None or (isinstance(v, float) and np.isnan(v)) or pd.isna(v):
            continue
        vals.append(float(v))
        wts.append(float(w))
    if not wts:
        return np.nan, 0.0
    return float(np.average(vals, weights=wts)), float(sum(wts))


def classify_environment(noise_score, maturity_ok):
    if not maturity_ok:
        return "Forming"
    if pd.isna(noise_score):
        return "Forming"
    if noise_score <= CLEAN_THR:
        return "Clean"
    if noise_score >= NOISY_THR:
        return "Noisy"
    return "Mixed"


def build_drivers(fatigue_avg, vol_avg, asymmetry_score, maturity_ok):
    drivers = []
    if not maturity_ok:
        drivers.append("early-season/low-history")
        return ", ".join(drivers)

    if not pd.isna(fatigue_avg) and fatigue_avg >= 0.60:
        drivers.append("high fatigue load")
    if not pd.isna(vol_avg) and vol_avg >= 0.60:
        drivers.append("high volatility")
    if not pd.isna(asymmetry_score) and asymmetry_score >= 0.60:
        drivers.append("asymmetry (conditions mismatch)")

    if not drivers:
        drivers.append("stable conditions")
    return ", ".join(drivers)


def main():
    df = pd.read_csv(INPUT_CSV)
    df["game_date"] = pd.to_datetime(df["game_date"])

    # Ensure we have exactly 2 rows per game_id (home + away)
    # We’ll still proceed if there are outliers, but we’ll drop broken games.
    counts = df.groupby("game_id").size()
    good_games = counts[counts == 2].index
    df = df[df["game_id"].isin(good_games)].copy()

    rows = []

    for game_id, g in df.groupby("game_id"):
        # Identify home vs away rows
        home = g[g.get("home_away", "").astype(str).str.upper().isin(["H", "HOME"])].head(1)
        away = g[g.get("home_away", "").astype(str).str.upper().isin(["A", "AWAY"])].head(1)

        # If your dataset uses different home/away flags, fallback:
        if home.empty or away.empty:
            # fallback: use presence of "home_team_id" vs "team_id" if exists
            # otherwise just take first as home, second as away (last resort)
            home = g.iloc[[0]]
            away = g.iloc[[1]]

        home = home.iloc[0]
        away = away.iloc[0]

        # Maturity check (rolling metrics become meaningful after ~10 games/team)
        gp_home = home.get("games_played", np.nan)
        gp_away = away.get("games_played", np.nan)
        maturity_ok = (
            (not pd.isna(gp_home) and gp_home >= MIN_GAMES_FOR_MATURE) and
            (not pd.isna(gp_away) and gp_away >= MIN_GAMES_FOR_MATURE)
        )

        # --- Components (0-1 risk) ---
        f_home = norm_fatigue(home.get("fatigue_index", np.nan))
        f_away = norm_fatigue(away.get("fatigue_index", np.nan))
        fatigue_avg, _ = safe_weighted_avg([(f_home, 1), (f_away, 1)])

        v_home = norm_volatility(home.get("pve_volatility", np.nan))
        v_away = norm_volatility(away.get("pve_volatility", np.nan))
        vol_avg, vol_w = safe_weighted_avg([(v_home, 1), (v_away, 1)])

        asym_f = norm_asym_fatigue(home.get("fatigue_index", np.nan), away.get("fatigue_index", np.nan))
        asym_c = norm_asym_consistency(home.get("consistency", np.nan), away.get("consistency", np.nan))
        asymmetry_score, asym_w = safe_weighted_avg([(asym_f, 1), (asym_c, 1)])

        # --- Composite noise score ---
        # Weighting philosophy:
        # - Fatigue drives execution risk (largest weight)
        # - Volatility drives unpredictability (second)
        # - Asymmetry captures mismatch / fragility (third)
        noise_score, wsum = safe_weighted_avg([
            (fatigue_avg, 0.45),
            (vol_avg,     0.35),
            (asymmetry_score, 0.20),
        ])

        # If volatility is missing early, the effective score might be based on fewer components.
        # That’s okay; maturity label will handle it. Still keep the computed value.
        env_label = classify_environment(noise_score, maturity_ok)
        drivers = build_drivers(fatigue_avg, vol_avg, asymmetry_score, maturity_ok)

        matchup = f"{away.get('team_abbr', away.get('team_name', 'AWAY'))} @ {home.get('team_abbr', home.get('team_name', 'HOME'))}"

        rows.append({
            "game_id": game_id,
            "game_date": home.get("game_date", away.get("game_date")),
            "matchup": matchup,

            "noise_score": None if pd.isna(noise_score) else round(noise_score, 3),
            "environment_label": env_label,
            "drivers": drivers,

            # Helpful diagnostics
            "fatigue_home": home.get("fatigue_index", np.nan),
            "fatigue_away": away.get("fatigue_index", np.nan),
            "fatigue_risk_avg": None if pd.isna(fatigue_avg) else round(fatigue_avg, 3),

            "vol_home": home.get("pve_volatility", np.nan),
            "vol_away": away.get("pve_volatility", np.nan),
            "vol_risk_avg": None if pd.isna(vol_avg) else round(vol_avg, 3),

            "asymmetry_score": None if pd.isna(asymmetry_score) else round(asymmetry_score, 3),

            # Optional: baseline expected margins (pre-game)
            "expected_margin_home": home.get("expected_margin", np.nan),
            "expected_margin_away": away.get("expected_margin", np.nan),

            # Optional: maturity
            "games_played_home": gp_home,
            "games_played_away": gp_away,
            "maturity_ok": maturity_ok,
        })

    out = pd.DataFrame(rows)
    out["game_date"] = pd.to_datetime(out["game_date"])
    out = out.sort_values(["game_date", "game_id"])

    out.to_csv(OUTPUT_CSV, index=False)
    print(f"Saved game environment classification to {OUTPUT_CSV} ({len(out)} games)")


if __name__ == "__main__":
    main()
