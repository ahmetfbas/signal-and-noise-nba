import pandas as pd
from datetime import datetime, timezone

FACTS_CSV = "data/core/team_game_facts.csv"
METRICS_CSV = "data/derived/team_game_metrics_with_rpmi.csv"
WINDOW = 10


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
    # --- load facts (source of truth for games & W–L) ---
    facts = pd.read_csv(FACTS_CSV)
    facts["game_date"] = pd.to_datetime(facts["game_date"], utc=True, errors="coerce")
    facts = facts[facts["game_date"].notna()].copy()

    # ignore today & future (pre-game rule)
    today_utc = pd.Timestamp(datetime.now(timezone.utc).date(), tz="UTC")
    facts = facts[facts["game_date"] < today_utc]

    # derive margin for W–L
    facts["actual_margin"] = facts["team_points"] - facts["opponent_points"]

    # --- load metrics (source of momentum signal) ---
    metrics = pd.read_csv(METRICS_CSV)
    metrics["game_date"] = pd.to_datetime(metrics["game_date"], utc=True, errors="coerce")

    metrics = metrics[[
        "game_id",
        "team_name",
        "momentum_unit"
    ]]

    rows = []

    # ✅ GROUP BY TEAM NAME (critical fix)
    for team_name, g in facts.groupby("team_name"):
        g = g.sort_values("game_date")

        # last N REAL games
        recent_games = g.tail(WINDOW)
        if len(recent_games) < WINDOW:
            continue

        # W–L from facts only
        wins = (recent_games["actual_margin"] > 0).sum()
        losses = (recent_games["actual_margin"] < 0).sum()

        # attach momentum without affecting window
        merged = recent_games.merge(
            metrics,
            on=["game_id", "team_name"],
            how="left"
        )

        # momentum score (missing = 0)
        momentum_score = merged["momentum_unit"].fillna(0).sum()

        rows.append({
            "team_name": team_name,
            "score": round(momentum_score, 2),
            "wins": int(wins),
            "losses": int(losses),
            "label": momentum_label(momentum_score),
            "start_date": recent_games["game_date"].min().date(),
            "end_date": recent_games["game_date"].max().date(),
        })

    board = pd.DataFrame(rows).sort_values("score", ascending=False)

    if board.empty:
        print("No teams with sufficient data.")
        return

    print(
        f"\n🔄 Momentum Board ({board['start_date'].min()} → {board['end_date'].max()}) "
        f"— last {WINDOW} games\n"
        "Score: performance vs expectation, adjusted for win–loss reality.\n"
    )

    for _, r in board.iterrows():
        emoji = "🟢" if r["score"] >= 3 else "🟠" if r["score"] > -3 else "🔴"
        print(
            f"{emoji} {r['team_name']:<25} — {r['label']:<8} "
            f"| score: {r['score']:>6} | W–L: {r['wins']}-{r['losses']}"
        )


if __name__ == "__main__":
    main()
