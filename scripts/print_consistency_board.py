# scripts/print_consistency_board.py

import pandas as pd

INPUT_CSV = "data/derived/team_game_metrics_with_rpmi_cvv.csv"

# --------------------------------------------------
# Helper labels
# --------------------------------------------------

def consistency_band(v):
    if pd.isna(v):
        return "—"
    if v >= 0.65:
        return "High"
    if v >= 0.50:
        return "Medium"
    return "Low"


def direction_label(win_c, loss_c):
    if pd.isna(win_c) or pd.isna(loss_c):
        return "—"
    if win_c > loss_c + 0.05:
        return "Good Wins"
    if loss_c > win_c + 0.05:
        return "Controlled Losses"
    return "Neutral"


# --------------------------------------------------
# Archetype logic (REFactored)
# Uses avg_pve_window instead of RPMI
# --------------------------------------------------

def archetype(row):
    c = row["consistency"]
    w = row["consistency_win"]
    l = row["consistency_loss"]
    avg_pve = row["avg_pve_window"]

    if pd.isna(c) or pd.isna(avg_pve):
        return "—"

    # Stable teams
    if c >= 0.65 and avg_pve >= 6:
        return "Boring Contender"
    if c >= 0.65 and avg_pve <= -6:
        return "Consistently Bad"

    # Unstable extremes
    if c < 0.50 and avg_pve >= 6:
        return "Fake Good Team"
    if c < 0.50 and avg_pve <= -6:
        return "Dangerous Underdog"

    # Style-based
    if not pd.isna(w) and not pd.isna(l):
        if w >= 0.65 and l <= 0.45:
            return "Boom–Bust"

    return "Mixed Form"


# --------------------------------------------------
# Main
# --------------------------------------------------

def main():
    df = pd.read_csv(INPUT_CSV)
    df["game_date"] = pd.to_datetime(df["game_date"], errors="coerce").dt.date

    df = df[df["consistency"].notna()]
    if df.empty:
        print("⚠️ No valid consistency data available.")
        return

    latest = (
        df.sort_values("game_date", ascending=False)
        .drop_duplicates(subset=["team_name"])
        .sort_values("consistency", ascending=False)
    )

    latest_date = latest["game_date"].max()
    print(f"📊 Consistency Board ({latest_date})\n")

    for _, r in latest.iterrows():
        win_c = r["consistency_win"]
        loss_c = r["consistency_loss"]

        print(
            f"{r['team_name']:<25} | "
            f"avg: {r['consistency']:.2f} ({consistency_band(r['consistency'])}) | "
            f"W: {win_c:.2f}" if not pd.isna(win_c)
            else f"{r['team_name']:<25} | avg: {r['consistency']:.2f} | W: —",
            end=""
        )

        if not pd.isna(loss_c):
            print(f" | L: {loss_c:.2f}", end="")
        else:
            print(" | L: —", end="")

        print(
            f" | {direction_label(win_c, loss_c)} | "
            f"{archetype(r)}"
        )


if __name__ == "__main__":
    main()
