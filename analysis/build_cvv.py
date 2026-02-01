import pandas as pd
import numpy as np
import os

# --------------------------------------------------
# Configuration
# --------------------------------------------------

WINDOW = 10
VOL_SCALE = 15.0   # 🔧 recalibrated (was 10.0)


# --------------------------------------------------
# Core helpers
# --------------------------------------------------

def consistency_from_values(values: np.ndarray) -> float:
    if len(values) < 3:
        return np.nan
    vol = np.std(values, ddof=0)
    return round(1 / (1 + vol / VOL_SCALE), 3)


# --------------------------------------------------
# Core CVV computation
# --------------------------------------------------

def compute_cvv(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["game_date"] = pd.to_datetime(df["game_date"], errors="coerce")
    df = df.sort_values(["team_id", "game_date"])

    df[
        [
            "pve_volatility",
            "consistency",
            "consistency_win",
            "consistency_loss",
            "games_played",
            "games_in_window",
            "avg_pve_window",
        ]
    ] = np.nan

    for team_id, g in df.groupby("team_id"):
        g = g.reset_index()

        for i in range(len(g)):
            idx = g.loc[i, "index"]
            games_played = i + 1
            df.loc[idx, "games_played"] = games_played

            if i < WINDOW - 1:
                continue

            window = g.loc[i - WINDOW + 1 : i]
            window = window[window["actual_margin"] != 0]

            pve_all = window["pve"].dropna().values
            games_in_window = len(pve_all)

            df.loc[idx, "games_in_window"] = games_in_window
            df.loc[idx, "avg_pve_window"] = (
                round(float(np.mean(pve_all)), 2) if games_in_window > 0 else np.nan
            )

            if games_in_window < WINDOW:
                continue

            # Overall
            vol_all = np.std(pve_all, ddof=0)
            df.loc[idx, "pve_volatility"] = round(vol_all, 2)
            df.loc[idx, "consistency"] = consistency_from_values(pve_all)

            # Wins only
            pve_wins = window.loc[window["actual_margin"] > 0, "pve"].values
            df.loc[idx, "consistency_win"] = consistency_from_values(pve_wins)

            # Losses only
            pve_losses = window.loc[window["actual_margin"] < 0, "pve"].values
            df.loc[idx, "consistency_loss"] = consistency_from_values(pve_losses)

    return df


# --------------------------------------------------
# Label helpers
# --------------------------------------------------

def consistency_label(value, games_played):
    if pd.isna(value):
        return "Insufficient"
    if games_played < WINDOW * 2:
        return "Forming"
    if value >= 0.65:
        return "Very Consistent"
    if value >= 0.50:
        return "Consistent"
    if value >= 0.40:
        return "Volatile"
    return "Very Volatile"


# --------------------------------------------------
# Entrypoint
# --------------------------------------------------

def main():
    input_csv = "data/derived/team_game_metrics_with_rpmi.csv"
    output_csv = "data/derived/team_game_metrics_with_rpmi_cvv.csv"

    if not os.path.exists(input_csv):
        raise FileNotFoundError("RPMI output missing — CVV cannot run.")

    df = pd.read_csv(input_csv)
    if df.empty:
        raise RuntimeError("CVV input is empty — RPMI must run successfully first.")

    df = compute_cvv(df)

    df["consistency_label"] = df.apply(
        lambda r: consistency_label(r["consistency"], r["games_played"]),
        axis=1,
    )

    df.to_csv(output_csv, index=False)

    print(f"✅ Wrote {len(df)} rows → {output_csv}")
    print(f"Window size: {WINDOW} games")
    print(f"Vol scale: {VOL_SCALE}")
    print(f"Avg consistency (all): {df['consistency'].mean():.3f}")
    print(f"Avg win consistency: {df['consistency_win'].mean():.3f}")
    print(f"Avg loss consistency: {df['consistency_loss'].mean():.3f}")


if __name__ == "__main__":
    main()
