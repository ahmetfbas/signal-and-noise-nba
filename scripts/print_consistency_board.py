import pandas as pd

INPUT_CSV = "data/derived/team_game_metrics_with_rpmi_cvv.csv"


def consistency_label(value: float):
    if pd.isna(value):
        return None, None
    if value >= 0.65:
        return "🟢", "Very Consistent"
    if value >= 0.50:
        return "🟢", "Consistent"
    if value >= 0.35:
        return "⚠️", "Volatile"
    return "🔴", "Very Volatile"


def main():
    df = pd.read_csv(INPUT_CSV)
    df["game_date"] = pd.to_datetime(df["game_date"], errors="coerce").dt.date

    # Keep only non-null consistency
    df = df[~df["consistency"].isna()]

    # One record per team (latest game)
    latest = (
        df.sort_values("game_date", ascending=False)
        .drop_duplicates(subset=["team_name"])
        .sort_values("consistency", ascending=False)
    )

    if latest.empty:
        print("⚠️ No valid consistency data available.")
        return

    latest_date = df["game_date"].max()
    print(f"Weekly Consistency Board 📊 ({latest_date})\n")

    for _, row in latest.iterrows():
        emoji, label = consistency_label(row["consistency"])
        if emoji:
            print(f"{emoji} {row['team_name']} — {label}")


if __name__ == "__main__":
    main()
