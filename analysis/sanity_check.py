import pandas as pd
import numpy as np

CSV_PATH = "data/derived/team_game_metrics_with_rpmi_cvv.csv"
WINDOW = 5
VOL_SCALE = 10
EPS = 0.05  # tolerance for float checks


def header(title):
    print("\n" + "=" * 60)
    print(title)
    print("=" * 60)


def load_data():
    df = pd.read_csv(CSV_PATH)
    df["game_date"] = pd.to_datetime(df["game_date"])
    return df


def check_rows_per_game(df):
    header("1) GAME ROW INTEGRITY (2 rows per game)")
    counts = df.groupby("game_id").size()
    bad = counts[counts != 2]
    print(f"Total games: {counts.shape[0]}")
    print(f"Games with !=2 rows: {len(bad)}")
    if len(bad) == 0:
        print("PASS")
    else:
        print("FAIL")
        print(bad.head())


def check_margin_symmetry(df):
    header("2) MARGIN SYMMETRY CHECK")
    g = df.groupby("game_id")[["actual_margin", "expected_margin", "pve"]].sum()
    max_actual = g["actual_margin"].abs().max()
    max_expected = g["expected_margin"].abs().max()
    max_pve = g["pve"].abs().max()

    print("Max abs(sum actual_margin):", round(max_actual, 4))
    print("Max abs(sum expected_margin):", round(max_expected, 4))
    print("Max abs(sum pve):", round(max_pve, 4))

    if max(max_actual, max_expected, max_pve) < EPS:
        print("PASS")
    else:
        print("FAIL")


def check_pve_identity(df):
    header("3) PvE IDENTITY CHECK (actual - expected = pve)")
    diff = (df["actual_margin"] - df["expected_margin"] - df["pve"]).abs()
    print("Max absolute error:", round(diff.max(), 4))
    print("Rows with error > EPS:", (diff > EPS).sum())
    print("PASS" if diff.max() < EPS else "FAIL")


def check_expected_breakdown(df):
    header("4) EXPECTED MARGIN COMPONENT CHECK")
    calc = df["base_form_diff"] + df["home_away_adj"] + df["fatigue_adj"]
    err = (df["expected_margin"] - calc).abs()

    print("Max absolute component error:", round(err.max(), 4))
    print("Rows with error > EPS:", (err > EPS).sum())
    print("PASS" if err.max() < EPS else "FAIL")


def check_fatigue_ranges(df):
    header("5) FATIGUE RANGE & LOGIC CHECK")
    print(df["fatigue_index"].describe())
    bad7 = df[df["games_last_7"] > 7]
    bad14 = df[df["games_last_14"] > 14]

    print("games_last_7 > 7:", len(bad7))
    print("games_last_14 > 14:", len(bad14))
    print("PASS" if len(bad7) == 0 and len(bad14) == 0 else "FAIL")


def recompute_cvv(df):
    header("6) CvV RECOMPUTATION CHECK")
    df = df.sort_values(["team_id", "game_date"]).copy()

    vol_err = []
    cons_err = []

    for _, g in df.groupby("team_id"):
        pve = g["pve"].values
        idx = g.index.values

        for i in range(WINDOW - 1, len(g)):
            window = pve[i - WINDOW + 1 : i + 1]
            vol = round(np.std(window, ddof=0), 2)
            cons = round(1 / (1 + (vol / VOL_SCALE)), 3)

            vol_err.append(abs(df.loc[idx[i], "pve_volatility"] - vol))
            cons_err.append(abs(df.loc[idx[i], "consistency"] - cons))

    print("Max volatility diff:", round(max(vol_err), 4))
    print("Max consistency diff:", round(max(cons_err), 4))
    print("PASS" if max(vol_err) < EPS and max(cons_err) < EPS else "FAIL")


def check_distribution_sanity(df):
    header("7) DISTRIBUTION SANITY CHECK")
    print("\nPvE:")
    print(df["pve"].describe())
    print("\nRPMI:")
    print(df["rpmi"].describe())
    print("\nVolatility:")
    print(df["pve_volatility"].describe())
    print("\nConsistency:")
    print(df["consistency"].describe())
    print("\n(Manual inspection — looking for reasonable spread)")


def main():
    df = load_data()
    check_rows_per_game(df)
    check_margin_symmetry(df)
    check_pve_identity(df)
    check_expected_breakdown(df)
    check_fatigue_ranges(df)
    recompute_cvv(df)
    check_distribution_sanity(df)

    print("\nSANITY CHECK COMPLETE")


if __name__ == "__main__":
    main()
