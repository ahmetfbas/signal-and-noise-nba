import pandas as pd
import numpy as np
import os

WINDOW = 10
VOL_SCALE = 15.0
MIN_GAMES = 3


def consistency_from_values(values: np.ndarray) -> float:
    if len(values) < MIN_GAMES:
        return np.nan
    vol = np.std(values, ddof=0)
    return round(1 / (1 + vol / VOL_SCALE), 3)


def compute_cvv(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["game_date"] = pd.to_datetime(df["game_date"], errors="coerce", utc=True)

    # IMPORTANT: sort by TEAM NAME (stable identity)
    df = df.sort_values(["team_name", "game_date", "game_id"])

    cols = [
        "pve_volatility",
        "consistency",
        "consistency_win",
        "consistency_loss",
        "games_played",
        "games_in_window",
        "avg_pve_window",
        "wins_window",
        "losses_window",
        "win_rate_window",
    ]
    df[cols] = np.nan

    for team, g in df.groupby("team_name"):
        g = g.reset_index()

        for i in range(len(g)):
            idx = g.loc[i, "index"]
            df.loc[idx, "games_played"] = i + 1

            if i < WINDOW - 1:
                continue

            window = g.loc[i - WINDOW + 1 : i]

            # Exclude unplayed / invalid games
            window = window[window["actual_margin"] != 0]

            wins = (window["actual_margin"] > 0).sum()
            losses = (window["actual_margin"] < 0).sum()
            total = wins + losses

            df.loc[idx, "wins_window"] = wins
            df.loc[idx, "losses_window"] = losses
            df.loc[idx, "win_rate_window"] = round(wins / total, 3) if total else np.nan

            pve_vals = window["pve"].dropna().values
            df.loc[idx, "games_in_window"] = len(pve_vals)

            # Always write volatility if possible
            if len(pve_vals) >= MIN_GAMES:
                df.loc[idx, "avg_pve_window"] = round(float(np.mean(pve_vals)), 2)
                df.loc[idx, "pve_volatility"] = round(np.std(pve_vals, ddof=0), 2)
                df.loc[idx, "consistency"] = consistency_from_values(pve_vals)

                win_vals = window.loc[window["actual_margin"] > 0, "pve"].dropna().values
                loss_vals = window.loc[window["actual_margin"] < 0, "pve"].dropna().values

                df.loc[idx, "consistency_win"] = consistency_from_values(win_vals)
                df.loc[idx, "consistency_loss"] = consistency_from_values(loss_vals)

    return df


def main():
    input_csv = "data/derived/team_game_metrics_with_rpmi.csv"
    output_csv = "data/derived/team_game_metrics_with_rpmi_cvv.csv"

    if not os.path.exists(input_csv):
        raise FileNotFoundError("RPMI output missing — CVV cannot run.")

    df = pd.read_csv(input_csv)
    if df.empty:
        raise RuntimeError("CVV input is empty.")

    out = compute_cvv(df)
    out.to_csv(output_csv, index=False)

    print(f"✅ Wrote {len(out)} rows → {output_csv}")
    print(f"Window size: {WINDOW}")
    print(f"Latest consistency date: {out.loc[out['consistency'].notna(), 'game_date'].max()}")
    print(f"Avg win-rate (window): {out['win_rate_window'].mean():.3f}")


if __name__ == "__main__":
    main()
