"""Run Book G in order: G1 charter then peek, G2, G3. Stop on a non-PASS."""

from __future__ import annotations

from src.events.g1 import run_g1
from src.events.g2 import run_g2
from src.events.g3 import run_g3


def run_g_series() -> dict:
    g1 = run_g1(peek=True)
    auth = g1["authority"]
    if auth["verdict"] != "PASS":
        print(
            f"G1 verdict={auth['verdict']}. Book G stops. G2 and G3 not opened."
        )
        return {"g1": g1, "stopped_after": "G1"}
    g2 = run_g2(g1["measured"])
    if g2["authority"]["verdict"] != "PASS":
        print(
            f"G2 verdict={g2['authority']['verdict']}. Book G stops. G3 not opened."
        )
        return {"g1": g1, "g2": g2, "stopped_after": "G2"}
    g3 = run_g3(g1["measured"])
    return {"g1": g1, "g2": g2, "g3": g3, "stopped_after": None}


def main() -> None:
    run_g_series()


if __name__ == "__main__":
    main()
