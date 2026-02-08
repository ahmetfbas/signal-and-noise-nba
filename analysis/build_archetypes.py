import os
import pandas as pd
from analysis.archetypes import classify_archetype

INPUT_CSV = "data/derived/team_game_metrics_with_rpmi_cvv.csv"
OUTPUT_CSV = "data/derived/team_season_identity.csv"


def main():
    if not os.path.exists(INPUT_CSV):
        raise FileNotFoundError("Metrics CSV missing — cannot build season identities.")

    df = pd.read_csv(INPUT_CSV)
    if df.empty:
        raise RuntimeError("Input metrics are empty.")

    # --------------------------------------------------
    # Build SEASON-LEVEL aggregates per team
    # --------------------------------------------------
    season = (
        df.sort_values("game_date")
          .groupby("team_name", as_index=False)
          .agg(
              season_games=("game_id", "count"),
              season_wins=("win", "sum"),
              season_avg_pve=("pve", "mean"),
              season_consistency=("consistency", "mean"),
          )
    )

    season["season_win_rate"] = season["season_wins"] / season["season_games"]

    # --------------------------------------------------
    # Apply STABLE identity archetype
    # --------------------------------------------------
    season["archetype"] = season.apply(classify_archetype, axis=1)

    season = season.sort_values("season_win_rate", ascending=False)

    season.to_csv(OUTPUT_CSV, index=False)
    print(f"✅ Wrote {len(season)} rows → {OUTPUT_CSV}")


if __name__ == "__main__":
    main()
