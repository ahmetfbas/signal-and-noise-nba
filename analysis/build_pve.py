import pandas as pd

from analysis.pve import expected_margin_breakdown_from_rows

INPUT_CSV = "data/derived/team_game_metrics.csv"
OUTPUT_CSV = "data/derived/team_game_metrics_with_pve.csv"


def build_pve(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    # ------------------------------------------------------------------
    # Date handling (timezone-safe)
    # ------------------------------------------------------------------
    df["game_date"] = pd.to_datetime(df["game_date"], utc=True, errors="coerce")
    today = pd.Timestamp.utcnow().normalize()

    # Exclude games today or in the future (not played yet)
    df = df[df["game_date"] < today]

    df = df.sort_values(["team_id", "game_date"])

    pve_rows = []

    # ------------------------------------------------------------------
    # Process game-by-game (pairwise)
    # ------------------------------------------------------------------
    for game_id, g in df.groupby("game_id"):
        if len(g) != 2:
            continue  # broken game

        for _, row in g.iterrows():
            actual = row["actual_margin"]

            # --------------------------------------------------
            # Ignore zero-margin rows (API artifacts)
            # --------------------------------------------------
            if pd.isna(actual) or actual == 0:
                continue

            recent_games = df[
                (df["team_id"].isin([row["team_id"], row["opponent_id"]]))
                & (df["game_date"] < row["game_date"])
            ].tail(30)

            breakdown = expected_margin_breakdown_from_rows(
                team_id=row["team_id"],
                opponent_id=row["opponent_id"],
                is_home=row["home_away"] == "H",
                recent_games=recent_games,
                fatigue_index=row["fatigue_index"],
            )

            expected = breakdown["expected_total"]
            pve = actual - expected

            pve_rows.append({
                **row.to_dict(),
                "expected_margin": round(expected, 2),
                "pve": round(pve, 2),
                **breakdown,
            })

    return pd.DataFrame(pve_rows)


def main():
    df = pd.read_csv(INPUT_CSV)

    out = build_pve(df)

    if out.empty:
        raise RuntimeError("PvE produced no rows — pipeline error")

    out.to_csv(OUTPUT_CSV, index=False)
    print(f"✅ PvE written: {len(out)} rows")


if __name__ == "__main__":
    main()
