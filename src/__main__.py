"""`poetry run python -m src` — package sanity check, no strategy work."""

from src import __version__


def main() -> None:
    print(f"algo-trade-platform {__version__}")


if __name__ == "__main__":
    main()
