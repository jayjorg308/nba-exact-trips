"""Robustness for the persistence result:

1. Panel-threshold sensitivity — the gradient at FGA bars 200/300/400.
2. Exposure basis — per-36-minutes rates beside per-100-FGA.
3. The context test — if bonus generation carries a team-context component,
   players who CHANGED teams between seasons should persist less than
   players who stayed. (TOT rows count as movers; a mid-season trade is a
   context change.)

  python analysis/robustness.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import math

from lib import ANALYSIS, TRIP_CLASSES, pearson, player_seasons  # noqa: E402

SEASONS = ("2024-25", "2025-26")

CHANNELS = [
    ("shootingFoul2", "SF2"),
    ("shootingFoul3", "SF3"),
    ("bonus", "bonus"),
    ("andOne", "and-one"),
]


def add_per36(record: dict) -> None:
    if record["min"] > 0:
        for c in TRIP_CLASSES:
            record[f"{c}Per36"] = 36 * record["n"][c] / record["min"]
        record["tripsPer36"] = 36 * record["trips"] / record["min"]


def build_panel(prior: dict, current: dict, min_fga: int) -> list[tuple[dict, dict]]:
    return [
        (prior[p], current[p])
        for p in sorted(set(prior) & set(current))
        if prior[p]["fga"] >= min_fga and current[p]["fga"] >= min_fga
        and prior[p].get("trips", 0) > 0 and current[p].get("trips", 0) > 0
    ]


def corr(panel: list[tuple[dict, dict]], key: str) -> float:
    xs = [a[key] for (a, b) in panel if key in a and key in b]
    ys = [b[key] for (a, b) in panel if key in a and key in b]
    return pearson(xs, ys)


def main() -> None:
    prior = player_seasons(SEASONS[0])
    current = player_seasons(SEASONS[1])
    for record in list(prior.values()) + list(current.values()):
        add_per36(record)

    out: list[str] = []
    o = out.append
    o("# Robustness: the persistence gradient")
    o("")

    o("## 1. Panel-threshold sensitivity (per 100 FGA)")
    o("")
    o("| channel | FGA≥200 | FGA≥300 | FGA≥400 |")
    o("|---|--:|--:|--:|")
    panels = {bar: build_panel(prior, current, bar) for bar in (200, 300, 400)}
    o(f"| _panel size_ | {len(panels[200])} | {len(panels[300])} | {len(panels[400])} |")
    for cls, label in CHANNELS + [(None, "all trips")]:
        key = f"{cls}Per100Fga" if cls else "tripsPer100Fga"
        cells = " | ".join(f"{corr(panels[bar], key):.3f}" for bar in (200, 300, 400))
        o(f"| {label} | {cells} |")
    o("")

    o("## 2. Exposure basis (panel FGA≥300)")
    o("")
    o("| channel | per 100 FGA | per 36 min |")
    o("|---|--:|--:|")
    panel = panels[300]
    for cls, label in CHANNELS + [(None, "all trips")]:
        k_fga = f"{cls}Per100Fga" if cls else "tripsPer100Fga"
        k_min = f"{cls}Per36" if cls else "tripsPer36"
        o(f"| {label} | {corr(panel, k_fga):.3f} | {corr(panel, k_min):.3f} |")
    o("")

    o("## 3. The context test — stayers vs team-changers (FGA≥300)")
    o("")
    stayers = [(a, b) for (a, b) in panel
               if a["team"] == b["team"] and a["team"] != "TOT" and b["team"] != "TOT"]
    movers = [(a, b) for (a, b) in panel if (a, b) not in stayers]
    o(f"Stayers: {len(stayers)} · Movers (incl. any TOT season): {len(movers)}")
    o("")
    o("| channel | stayers r | movers r | gap | Fisher z | p (two-sided) |")
    o("|---|--:|--:|--:|--:|--:|")
    for cls, label in CHANNELS + [(None, "all trips")]:
        key = f"{cls}Per100Fga" if cls else "tripsPer100Fga"
        rs = corr(stayers, key)
        rm = corr(movers, key)
        z = (math.atanh(rs) - math.atanh(rm)) / math.sqrt(
            1 / (len(stayers) - 3) + 1 / (len(movers) - 3)
        )
        p = math.erfc(abs(z) / math.sqrt(2))
        o(f"| {label} | {rs:.3f} | {rm:.3f} | {rs - rm:+.3f} | {z:.2f} | {p:.3f} |")

    report = "\n".join(out)
    out_path = ANALYSIS / "output" / "robustness.md"
    out_path.write_text(report, encoding="utf-8")
    print(report)
    print(f"\nreport -> {out_path}")


if __name__ == "__main__":
    main()
