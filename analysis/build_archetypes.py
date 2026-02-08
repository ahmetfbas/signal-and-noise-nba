import os
import pandas as pd
from analysis.archetypes import classify_archetype

INPUT_CSV = "data/derived/team_game_metrics_with_rpmi_cvv.csv"
OUTPUT_CSV = "data/derived/team_game_metrics_with_archetypes.csv"


def main():
    if not os.path.exists(INPUT_CSV):
        raise FileNotFoundError("Metrics CSV missing — archetypes cannot run.")

    df = pd.read_csv(INPUT_CSV)
    if df.empty:
        raise RuntimeError("Archetypes input is empty.")

    # -----------------------------
    # Build SEASON-LEVEL identity
    # -----------------------------
    # One row per team, using all games played
    season = (
        df.sort_values("game_date")
          .groupby("team_name", as_index=False)
          .agg(
              season_games=("game_id", "count"),
              season_wins=("actual_margin", lambda x: (x > 0).sum()),
              season_avg_pve=("pve", "mean"),
              season_consistency=("consistency", "mean"),
          )
    )

    season["season_win_rate"] = (
        season["season_wins"] / season["season_games"]
    )

    # -----------------------------
    # Classify archetypes (STABLE)
    # -----------------------------
    season["archetype"] = season.apply(classify_archetype, axis=1)

    # -----------------------------
    # Merge back to game-level data
    # -----------------------------
    out = df.merge(
        season[
            [
                "team_name",
                "season_win_rate",
                "season_avg_pve",
                "season_consistency",
                "archetype",
            ]
        ],
        on="team_name",
        how="left",
    )

    out.to_csv(OUTPUT_CSV, index=False)
    print(f"✅ Wrote {len(out)} rows → {OUTPUT_CSV}")


if __name__ == "__main__":
    main()
