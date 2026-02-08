# scripts/print_momentum_thread.py
import pandas as pd
import numpy as np

INPUT_CSV = "data/derived/team_game_metrics_with_rpmi_cvv.csv"
WINDOW = 10

# ---- Helper formatting ----
def fmt_float(x, nd=2):
    return "—" if pd.isna(x) else f"{float(x):.{nd}f}"

def fmt_wl(w, l):
    return f"{int(w)}-{int(l)}"

def safe_sum(s):
    return float(pd.to_numeric(s, errors="coerce").fillna(0).sum())

def safe_mean(s):
    s = pd.to_numeric(s, errors="coerce")
    return float(s.mean()) if s.notna().any() else np.nan

def build_last_n(df: pd.DataFrame, n: int = 10) -> pd.DataFrame:
    df = df.copy()
    df["game_date"] = pd.to_datetime(df["game_date"], errors="coerce", utc=True)
    df = df[df["game_date"].notna()].copy()

    # guard: if game_id exists, sort by it too for same-day ordering
    sort_cols = ["team_name", "game_date"]
    if "game_id" in df.columns:
        sort_cols.append("game_id")

    df = df.sort_values(sort_cols)
    lastn = df.groupby("team_name", as_index=False).tail(n).copy()
    return lastn

def summarize_team(lastn: pd.DataFrame) -> pd.DataFrame:
    # expected columns used:
    # team_name, game_date, actual_margin, pve, momentum_unit
    lastn = lastn.copy()

    lastn["actual_margin"] = pd.to_numeric(lastn.get("actual_margin"), errors="coerce")
    lastn["pve"] = pd.to_numeric(lastn.get("pve"), errors="coerce")
    lastn["momentum_unit"] = pd.to_numeric(lastn.get("momentum_unit"), errors="coerce")

    def agg(g):
        wins = int((g["actual_margin"] > 0).sum())
        losses = int((g["actual_margin"] < 0).sum())
        games = int(g["actual_margin"].notna().sum())
        return pd.Series(
            {
                "team_name": g["team_name"].iloc[0],
                "start_date": g["game_date"].min(),
                "end_date": g["game_date"].max(),
                "games_in_window": games,
                "wins": wins,
                "losses": losses,
                "win_rate": (wins / (wins + losses)) if (wins + losses) else np.nan,
                "momentum_score": safe_sum(g["momentum_unit"]),
                "avg_pve": safe_mean(g["pve"]),
                "sum_pve": safe_sum(g["pve"]),
            }
        )

    out = lastn.groupby("team_name", as_index=False).apply(agg)
    # groupby+apply creates weird index sometimes
    out = out.reset_index(drop=True)
    return out

def pick_top(df, col, n=3, asc=False):
    if df.empty:
        return []
    d = df.sort_values(col, ascending=asc).copy()
    return d.head(n)["team_name"].tolist()

def main():
    df = pd.read_csv(INPUT_CSV)

    lastn = build_last_n(df, WINDOW)
    if lastn.empty:
        print("⚠️ No data available.")
        return

    summary = summarize_team(lastn)
    summary = summary[summary["games_in_window"] >= WINDOW].copy()
    if summary.empty:
        print("⚠️ Not enough games to build a momentum thread (need 10 per team).")
        return

    # Global window label (for sanity)
    global_start = summary["start_date"].min().date()
    global_end = summary["end_date"].max().date()

    # ---- Thresholds (simple + robust) ----
    # momentum_score: use quantiles so it scales naturally
    hi_m = summary["momentum_score"].quantile(0.80)
    lo_m = summary["momentum_score"].quantile(0.20)

    # win_rate: "good" and "bad"
    hi_wr = summary["win_rate"].quantile(0.70)
    lo_wr = summary["win_rate"].quantile(0.30)

    # PvE: positive vs negative (use 0, but also keep a small buffer)
    # buffer avoids tiny +/- 0.01 noise
    PVE_BUF = 0.25

    # ---- Categories ----
    riding = summary[(summary["momentum_score"] >= hi_m) & (summary["win_rate"] >= hi_wr)].copy()
    collapse = summary[(summary["momentum_score"] <= lo_m) & (summary["win_rate"] <= lo_wr)].copy()

    unlucky = summary[(summary["win_rate"] <= lo_wr) & (summary["avg_pve"] >= PVE_BUF)].copy()
    paper = summary[(summary["win_rate"] >= hi_wr) & (summary["avg_pve"] <= -PVE_BUF)].copy()

    # Ladder
    ladder = summary.sort_values(["momentum_score", "team_name"], ascending=[False, True]).copy()

    # ---- Tweet 1: Opening ----
    print(f"🧵 Weekly Momentum Check ({global_start} → {global_end}) — last {WINDOW} games\n")
    print(
        "📊 Momentum is short-term direction.\n\n"
        "We sum a game-by-game *momentum unit* built from Performance vs Expectation (PvE),\n"
        "with a small win–loss reality check.\n"
    )

    # ---- Tweet 2: Teams Riding the Wave ----
    if not riding.empty:
        print("🌊 Teams Riding the Wave\n")
        print("Big positive momentum *and* the wins to match.\n")
        riding = riding.sort_values("momentum_score", ascending=False).head(3)
        for _, r in riding.iterrows():
            print(f"{r['team_name']} — score: {fmt_float(r['momentum_score'])} | W–L: {fmt_wl(r['wins'], r['losses'])}")
        print()

    # ---- Tweet 3: Momentum Collapse Watch ----
    if not collapse.empty:
        print("🧨 Momentum Collapse Watch\n")
        print("Momentum is falling and the results are ugly.\n")
        collapse = collapse.sort_values("momentum_score", ascending=True).head(3)
        for _, r in collapse.iterrows():
            print(f"{r['team_name']} — score: {fmt_float(r['momentum_score'])} | W–L: {fmt_wl(r['wins'], r['losses'])}")
        print()

    # ---- Tweet 4: Unlucky Teams ----
    if not unlucky.empty:
        print("🍀 Unlucky Teams\n")
        print("Bad W–L, but PvE says they’ve played better than the outcomes.\n")
        unlucky = unlucky.sort_values(["avg_pve", "momentum_score"], ascending=[False, False]).head(3)
        for _, r in unlucky.iterrows():
            print(
                f"{r['team_name']} — W–L: {fmt_wl(r['wins'], r['losses'])} | "
                f"avg PvE: {fmt_float(r['avg_pve'])} | score: {fmt_float(r['momentum_score'])}"
            )
        print()

    # ---- Tweet 5: Paper Tigers ----
    if not paper.empty:
        print("📄 Paper Tigers\n")
        print("Good W–L, but PvE says the play hasn’t been as strong as the record.\n")
        paper = paper.sort_values(["avg_pve", "momentum_score"], ascending=[True, True]).head(3)
        for _, r in paper.iterrows():
            print(
                f"{r['team_name']} — W–L: {fmt_wl(r['wins'], r['losses'])} | "
                f"avg PvE: {fmt_float(r['avg_pve'])} | score: {fmt_float(r['momentum_score'])}"
            )
        print()

    # ---- Tweet 6: Full Momentum Ladder ----
    print("🪜 Full Momentum Ladder (best → worst)\n")
    for i, (_, r) in enumerate(ladder.iterrows(), start=1):
        print(f"{i}. {r['team_name']} — {fmt_float(r['momentum_score'])} | {fmt_wl(r['wins'], r['losses'])}")
        if i % 10 == 0 and i != len(ladder):
            print()  # line break every 10 for readability
    print()

    # ---- Tweet 7: Closing ----
    print(
        "Momentum isn’t a power ranking.\n"
        "It’s the *recent slope*.\n\n"
        "Ride it while it’s real, and watch for the snapback."
    )

if __name__ == "__main__":
    main()

