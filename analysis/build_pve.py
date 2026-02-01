import pandas as pd

from analysis.pve import expected_margin_breakdown_from_rows


INPUT_CSV = "data/derived/team_game_metrics.csv"
OUTPUT_CSV = "data/derived/team_game_metrics_with_pve.csv"


def build_pve(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["game_date"] = pd.to_datetime(df["game_date"], utc=True)
    df = df.sort_values(["team_id", "game_date"])

    pve_rows = []

    for game_id, g in df.groupby("game_id"):
        if len(g) != 2:
            continue  # skip broken games

        for _, row in g.iterrows():
            actual = row["actual_margin"]

            # --------------------------------------------------
            # ❌ EXCLUDE DRAWS (no signal)
            # --------------------------------------------------
            if actual == 0:
                continue

            breakdown = expected_margin_breakdown_from_rows(
                team_id=row["team_id"],
                opponent_id=row["opponent_id"],
                is_home=row["home_away"] == "H",
                recent_games=df[
                    (df["team_id"].isin([row["team_id"], row["opponent_id"]]))
                    & (df["game_date"] < row["game_date"])
                ].tail(30),
                fatigue_index=row["fatigue_index"],
            )

            expected = breakdown["expected_total"]
            raw_pve = actual - expected

            # --------------------------------------------------
            # PvE CORRECTIONS (loss-aware)
            # --------------------------------------------------
            pve = raw_pve

            if actual < 0:
                # Cap positive surprise from losses
                pve = min(pve, 5.0)

                # Blowout loss damping
                if actual <= -15:
                    pve *= 0.25

                # Bad-team surprise suppression
                team_rows = df[
                    (df["team_id"] == row["team_id"])
                    & (df["game_date"] < row["game_date"])
                ].tail(30)

                if not team_rows.empty:
                    win_rate = (team_rows["actual_margin"] > 0).mean()
                    if win_rate < 0.40:
                        pve *= 0.30

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
        raise RuntimeError("PvE produced no rows — this is a pipeline error.")

    out.to_csv(OUTPUT_CSV, index=False)
    print(f"✅ PvE written: {len(out)} rows")


if __name__ == "__main__":
    main()
