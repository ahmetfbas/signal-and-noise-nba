def main():
    # INGEST (CRITICAL)
    from scripts.ingest.append_daily_games import main as ingest_games

    # ANALYSIS
    from analysis.build_team_game_metrics import main as build_metrics
    from analysis.build_pve import main as build_pve
    from analysis.build_rpmi import main as build_rpmi
    from analysis.build_cvv import main as build_cvv
    from analysis.build_game_environment import main as build_environment

    ingest_games()         # updates raw data
    build_metrics()
    build_pve()
    build_rpmi()
    build_cvv()
    build_environment()


if __name__ == "__main__":
    main()
