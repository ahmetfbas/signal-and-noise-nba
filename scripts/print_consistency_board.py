import pandas as pd

INPUT_CSV = "data/derived/team_game_metrics_with_rpmi_cvv.csv"


def consistency_band(v):
    if pd.isna(v):
        return "—"
    if v >= 0.65:
        return "High"
    if v >= 0.50:
        return "Medium"
    return "Low"


def fmt_float(x, nd=2):
    return "—" if pd.isna(x) else f"{float(x):.{nd}f}"


def main():
    df = pd.read_csv(INPUT_CSV)

    df["game_date"] = pd.to_datetime(df["game_date"], errors="coerce", utc=True)
    df = df[df["game_date"].notna()].copy()

    # only rows where consistency exists
    df = df[df["consistency"].notna()].copy()

    if df.empty:
        print("⚠️ No valid consistency data available.")
        return

    # sort so latest game per team_name is last
    df = df.sort_values(["team_name", "game_date", "game_id"])

    latest = df.groupby("team_name", as_index=False).tail(1)

    latest = latest.sort_values(
        ["consistency", "team_name"],
        ascending=[False, True]
    )

    min_date = df["game_date"].min().date()
    max_date = df["game_date"].max().date()

    print(f"📊 Consistency Board ({min_date} → {max_date})\n")

    for _, r in latest.iterrows():
        print(
            f"{r['team_name']:<25} | "
            f"avg: {r['consistency']:.2f} ({consistency_band(r['consistency'])}) | "
            f"W: {fmt_float(r.get('consistency_win'))} | "
            f"L: {fmt_float(r.get('consistency_loss'))}"
        )


if __name__ == "__main__":
    main()
