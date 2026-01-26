import pandas as pd

from analysis.pve import expected_margin_breakdown_from_rows


INPUT_CSV = "data/derived/team_game_metrics.csv"
OUTPUT_CSV = "data/derived/team_game_metrics_with_pve.csv"


def build_pve(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["game_date"] = pd.to_datetime(df["game_date"])
    df = df.sort_values(["team_id", "game_date"])

    pve_rows = []

    for game_id, g in df.groupby("game_id"):
        if len(g) != 2:
            continue  # skip broken games

        for _, row in g.iterrows():
            breakdown = expected_margin_breakdown_from_rows(
                team_id=row["team_id"],
                opponent_id=row["opponent_id"],
                is_home=row["home_away"] == "H",
                recent_games=df[
                    (df["team_id"] == row["team_id"]) &
                    (df["game_date"] < row["game_date"])
                ].tail(15),
                fatigue_index=row["fatigue_index"],
            )

            expected = breakdown["expected_total"]
            actual = row["actual_margin"]

            pve_rows.append({
                **row.to_dict(),
                "expected_margin": round(expected, 2),
                "pve": round(actual - expected, 2),
                **breakdown,
            })

    return pd.DataFrame(pve_rows)


def main():
    df = pd.read_csv(INPUT_CSV)
    out = build_pve(df)
    out.to_csv(OUTPUT_CSV, index=False)


if __name__ == "__main__":
    main()
