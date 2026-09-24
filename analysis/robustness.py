"""Robustness for the persistence result, pooled over both season
transitions (2023-24→2024-25, 2024-25→2025-26):

1. Panel-threshold sensitivity — the gradient at FGA bars 200/300/400.
2. Exposure basis — per-36-minutes rates beside per-100-FGA.
3. The context test — if bonus generation carries a team-context component,
   players who CHANGED teams between seasons should persist less than
   players who stayed. Groups come from game-level team history; a
   midseason change in either season is 'mixed' and excluded (then folded
   into movers as a sensitivity). The FGA≥300 row of this test also
   appears in persistence.py's report; the two must agree.
4. The context test at each FGA bar — how the bonus gap and its
   uncertainty move with panel size.

  python analysis/robustness.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib import (  # noqa: E402
    ANALYSIS, TRIP_CLASSES, bootstrap_gap, build_panel, classify_transition,
    corr, fisher_p, player_seasons,
)

SEASONS = ("2023-24", "2024-25", "2025-26")

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


def split_groups(panel: list[tuple[dict, dict]]) -> dict[str, list[tuple[dict, dict]]]:
    groups: dict[str, list[tuple[dict, dict]]] = {"stayer": [], "mover": [], "mixed": []}
    for a, b in panel:
        groups[classify_transition(a, b)].append((a, b))
    return groups


def main() -> None:
    by_season = {s: player_seasons(s) for s in SEASONS}
    for players in by_season.values():
        for record in players.values():
            add_per36(record)
    pairs = list(zip(SEASONS, SEASONS[1:]))

    def pooled_panel(min_fga: int) -> list[tuple[dict, dict]]:
        panel: list[tuple[dict, dict]] = []
        for earlier, later in pairs:
            panel += build_panel(by_season[earlier], by_season[later], min_fga)
        return panel

    out: list[str] = []
    o = out.append
    o("# Robustness: the persistence gradient "
      f"(pooled transitions, {SEASONS[0]} … {SEASONS[-1]})")
    o("")

    o("## 1. Panel-threshold sensitivity (per 100 FGA)")
    o("")
    o("| channel | FGA≥200 | FGA≥300 | FGA≥400 |")
    o("|---|--:|--:|--:|")
    panels = {bar: pooled_panel(bar) for bar in (200, 300, 400)}
    o(f"| _pooled transitions_ | {len(panels[200])} | {len(panels[300])} "
      f"| {len(panels[400])} |")
    for cls, label in CHANNELS + [(None, "all trips")]:
        key = f"{cls}Per100Fga" if cls else "tripsPer100Fga"
        cells = " | ".join(f"{corr(panels[bar], key):.3f}" for bar in (200, 300, 400))
        o(f"| {label} | {cells} |")
    o("")

    o("## 2. Exposure basis (pooled, FGA≥300)")
    o("")
    o("| channel | per 100 FGA | per 36 min |")
    o("|---|--:|--:|")
    panel = panels[300]
    for cls, label in CHANNELS + [(None, "all trips")]:
        k_fga = f"{cls}Per100Fga" if cls else "tripsPer100Fga"
        k_min = f"{cls}Per36" if cls else "tripsPer36"
        o(f"| {label} | {corr(panel, k_fga):.3f} | {corr(panel, k_min):.3f} |")
    o("")

    o("## 3. The context test — stayers vs team-changers (pooled, FGA≥300)")
    o("")
    groups = split_groups(panel)
    stayers, movers, mixed = groups["stayer"], groups["mover"], groups["mixed"]
    o(f"Stayer transitions: {len(stayers)} · mover transitions: {len(movers)} "
      f"· mixed (midseason change, excluded): {len(mixed)}")
    o("")
    o("| channel | stayers r | movers r | gap | Fisher z | p (two-sided) | bootstrap 95% CI |")
    o("|---|--:|--:|--:|--:|--:|--:|")
    for cls, label in CHANNELS + [(None, "all trips")]:
        key = f"{cls}Per100Fga" if cls else "tripsPer100Fga"
        rs, rm = corr(stayers, key), corr(movers, key)
        z, p = fisher_p(rs, len(stayers), rm, len(movers))
        lo, hi, _ = bootstrap_gap(stayers, movers, key)
        o(f"| {label} | {rs:.3f} | {rm:.3f} | {rs - rm:+.3f} | {z:.2f} | {p:.3f} "
          f"| [{lo:+.3f}, {hi:+.3f}] |")
    o("")
    o("Mixed folded into movers:")
    o("")
    o("| channel | stayers r | movers+mixed r | gap | p (two-sided) |")
    o("|---|--:|--:|--:|--:|")
    movers_plus = movers + mixed
    for cls, label in CHANNELS + [(None, "all trips")]:
        key = f"{cls}Per100Fga" if cls else "tripsPer100Fga"
        rs, rm = corr(stayers, key), corr(movers_plus, key)
        _, p = fisher_p(rs, len(stayers), rm, len(movers_plus))
        o(f"| {label} | {rs:.3f} | {rm:.3f} | {rs - rm:+.3f} | {p:.3f} |")
    o("")

    o("## 4. The context test at each FGA bar (mixed excluded)")
    o("")
    o("| FGA bar | stayers / movers | SF2 gap (p) | bonus gap (p) | bonus bootstrap 95% CI |")
    o("|---|--:|--:|--:|--:|")
    for bar in (200, 300, 400):
        g = split_groups(panels[bar])
        cells = []
        for cls in ("shootingFoul2", "bonus"):
            key = f"{cls}Per100Fga"
            rs, rm = corr(g["stayer"], key), corr(g["mover"], key)
            _, p = fisher_p(rs, len(g["stayer"]), rm, len(g["mover"]))
            cells.append(f"{rs - rm:+.3f} ({p:.3f})")
        lo, hi, _ = bootstrap_gap(g["stayer"], g["mover"], "bonusPer100Fga")
        o(f"| ≥{bar} | {len(g['stayer'])} / {len(g['mover'])} | {cells[0]} | {cells[1]} "
          f"| [{lo:+.3f}, {hi:+.3f}] |")

    report = "\n".join(out)
    out_path = ANALYSIS / "output" / "robustness.md"
    out_path.write_text(report, encoding="utf-8")
    print(report)
    print(f"\nreport -> {out_path}")


if __name__ == "__main__":
    main()
