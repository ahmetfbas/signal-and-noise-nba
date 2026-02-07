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

    if df.empty:
        print("⚠️ No data available.")
        return

    df = df.sort_values(["team_id", "game_date", "game_id"])
    latest = df.drop_duplicates(subset=["team_id"], keep="last").copy()

    latest = latest[latest["consistency"].notna()].copy()
    if latest.empty:
        print("⚠️ No valid consistency data available.")
        return

    latest = latest.sort_values(["consistency", "team_name"], ascending=[False, True])

    latest_date = latest["game_date"].max().date()
    print(f"📊 Consistency Board ({latest_date})\n")

    for _, r in latest.iterrows():
        team = r["team_name"]
        c = r["consistency"]
        win_c = r.get("consistency_win")
        loss_c = r.get("consistency_loss")
        band = consistency_band(c)

        line = (
            f"{team:<25} | "
            f"avg: {float(c):.2f} ({band}) | "
            f"W: {fmt_float(win_c)} | "
            f"L: {fmt_float(loss_c)}"
        )
        print(line)


if __name__ == "__main__":
    main()
