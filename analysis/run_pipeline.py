def main():
    from analysis.build_team_game_metrics import main as build_metrics
    from analysis.build_pve import main as build_pve
    from analysis.build_rpmi import main as build_rpmi
    from analysis.build_cvv import main as build_cvv
    from analysis.build_game_environment import main as build_environment

    build_metrics()        # produces team_game_metrics.csv
    build_pve()            # produces team_game_metrics_with_pve.csv
    build_rpmi()           # produces team_game_metrics_with_rpmi.csv
    build_cvv()            # produces team_game_metrics_with_rpmi_cvv.csv
    build_environment()    # produces game_environment.csv


if __name__ == "__main__":
    main()
