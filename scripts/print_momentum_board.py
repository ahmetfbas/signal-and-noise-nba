# scripts/print_momentum_board.py

from datetime import timedelta
import pandas as pd
import numpy as np

INPUT_CSV = "data/derived/team_game_metrics_with_pve.csv"
WINDOW_DAYS = 7  # calendar-day window


# --------------------------------------------------
# Helpers
# --------------------------------------------------

def weighted_pve(values: np.ndarray) -> float:
    """
    Linearly weighted PvE (recent games matter more).
    """
    n = len(values)
    if n == 0:
        return np.nan
    weights = np.arange(1, n + 1)
    return float(np.dot(values, weights) / weights.sum())


def momentum_label(score: float):
    if pd.isna(score):
        return "⚪", "No games"
    if score >= 2.0:
        return "🟢", "Strong"
    if score >= 0.5:
        return "🟢", "Positive"
    if score > -0.5:
        return "🟠", "Flat"
    if score > -2.0:
        return "🔴", "Fading"
    return "🔴", "Falling"


# --------------------------------------------------
# Main
# --------------------------------------------------

def main():
    df = pd.read_csv(INPUT_CSV)

    # Required columns
    required = {"team_name", "game_date", "pve", "actual_margin", "game_id"}
    if not required.issubset(df.columns):
        raise RuntimeError("Missing required columns. Rebuild PvE first.")

    df["game_date"] = pd.to_datetime(df["game_date"], errors="coerce").dt.date

    # Exclude invalid games
    df = df[
        df["pve"].notna()
        & df["actual_margin"].notna()
        & (df["actual_margin"] != 0)
    ].copy()

    if df.empty:
        raise RuntimeError("No valid PvE rows available after filtering.")

    latest_date = df["game_date"].max()
    start_date = latest_date - timedelta(days=WINDOW_DAYS - 1)

    window_df = df[
        (df["game_date"] >= start_date)
        & (df["game_date"] <= latest_date)
    ]

    all_teams = sorted(df["team_name"].unique())

    rows = []

    for team in all_teams:
        t = window_df[window_df["team_name"] == team].sort_values("game_date")

        pve_vals = t["pve"].to_numpy()
        score = weighted_pve(pve_vals)
        games = int(t["game_id"].nunique())
        emoji, label = momentum_label(score)

        rows.append({
            "team_name": team,
            "score": score,
            "games": games,
            "emoji": emoji,
            "label": label,
        })

    out = pd.DataFrame(rows)
    out["_sort"] = out["score"].fillna(-9999)
    out = out.sort_values(["_sort", "games"], ascending=[False, False]).drop(columns="_sort")

    # --------------------------------------------------
    # Output
    # --------------------------------------------------

    print(
        f"🔄 Momentum Board ({start_date} → {latest_date}) — last {WINDOW_DAYS} calendar days"
    )
    print("Score: weighted PvE vs expectation (wins matter, blowouts vs weak teams muted).\n")

    for _, r in out.iterrows():
        score_txt = f"{r['score']:+.2f}" if pd.notna(r["score"]) else "—"
        print(
            f"{r['emoji']} {r['team_name']:<25} — {r['label']:<8} "
            f"| score: {score_txt:>6} | games: {r['games']}"
        )


if __name__ == "__main__":
    main()
