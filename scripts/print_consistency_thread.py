import pandas as pd

INPUT_CSV = "data/derived/team_game_metrics_with_rpmi_cvv.csv"

TOP_N = 3
MID_N = 3
BOT_N = 3


def main():
    df = pd.read_csv(INPUT_CSV)

    df["game_date"] = pd.to_datetime(df["game_date"], errors="coerce", utc=True)
    df = df[df["game_date"].notna()].copy()

    if df.empty:
        print("⚠️ No data available.")
        return

    df = df.sort_values(["team_id", "game_date", "game_id"])
    latest = df.drop_duplicates(subset=["team_id"], keep="last").copy()
    latest = latest[latest["consistency"].notna()].copy()

    if latest.empty:
        print("⚠️ No valid consistency data available.")
        return

    latest = latest.sort_values("consistency", ascending=False)

    latest_date = latest["game_date"].max().date()

    most_consistent = latest.head(TOP_N)["team_name"].tolist()
    most_volatile = latest.tail(BOT_N)["team_name"].tolist()

    mid_start = (len(latest) // 2) - (MID_N // 2)
    mixed = latest.iloc[mid_start : mid_start + MID_N]["team_name"].tolist()

    ordered_teams = latest["team_name"].tolist()

    # Tweet 1 — Opening
    print(f"🧵 Weekly Consistency Check ({latest_date})\n")
    print(
        "📊 Consistency is about predictability, not strength.\n\n"
        "It shows how repeatable a team’s performances are from game to game ,\n"
        "not whether they’re good or bad.\n"
    )

    # Tweet 2 — Most Consistent
    print("🧱 Most Consistent Teams\n")
    print(
        "These teams look roughly the same every night ,\n"
        "wins or losses don’t swing wildly.\n"
    )
    for t in most_consistent:
        print(t)
    print()

    # Tweet 3 — Mixed
    print("⚖️ Mixed Consistency\n")
    print(
        "These teams can be solid one night and shaky the next ,\n"
        "outcomes depend more on context.\n"
    )
    for t in mixed:
        print(t)
    print()

    # Tweet 4 — Most Volatile
    print("🌪️ Most Volatile Teams\n")
    print(
        "Big swings from game to game, \n"
        "hard to know which version will show up.\n"
    )
    for t in most_volatile:
        print(t)
    print()

    # Tweet 5 — Full Order
    print("🧾 Full League Order (most consistent → most volatile)\n")

    for i, team in enumerate(ordered_teams, start=1):
        print(f"{i}. {team}")

    print()


    # Tweet 6 — Closing
    print(
        "Talent wins games.\n"
        "Execution decides nights.\n\n"
        "Consistency shows what a team usually brings, no matter the score."
    )


if __name__ == "__main__":
    main()
