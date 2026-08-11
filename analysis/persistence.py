"""The headline analysis: which trip channels persist as skills?

Three seasons, two adjacent transitions: per-transition and pooled
year-over-year correlations of per-channel generation rates, the two-year
lag (decay), the stayers-vs-movers context test pooled across both
transitions, and split-half (odd/even game) reliability within each season.

  python analysis/persistence.py
"""

from __future__ import annotations

import csv
import math
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib import (  # noqa: E402
    ANALYSIS, RESEARCH, TRIP_CLASSES, pearson, player_seasons, spearman,
)

SEASONS = ("2023-24", "2024-25", "2025-26")
PANEL_MIN_FGA = 300

METRICS = [
    ("ftaRate", "FTA rate (benchmark)"),
    ("conversion", "FT conversion (benchmark)"),
    ("tripsPer100Fga", "all trips /100 FGA"),
    ("shootingFoul2Per100Fga", "SF2 /100 FGA"),
    ("shootingFoul3Per100Fga", "SF3 /100 FGA"),
    ("bonusPer100Fga", "bonus /100 FGA"),
    ("andOnePer100Fga", "and-one /100 FGA"),
    ("otherAddonPer100Fga", "other add-on /100 FGA"),
    ("trueCoef", "true 0.44 coefficient"),
    ("premium", "line premium"),
]

CHANNEL_KEYS = [
    ("shootingFoul2Per100Fga", "SF2"),
    ("shootingFoul3Per100Fga", "SF3"),
    ("bonusPer100Fga", "bonus"),
    ("andOnePer100Fga", "and-one"),
    ("tripsPer100Fga", "all trips"),
]


def build_panel(prior: dict, current: dict) -> list[tuple[dict, dict]]:
    return [
        (prior[p], current[p])
        for p in sorted(set(prior) & set(current))
        if prior[p]["fga"] >= PANEL_MIN_FGA and current[p]["fga"] >= PANEL_MIN_FGA
        and prior[p].get("trips", 0) > 0 and current[p].get("trips", 0) > 0
    ]


def corr(panel: list[tuple[dict, dict]], key: str, method=pearson) -> float:
    xs = [a[key] for (a, b) in panel if key in a and key in b]
    ys = [b[key] for (a, b) in panel if key in a and key in b]
    return method(xs, ys)


def fisher_p(r1: float, n1: int, r2: float, n2: int) -> tuple[float, float]:
    z = (math.atanh(r1) - math.atanh(r2)) / math.sqrt(1 / (n1 - 3) + 1 / (n2 - 3))
    return z, math.erfc(abs(z) / math.sqrt(2))


def split_half_reliability(season: str, min_fga: int) -> dict[str, float]:
    """Odd/even game-ID split within a season: per-channel trip counts per
    half, correlated across qualified players, Spearman-Brown corrected."""
    players = player_seasons(season)
    qualified = {p for p, r in players.items() if r["fga"] >= min_fga}
    halves: dict[str, dict[int, list[int]]] = {
        c: defaultdict(lambda: [0, 0]) for c in TRIP_CLASSES
    }
    totals: dict[int, list[int]] = defaultdict(lambda: [0, 0])
    trips_path = RESEARCH / "data" / "derived" / season / "trips.csv"
    with trips_path.open(encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            player_id = int(row["player_id"])
            if player_id not in qualified:
                continue
            half = int(row["game_id"]) % 2
            halves[row["trip_class"]][player_id][half] += 1
            totals[player_id][half] += 1

    result: dict[str, float] = {}
    for label, counts in [("tripsPer100Fga", totals)] + [
        (f"{c}Per100Fga", halves[c]) for c in TRIP_CLASSES
    ]:
        xs, ys = [], []
        for player_id in qualified:
            a, b = counts.get(player_id, [0, 0])
            xs.append(a)
            ys.append(b)
        r = pearson(xs, ys)
        result[label] = 2 * r / (1 + r)
    return result


def main() -> None:
    by_season = {s: player_seasons(s) for s in SEASONS}
    transitions = [
        (SEASONS[0], SEASONS[1], build_panel(by_season[SEASONS[0]], by_season[SEASONS[1]])),
        (SEASONS[1], SEASONS[2], build_panel(by_season[SEASONS[1]], by_season[SEASONS[2]])),
    ]
    lag_panel = build_panel(by_season[SEASONS[0]], by_season[SEASONS[2]])
    pooled = transitions[0][2] + transitions[1][2]

    out: list[str] = []
    o = out.append
    o(f"# Channel persistence across three seasons ({SEASONS[0]} … {SEASONS[2]})")
    o("")
    sizes = " · ".join(f"{a}→{b}: {len(panel)}" for a, b, panel in transitions)
    o(f"Panels (≥{PANEL_MIN_FGA} FGA and ≥1 trip both seasons): {sizes} · "
      f"pooled player-transitions: {len(pooled)} · two-year lag "
      f"({SEASONS[0]}→{SEASONS[2]}): {len(lag_panel)}")
    o("")

    reliability = {s: split_half_reliability(s, PANEL_MIN_FGA) for s in SEASONS}

    o("## Year-over-year persistence, per transition and pooled")
    o("")
    o(f"| metric | {transitions[0][0]}→{transitions[0][1]} "
      f"| {transitions[1][0]}→{transitions[1][1]} | pooled r | pooled ρ "
      f"| split-half (3-season range) |")
    o("|---|--:|--:|--:|--:|--:|")
    for key, label in METRICS:
        r1 = corr(transitions[0][2], key)
        r2 = corr(transitions[1][2], key)
        rp = corr(pooled, key)
        rho = corr(pooled, key, spearman)
        rels = [reliability[s].get(key) for s in SEASONS]
        rel_txt = ("—" if all(v is None for v in rels) else
                   f"{min(v for v in rels if v is not None):.2f}–"
                   f"{max(v for v in rels if v is not None):.2f}")
        o(f"| {label} | {r1:.3f} | {r2:.3f} | {rp:.3f} | {rho:.3f} | {rel_txt} |")
    o("")

    o("## Decay: adjacent-season vs two-year-lag correlation")
    o("")
    o("| channel | adjacent (pooled) | two-year lag | retention |")
    o("|---|--:|--:|--:|")
    for key, label in CHANNEL_KEYS:
        adj = corr(pooled, key)
        lag = corr(lag_panel, key)
        o(f"| {label} | {adj:.3f} | {lag:.3f} | {lag / adj:.0%} |")
    o("")

    o("## The context test, pooled across both transitions")
    o("")
    stayers, movers = [], []
    for _, _, panel in transitions:
        for a, b in panel:
            if a["team"] == b["team"] and a["team"] != "TOT" and b["team"] != "TOT":
                stayers.append((a, b))
            else:
                movers.append((a, b))
    o(f"Stayer transitions: {len(stayers)} · mover transitions: {len(movers)}")
    o("")
    o("| channel | stayers r | movers r | gap | Fisher z | p (two-sided) |")
    o("|---|--:|--:|--:|--:|--:|")
    for key, label in CHANNEL_KEYS:
        rs = corr(stayers, key)
        rm = corr(movers, key)
        z, p = fisher_p(rs, len(stayers), rm, len(movers))
        o(f"| {label} | {rs:.3f} | {rm:.3f} | {rs - rm:+.3f} | {z:.2f} | {p:.3f} |")
    o("")

    o("## Channel-mix stability (share of trips, pooled)")
    o("")
    o("| share | r | ρ |")
    o("|---|--:|--:|")
    for cls, label in [
        ("shootingFoul2Share", "SF2"), ("shootingFoul3Share", "SF3"),
        ("bonusShare", "bonus"), ("andOneShare", "and-one"),
    ]:
        o(f"| {label} | {corr(pooled, cls):.3f} | {corr(pooled, cls, spearman):.3f} |")

    report = "\n".join(out)
    out_path = ANALYSIS / "output" / "persistence.md"
    out_path.write_text(report, encoding="utf-8")
    print(report)
    print(f"\nreport -> {out_path}")


if __name__ == "__main__":
    main()
