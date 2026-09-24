"""The two abstract exhibits, reproducible from the dataset.

Exhibit 1 (figure): the persistence gradient with the context test — per
channel, year-over-year correlation for players who stayed on their team vs
players who changed teams, with the within-season (split-half) reliability
ceiling as a muted tick. One axis; channels ordered by overall persistence.

Exhibit 2 (table): the trip taxonomy in one table — tier, league volume,
rate distribution, and both stability measures per channel.

  python analysis/exhibits.py
"""

from __future__ import annotations

import csv
import math
import sys
from collections import defaultdict
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib import (  # noqa: E402
    ANALYSIS, RESEARCH, build_panel, classify_transition, corr, player_seasons,
    quantiles, split_half_reliability,
)

SEASONS = ("2023-24", "2024-25", "2025-26")
PANEL_MIN_FGA = 300

# Reference palette (dataviz skill defaults), light mode.
SURFACE = "#fcfcfb"
INK = "#0b0b0b"
INK_SECONDARY = "#52514e"
MUTED = "#898781"
GRID = "#e1e0d9"
BASELINE = "#c3c2b7"
STAYERS = "#2a78d6"  # slot 1
MOVERS = "#eb6834"   # slot 2

CHANNELS = [
    ("shootingFoul2", "Two-shot shooting fouls", "attempt-equivalent"),
    ("andOne", "And-ones", "add-on"),
    ("shootingFoul3", "Three-shot shooting fouls", "attempt-equivalent"),
    ("bonus", "Bonus (non-shooting)", "attempt-equivalent"),
]


def main() -> None:
    by_season = {s: player_seasons(s) for s in SEASONS}
    panel = []
    for earlier, later in zip(SEASONS, SEASONS[1:]):
        panel += build_panel(by_season[earlier], by_season[later], PANEL_MIN_FGA)
    groups: dict[str, list] = {"stayer": [], "mover": [], "mixed": []}
    for a, b in panel:
        groups[classify_transition(a, b)].append((a, b))
    stayers, movers, mixed = groups["stayer"], groups["mover"], groups["mixed"]
    reliability = split_half_reliability(SEASONS[-1], PANEL_MIN_FGA)
    current = by_season[SEASONS[-1]]

    rows = []
    for cls, label, tier in CHANNELS:
        key = f"{cls}Per100Fga"
        rows.append({
            "cls": cls,
            "label": label,
            "tier": tier,
            "overall": corr(panel, key),
            "stayers": corr(stayers, key),
            "movers": corr(movers, key),
            "reliability": reliability.get(key),
        })
    rows.sort(key=lambda r: -r["overall"])

    # ---- Exhibit 1: the figure -------------------------------------------
    fig, ax = plt.subplots(figsize=(8.2, 4.0), dpi=200)
    fig.patch.set_facecolor(SURFACE)
    ax.set_facecolor(SURFACE)

    ys = list(range(len(rows)))[::-1]
    for y, row in zip(ys, rows):
        ax.plot([row["movers"], row["stayers"]], [y, y],
                color=BASELINE, linewidth=2, zorder=1, solid_capstyle="round")
        ax.plot([row["reliability"]], [y], marker="|", markersize=16,
                markeredgewidth=2, color=MUTED, zorder=2)
        ax.plot([row["stayers"]], [y], "o", markersize=9, color=STAYERS,
                markeredgecolor=SURFACE, markeredgewidth=2, zorder=3)
        ax.plot([row["movers"]], [y], "o", markersize=9, color=MOVERS,
                markeredgecolor=SURFACE, markeredgewidth=2, zorder=3)
        ax.text(0.02, y, row["label"], ha="left", va="center",
                fontsize=10.5, color=INK)

    # The key lives on the bonus row, where the two groups separate.
    bonus_y, bonus_row = next((y, r) for y, r in zip(ys, rows)
                              if r["cls"] == "bonus")
    ax.text(bonus_row["movers"], bonus_y + 0.28, "changed teams",
            ha="center", va="bottom", fontsize=9.5, color=MOVERS)
    ax.text(bonus_row["stayers"], bonus_y + 0.28, "stayed on team",
            ha="center", va="bottom", fontsize=9.5, color=STAYERS)
    rel_y = ys[1]
    ax.annotate("within-season reliability\n(the measurement ceiling)",
                (rows[1]["reliability"], rel_y),
                xytext=(rows[1]["reliability"] + 0.015, rel_y - 0.35),
                ha="left", va="top", fontsize=8.5, color=MUTED)

    # Per-row stayer-vs-mover gap significance (robustness.py's Fisher z).
    se = math.sqrt(1 / (len(stayers) - 3) + 1 / (len(movers) - 3))
    for y, row in zip(ys, rows):
        z = (math.atanh(row["stayers"]) - math.atanh(row["movers"])) / se
        p = math.erfc(abs(z) / math.sqrt(2))
        mid = (row["stayers"] + row["movers"]) / 2
        if row["cls"] == "bonus":
            ax.text(mid, y - 0.42, f"context gap p = {p:.3f}".replace("0.", ".", 1),
                    ha="center", fontsize=9, color=INK_SECONDARY)
        else:
            ax.text(mid, y - 0.34, f"gap p = {p:.2f}".replace("0.", ".", 1),
                    ha="center", fontsize=8, color=MUTED)

    ax.set_xlim(0, 1.0)
    ax.set_ylim(-0.9, len(rows) - 0.55)
    ax.set_yticks([])
    ax.set_xticks([0, 0.2, 0.4, 0.6, 0.8, 1.0])
    ax.tick_params(axis="x", colors=MUTED, labelsize=9)
    ax.grid(axis="x", color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)
    for spine in ("top", "right", "left"):
        ax.spines[spine].set_visible(False)
    ax.spines["bottom"].set_color(BASELINE)
    ax.set_xlabel("Year-over-year correlation of trip generation per 100 FGA "
                  f"(pooled transitions, {SEASONS[0]} … {SEASONS[-1]})",
                  fontsize=9.5, color=INK_SECONDARY)
    ax.set_title("Foul-drawing channels persist differentially, and the "
                 "non-shooting bonus channel persists least",
                 fontsize=11.5, color=INK, loc="left", pad=46)
    ax.text(0, 1.045,
            "Each dot: the correlation between a player's rate in one "
            "season and the next, computed separately over\n"
            f"player-season pairs where he stayed with one team (blue, "
            f"n = {len(stayers)}) and where he changed teams between\n"
            f"seasons (orange, n = {len(movers)}); {len(mixed)} pairs with "
            "a midseason move are excluded.",
            transform=ax.transAxes, fontsize=8.6, color=INK_SECONDARY,
            va="bottom", linespacing=1.4)
    fig.tight_layout()
    fig_path = ANALYSIS / "output" / "exhibit1-persistence.png"
    fig.savefig(fig_path, facecolor=SURFACE, bbox_inches="tight")
    print(f"exhibit 1 -> {fig_path}")

    # ---- Exhibit 2: the table --------------------------------------------
    league_trips: dict[str, int] = defaultdict(int)
    with (RESEARCH / "data" / "derived" / SEASONS[-1] / "trips.csv").open(
        encoding="utf-8"
    ) as handle:
        for row in csv.DictReader(handle):
            league_trips[row["trip_class"]] += 1
    qualified = [r for r in current.values()
                 if r["fga"] >= PANEL_MIN_FGA and r.get("trips", 0) > 0]

    out = []
    o = out.append
    o(f"# Exhibit 2 — the trip taxonomy, measured ({SEASONS[-1]} volume, rates, "
      f"and split-half reliability; year-over-year r pooled over {SEASONS[0]} … "
      f"{SEASONS[-1]})")
    o("")
    o("| channel | tier | league trips | median /100 FGA (p10–p90) | YoY r (pooled) "
      f"| split-half ({SEASONS[-1]}) |")
    o("|---|---|--:|--:|--:|--:|")
    for row in rows:
        cls = row["cls"]
        values = [r[f"{cls}Per100Fga"] for r in qualified]
        qs = quantiles(values, (0.1, 0.5, 0.9))
        o(f"| {row['label']} | {row['tier']} | {league_trips[cls]:,} "
          f"| {qs[1]:.1f} ({qs[0]:.1f}–{qs[2]:.1f}) "
          f"| {row['overall']:.2f} | {row['reliability']:.2f} |")
    other = sum(league_trips[c] for c in ("flagrant", "awayFromPlay",
                                          "transitionTake", "clearPath"))
    other_corr = corr(panel, "otherAddonPer100Fga")
    o(f"| Other add-on (flagrant, away-from-play, transition, clear path) "
      f"| add-on | {other:,} | — | {other_corr:.2f} | — |")
    all_r = corr(panel, "tripsPer100Fga")
    o(f"| **All trips** | — | {sum(league_trips.values()):,} | — | {all_r:.2f} "
      f"| {reliability['tripsPer100Fga']:.2f} |")
    o("")
    coefs = [r["trueCoef"] for r in qualified]
    qs = quantiles(coefs, (0.1, 0.5, 0.9))
    o(f"The true attempt-equivalent coefficient — the exact replacement "
      f"for the conventional 0.44 — has median {qs[1]:.3f} across "
      f"qualified players (p10–p90 {qs[0]:.3f}–{qs[2]:.3f}, full span "
      f"{min(coefs):.3f}–{max(coefs):.3f}) and persists year over year "
      f"at r = {corr(panel, 'trueCoef'):.2f}.")
    table = "\n".join(out)
    table_path = ANALYSIS / "output" / "exhibit2-taxonomy.md"
    table_path.write_text(table, encoding="utf-8")
    print(table)
    print(f"\nexhibit 2 -> {table_path}")


if __name__ == "__main__":
    main()
