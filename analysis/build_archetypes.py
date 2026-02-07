import os
import pandas as pd
from analysis.archetypes import classify_archetype, direction_label

INPUT_CSV = "data/derived/team_game_metrics_with_rpmi_cvv.csv"
OUTPUT_CSV = "data/derived/team_game_metrics_with_archetypes.csv"

def main():
    if not os.path.exists(INPUT_CSV):
        raise FileNotFoundError("CVV output missing — archetypes cannot run.")

    df = pd.read_csv(INPUT_CSV)
    if df.empty:
        raise RuntimeError("Archetypes input is empty.")

    df["archetype"] = df.apply(classify_archetype, axis=1)
    df["direction_label"] = df.apply(direction_label, axis=1)

    df.to_csv(OUTPUT_CSV, index=False)
    print(f"✅ Wrote {len(df)} rows → {OUTPUT_CSV}")

if __name__ == "__main__":
    main()
