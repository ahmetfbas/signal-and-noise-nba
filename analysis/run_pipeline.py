def main():
    """
    Master pipeline runner for Signal & Noise NBA project.
    """

    import os

    # -----------------------------
    # 1️⃣ INGEST
    # -----------------------------
    from scripts.ingest.append_daily_games import main as ingest_games
    print("\n🚚 Step 1 — Ingesting new games...")
    ingest_games()

    # -----------------------------
    # 2️⃣ TEAM GAME METRICS
    # -----------------------------
    from analysis.build_team_game_metrics import main as build_metrics
    print("⚙️  Step 2 — Building fatigue / load metrics...")
    build_metrics()

    # -----------------------------
    # 3️⃣ PvE
    # -----------------------------
    from analysis.build_pve import main as build_pve
    print("📊 Step 3 — Calculating performance vs expectation...")
    build_pve()

    # -----------------------------
    # 4️⃣ RPMI
    # -----------------------------
    from analysis.build_rpmi import main as build_rpmi
    print("📈 Step 4 — Computing rolling momentum index...")
    build_rpmi()

    # -----------------------------
    # 5️⃣ CVV
    # -----------------------------
    from analysis.build_cvv import main as build_cvv
    print("🧩 Step 5 — Deriving consistency & volatility layers...")
    build_cvv()

    # -----------------------------
    # 6️⃣ SEASON ARCHETYPES (NEW, REQUIRED)
    # -----------------------------
    from analysis.build_archetypes import main as build_archetypes
    print("🧠 Step 6 — Building season team identities...")
    build_archetypes()

    if not os.path.exists("data/derived/team_game_metrics_with_archetypes.csv"):
        raise FileNotFoundError("❌ Archetype output missing — aborting pipeline.")

    # -----------------------------
    # 7️⃣ PREGAME ENVIRONMENT (FIXED)
    # -----------------------------
    from analysis.build_pregame_environment import main as build_environment
    print("🌍 Step 7 — Building pregame environment dataset...")
    build_environment()

    if not os.path.exists("data/derived/game_environment_pregame.csv"):
        raise FileNotFoundError("❌ Pregame environment output missing.")

    print("\n✅ Pipeline completed successfully!")

if __name__ == "__main__":
    main()
