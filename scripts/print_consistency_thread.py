import pandas as pd

INPUT_CSV = "data/derived/team_game_metrics_with_rpmi_cvv.csv"

TOP_N = 3
MID_N = 3
BOT_N = 3


def main():
    df = pd.read_csv(INPUT_CSV)

    df["game_date"] = pd.to_datetime(df["game_date"], errors="coerce", utc=True)
    df = df[df["game_date"].notna()].copy()
    df = df[df["consistency"].notna()].copy()

    if df.empty:
        print("⚠️ No valid consistency data available.")
        return

    df = df.sort_values(["team_name", "game_date", "game_id"])
    latest = df.groupby("team_name", as_index=False).tail(1)
    latest = latest.sort_values("consistency", ascending=False)

    min_date = df["game_date"].min().date()
    max_date = df["game_date"].max().date()

    most_consistent = latest.head(TOP_N)["team_name"].tolist()
    most_volatile = latest.tail(BOT_N)["team_name"].tolist()

    mid_start = (len(latest) // 2) - (MID_N // 2)
    mixed = latest.iloc[mid_start:mid_start + MID_N]["team_name"].tolist()

    ordered_teams = latest["team_name"].tolist()

    print(f"🧵 Weekly Consistency Check ({min_date} → {max_date})\n")

    print(
        "📊 Consistency is about predictability, not strength.\n\n"
        "It shows how repeatable a team’s performances are from game to game,\n"
        "not whether they’re good or bad.\n"
    )

    print("🧱 Most Consistent Teams\n")
    for t in most_consistent:
        print(t)
    print()

    print("⚖️ Mixed Consistency\n")
    for t in mixed:
        print(t)
    print()

    print("🌪️ Most Volatile Teams\n")
    for t in most_volatile:
        print(t)
    print()

    print("🧾 Full League Order (most consistent → most volatile)\n")
    for i, team in enumerate(ordered_teams, start=1):
        print(f"{i}. {team}")
    print()

    print(
        "Talent wins games.\n"
        "Execution decides nights.\n\n"
        "Consistency shows what a team usually brings, no matter the score."
    )


if __name__ == "__main__":
    main()
