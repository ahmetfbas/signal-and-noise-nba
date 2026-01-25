from analysis.fli import main as run_fatigue
from analysis.pve import main as run_pve


def main():
    print("\n=== Fatigue & Load ===")
    run_fatigue()

    print("\n=== Performance vs Expectation ===")
    run_pve()


if __name__ == "__main__":
    main()
