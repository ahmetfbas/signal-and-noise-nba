# scripts/print_momentum_board.py

import pandas as pd
from analysis.compose_tweet import compose_tweet


INPUT_CSV = "data/derived/team_game_metrics_with_rpmi.csv"


# --------------------------------------------------
# Label helpers (aligned with rpmi_delta scale)
# --------------------------------------------------

def momentum_label(delta: float):
    if pd.isna(delta):
        return None, None
    if delta >= 0.75:
        return "🟢", "Strong"
    if delta >= 0.25:
        return "🟢", "Positive"
    if delta > -0.25:
        return "🟠", "Flat"
    if delta > -0.75:
        return "🔴", "Fading"
    return "🔴", "Falling"


# --------------------------------------------------
# Main
# --------------------------------------------------

def main():
    df = pd.read_csv(INPUT_CSV)
    df["game_date"] = pd.to_datetime(df["game_date"], errors="coerce").dt.date

    # Keep only valid momentum entries
    df = df[df["rpmi_delta"].notna()]

    if df.empty:
        print("⚠️ No valid momentum data found.")
        return

    # Latest momentum snapshot per team
    latest = (
        df.sort_values("game_date", ascending=False)
        .drop_duplicates(subset=["team_name"])
        .sort_values("rpmi_delta", ascending=False)
    )

    latest_date = latest["game_date"].max()
    print(f"🔄 Momentum Board ({latest_date})\n")

    for _, row in latest.iterrows():
        emoji, label = momentum_label(row["rpmi_delta"])
        if emoji:
            print(f"{emoji} {row['team_name']:<25} — {label}")

    # --------------------------------------------------
    # AI commentary
    # --------------------------------------------------

    print("\n" + "=" * 45 + "\n")

    header = f"🔄 Momentum Board ({latest_date})"
    body_text = (
        "This board reflects the latest momentum shifts based on recent game-to-game "
        "performance changes. Strong indicates accelerating form, while Falling "
        "signals a sustained slowdown."
    )

    tweet_main, tweet_ai = compose_tweet(
        board_name="Momentum Board",
        data=latest,
        header=header,
        body_text=body_text,
        mode="board",
    )

    print(tweet_main)
    print(f"\n↳ {tweet_ai}\n")


if __name__ == "__main__":
    main()
