# scripts/print_consistency_board.py

import pandas as pd
from analysis.compose_tweet import compose_tweet


INPUT_CSV = "data/derived/team_game_metrics_with_rpmi_cvv.csv"


# --------------------------------------------------
# Label helpers
# --------------------------------------------------

def consistency_label(value: float):
    if pd.isna(value):
        return None, None
    if value >= 0.65:
        return "🔒", "Very Consistent"
    if value >= 0.50:
        return "⚖️", "Consistent"
    if value >= 0.35:
        return "🌪️", "Volatile"
    return "💥", "Very Volatile"


# --------------------------------------------------
# Main
# --------------------------------------------------

def main():
    df = pd.read_csv(INPUT_CSV)
    df["game_date"] = pd.to_datetime(df["game_date"], errors="coerce").dt.date

    # Keep only valid consistency entries
    df = df[df["consistency"].notna()]

    if df.empty:
        print("⚠️ No valid consistency data available.")
        return

    # Latest consistency snapshot per team
    latest = (
        df.sort_values("game_date", ascending=False)
        .drop_duplicates(subset=["team_name"])
        .sort_values("consistency", ascending=False)
    )

    latest_date = latest["game_date"].max()
    print(f"📊 Consistency Board ({latest_date})\n")

    for _, row in latest.iterrows():
        emoji, label = consistency_label(row["consistency"])
        if emoji:
            print(f"{emoji} {row['team_name']:<25} — {label}")

    # --------------------------------------------------
    # AI commentary
    # --------------------------------------------------

    print("\n" + "=" * 45 + "\n")

    header = f"📊 Consistency Board ({latest_date})"
    body_text = (
        "This board reflects how steady each team’s performance has been over "
        "recent games. Higher consistency points to predictable outcomes, while "
        "lower scores indicate wider performance swings."
    )

    tweet_main, tweet_ai = compose_tweet(
        board_name="Consistency Board",
        data=latest,
        header=header,
        body_text=body_text,
        mode="board",
    )

    print(tweet_main)
    print(f"\n↳ {tweet_ai}\n")


if __name__ == "__main__":
    main()
