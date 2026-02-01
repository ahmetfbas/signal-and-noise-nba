def main():
    """
    Master pipeline runner for Signal & Noise NBA project.
    Executes the full daily analysis stack in order:
      1. Ingest new games
      2. Build fatigue/load (FLI)
      3. Build performance vs expectation (PvE)
      4. Build rolling performance momentum index (RPMI)
      5. Build consistency–volatility view (CVV)
      6. Build game environment layer (for dashboards or AI)
    """

    import os

    # -----------------------------
    # 1️⃣  INGEST (Critical step)
    # -----------------------------
    from scripts.ingest.append_daily_games import main as ingest_games
    print("\n🚚 Step 1 — Ingesting new games...")
    ingest_games()

    # -----------------------------
    # 2️⃣  TEAM GAME METRICS (FLI)
    # -----------------------------
    from analysis.build_team_game_metrics import main as build_metrics
    print("⚙️  Step 2 — Building fatigue/load metrics...")
    build_metrics()

    # -----------------------------
    # 3️⃣  PERFORMANCE vs EXPECTATION (PvE)
    # -----------------------------
    from analysis.build_pve import main as build_pve
    print("📊 Step 3 — Calculating performance vs expectation...")
    build_pve()

    # PvE must exist to continue
    if not os.path.exists("data/derived/team_game_metrics_with_pve.csv"):
        raise FileNotFoundError("❌ PvE output missing — aborting pipeline.")

    # -----------------------------
    # 4️⃣  ROLLING PERFORMANCE MOMENTUM INDEX (RPMI)
    # -----------------------------
    from analysis.build_rpmi import main as build_rpmi
    print("📈 Step 4 — Computing rolling momentum index...")
    build_rpmi()

    # -----------------------------
    # 5️⃣  CONSISTENCY–VOLATILITY VIEW (CVV)
    # -----------------------------
    from analysis.build_cvv import main as build_cvv
    print("🧩 Step 5 — Deriving consistency & volatility layers...")
    build_cvv()

    # -----------------------------
    # 6️⃣  GAME ENVIRONMENT SUMMARY
    # -----------------------------
    from analysis.build_game_environment import main as build_environment
    print("🌍 Step 6 — Building game environment dataset...")
    build_environment()

    print("\n✅ Pipeline completed successfully!")


if __name__ == "__main__":
    main()
