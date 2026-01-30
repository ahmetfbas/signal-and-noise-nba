import pandas as pd

INPUT_CSV = "data/derived/team_game_metrics_with_rpmi_cvv.csv"


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
    print(f"Weekly Momentum Board 🔄 ({latest_date})\n")

    for _, row in latest.iterrows():
        emoji, label = momentum_label(row["rpmi_delta"])
        if emoji and label:
            print(f"{emoji} {row['team_name']} — {label}")


if __name__ == "__main__":
    main()
