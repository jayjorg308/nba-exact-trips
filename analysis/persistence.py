"""The headline analysis: which trip channels persist as skills?

Year-over-year correlation of per-channel generation rates across the
two-season player panel, benchmarked against the known-stable quantities
(overall FTA rate, FT conversion), plus a split-half (odd/even game)
reliability check within each season.

  python analysis/persistence.py
"""

from __future__ import annotations

import csv
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib import (  # noqa: E402
    ANALYSIS, RESEARCH, TRIP_CLASSES, pearson, player_seasons, spearman,
)

SEASONS = ("2024-25", "2025-26")
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
        result[label] = 2 * r / (1 + r)  # Spearman-Brown, half -> full length
    return result


def main() -> None:
    prior = player_seasons(SEASONS[0])
    current = player_seasons(SEASONS[1])
    panel = [
        (prior[p], current[p])
        for p in sorted(set(prior) & set(current))
        if prior[p]["fga"] >= PANEL_MIN_FGA and current[p]["fga"] >= PANEL_MIN_FGA
        and prior[p].get("trips", 0) > 0 and current[p].get("trips", 0) > 0
    ]

    out: list[str] = []
    o = out.append
    o(f"# Channel persistence, {SEASONS[0]} -> {SEASONS[1]}")
    o("")
    o(f"Panel: {len(panel)} players with ≥{PANEL_MIN_FGA} FGA and ≥1 trip in "
      f"both seasons. Split-half reliability: odd/even game-ID halves within "
      f"each season, Spearman-Brown corrected, same FGA bar.")
    o("")

    sh_prior = split_half_reliability(SEASONS[0], PANEL_MIN_FGA)
    sh_current = split_half_reliability(SEASONS[1], PANEL_MIN_FGA)

    o("| metric | year-over-year r | Spearman ρ | split-half "
      f"{SEASONS[0]} | split-half {SEASONS[1]} |")
    o("|---|--:|--:|--:|--:|")
    for key, label in METRICS:
        xs = [a[key] for (a, b) in panel if key in a and key in b]
        ys = [b[key] for (a, b) in panel if key in a and key in b]
        r = pearson(xs, ys)
        rho = spearman(xs, ys)
        sh_a = sh_prior.get(key)
        sh_b = sh_current.get(key)
        o(f"| {label} | {r:.3f} | {rho:.3f} | "
          f"{'—' if sh_a is None else f'{sh_a:.3f}'} | "
          f"{'—' if sh_b is None else f'{sh_b:.3f}'} |")
    o("")

    o("## Channel-mix stability (share of trips, year over year)")
    o("")
    o("| share | r | ρ |")
    o("|---|--:|--:|")
    for cls, label in [
        ("shootingFoul2Share", "SF2"), ("shootingFoul3Share", "SF3"),
        ("bonusShare", "bonus"), ("andOneShare", "and-one"),
    ]:
        xs = [a[cls] for (a, b) in panel]
        ys = [b[cls] for (a, b) in panel]
        o(f"| {label} | {pearson(xs, ys):.3f} | {spearman(xs, ys):.3f} |")
    o("")

    o("## Biggest year-over-year movers (all trips per 100 FGA)")
    o("")
    movers = sorted(panel, key=lambda ab: ab[1]["tripsPer100Fga"] - ab[0]["tripsPer100Fga"])
    for a, b in movers[-6:][::-1]:
        o(f"- {b['name']} ({b['team']}): {a['tripsPer100Fga']:.1f} -> "
          f"{b['tripsPer100Fga']:.1f}")
    o("")
    for a, b in movers[:6]:
        o(f"- {b['name']} ({b['team']}): {a['tripsPer100Fga']:.1f} -> "
          f"{b['tripsPer100Fga']:.1f}")

    report = "\n".join(out)
    out_path = ANALYSIS / "output" / "persistence.md"
    out_path.parent.mkdir(exist_ok=True)
    out_path.write_text(report, encoding="utf-8")
    print(report)
    print(f"\nreport -> {out_path}")


if __name__ == "__main__":
    main()
