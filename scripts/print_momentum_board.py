# scripts/print_momentum_board.py

import pandas as pd
from analysis.compose_tweet import compose_tweet

INPUT_CSV = "data/derived/team_game_metrics_with_rpmi.csv"


def momentum_label(delta: float):
    if pd.isna(delta):
        return None, None
    if delta >= 2.5:
        return "🟢", "Strong"
    if delta >= 1.0:
        return "🟢", "Positive"
    if delta > -1.0:
        return "🟠", "Flat"
    if delta > -2.5:
        return "🔴", "Fading"
    return "🔴", "Falling"


def main():
    df = pd.read_csv(INPUT_CSV)
    df["game_date"] = pd.to_datetime(df["game_date"], errors="coerce").dt.date

    # Filter out null values
    df = df[~df["rpmi_delta"].isna()]

    # Get one latest record per team
    latest = (
        df.sort_values("game_date", ascending=False)
        .drop_duplicates(subset=["team_name"])
        .sort_values("rpmi_delta", ascending=False)
    )

    if latest.empty:
        print("⚠️ No valid rpmΔ data found.")
        return

    latest_date = df["game_date"].max()
    print(f"🔄 Weekly Momentum Board ({latest_date})\n")

    for _, row in latest.iterrows():
        emoji, label = momentum_label(row["rpmi_delta"])
        if emoji and label:
            print(f"{emoji} {row['team_name']:<25} — {label}")

    # --- AI Commentary ---
    print("\n" + "=" * 45 + "\n")

    header = f"🔄 Weekly Momentum Board ({latest_date})"
    body_text = (
        "This board shows which teams are trending upward or losing pace "
        "based on recent performance swings (rpmiΔ). Strong = improving form, "
        "Fading = momentum slipping."
    )

    tweet_main, tweet_ai = compose_tweet(
        board_name="Weekly Momentum Board",
        data=latest.head(10),
        header=header,
        body_text=body_text,
        mode="board",
    )

    print(tweet_main)
    print(f"\n↳ {tweet_ai}\n")


if __name__ == "__main__":
    main()
