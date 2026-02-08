import pandas as pd

INPUT_CSV = "data/derived/team_game_metrics_with_rpmi.csv"
WINDOW = 10


def win_loss_multiplier(win_rate: float) -> float:
    if win_rate < 0.40:
        return 0.50
    if win_rate < 0.50:
        return 0.75
    if win_rate < 0.65:
        return 1.00
    return 1.15


def momentum_label(score: float) -> str:
    if score >= 8:
        return "Strong"
    if score >= 3:
        return "Positive"
    if score > -3:
        return "Flat"
    if score > -8:
        return "Fading"
    return "Falling"


def main():
    df = pd.read_csv(INPUT_CSV)

    df["team_id"] = df["team_id"].astype(int)
    df["game_date"] = pd.to_datetime(df["game_date"], errors="coerce", utc=True)
    df = df[df["game_date"].notna()].copy()

    rows = []

    for team_id, g in df.groupby("team_id"):
        g = g.sort_values("game_date")

        recent = g[g["momentum_unit"].notna()].tail(WINDOW)
        if len(recent) < WINDOW:
            continue

        wins = (recent["actual_margin"] > 0).sum()
        losses = (recent["actual_margin"] < 0).sum()
        total = wins + losses

        if total == 0:
            continue

        win_rate = wins / total
        raw_score = recent["momentum_unit"].sum()
        adjusted_score = raw_score * win_loss_multiplier(win_rate)

        rows.append({
            "team_name": recent.iloc[-1]["team_name"],
            "raw_score": round(raw_score, 2),
            "score": round(adjusted_score, 2),
            "wins": wins,
            "losses": losses,
            "games": total,
            "label": momentum_label(adjusted_score),
            "start_date": recent.iloc[0]["game_date"].date(),
            "end_date": recent.iloc[-1]["game_date"].date(),
        })

    board = pd.DataFrame(rows).sort_values("score", ascending=False)

    start = board["start_date"].min()
    end = board["end_date"].max()

    print(f"🔄 Momentum Board ({start} → {end}) — last {WINDOW} games")
    print("Score: performance vs expectation, adjusted for win–loss reality.\n")

    for _, r in board.iterrows():
        icon = "🟢" if r["score"] > 0 else "🟠" if r["score"] > -3 else "🔴"
        print(
            f"{icon} {r['team_name']:<25} — {r['label']:<8} "
            f"| score: {r['score']:>6} "
            f"| W–L: {r['wins']}-{r['losses']}"
        )


if __name__ == "__main__":
    main()
