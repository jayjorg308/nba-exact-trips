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
import sys
import textwrap
from collections import defaultdict
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib import (  # noqa: E402
    ANALYSIS, RESEARCH, bootstrap_gap, bootstrap_r, build_panel,
    classify_transition, corr, player_seasons, quantiles,
    split_half_reliability,
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
            "stayersCi": bootstrap_r(stayers, key),
            "movers": corr(movers, key),
            "moversCi": bootstrap_r(movers, key),
            "gapCi": bootstrap_gap(stayers, movers, key)[:2],
            "reliability": reliability.get(key),
        })
    rows.sort(key=lambda r: -r["overall"])

    # ---- Exhibit 1: the figure -------------------------------------------
    # Type is sized for the image's reduction to a 6.5-inch text column.
    fig, ax = plt.subplots(figsize=(8.2, 5.0), dpi=200)
    fig.patch.set_facecolor(SURFACE)
    ax.set_facecolor(SURFACE)

    ys = list(range(len(rows)))[::-1]
    whisker_offset = 0.14
    for y, row in zip(ys, rows):
        ax.plot([row["movers"], row["stayers"]], [y, y],
                color=BASELINE, linewidth=2.5, zorder=1, solid_capstyle="round")
        ax.plot(row["stayersCi"], [y + whisker_offset] * 2, color=STAYERS,
                linewidth=1.8, alpha=0.55, zorder=2)
        ax.plot(row["moversCi"], [y - whisker_offset] * 2, color=MOVERS,
                linewidth=1.8, alpha=0.55, zorder=2)
        ax.plot([row["reliability"]], [y], marker="|", markersize=20,
                markeredgewidth=2.5, color=MUTED, zorder=2)
        ax.plot([row["stayers"]], [y], "o", markersize=11, color=STAYERS,
                markeredgecolor=SURFACE, markeredgewidth=2, zorder=3)
        ax.plot([row["movers"]], [y], "o", markersize=11, color=MOVERS,
                markeredgecolor=SURFACE, markeredgewidth=2, zorder=3)
        lo, hi = row["gapCi"]
        emphasis = row["cls"] == "bonus"
        ax.text((row["stayers"] + row["movers"]) / 2, y - 0.36,
                f"gap 95% CI [{lo:+.2f}, {hi:+.2f}]".replace("0.", "."),
                ha="center", va="top", fontsize=10.5 if emphasis else 9.5,
                color=INK_SECONDARY if emphasis else MUTED)
        # Row label above-left of its row: the whiskers never reach there.
        ax.text(0.01, y + 0.20, row["label"], ha="left", va="bottom",
                fontsize=12, color=INK)

    ax.legend(
        handles=[
            plt.Line2D([], [], marker="o", linestyle="", markersize=9,
                       color=STAYERS, label="stayed with one team"),
            plt.Line2D([], [], marker="o", linestyle="", markersize=9,
                       color=MOVERS, label="changed teams"),
        ],
        loc="lower left", frameon=False, fontsize=10.5, handletextpad=0.3,
        borderaxespad=0.3, labelcolor=INK_SECONDARY,
    )

    ax.set_xlim(0, 1.0)
    ax.set_ylim(-1.0, len(rows) - 0.4)
    ax.set_yticks([])
    ax.set_xticks([0, 0.2, 0.4, 0.6, 0.8, 1.0])
    ax.tick_params(axis="x", colors=MUTED, labelsize=10.5)
    ax.grid(axis="x", color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)
    for spine in ("top", "right", "left"):
        ax.spines[spine].set_visible(False)
    ax.spines["bottom"].set_color(BASELINE)
    ax.set_xlabel("Year-over-year correlation of trip generation per 100 FGA "
                  f"(pooled transitions, {SEASONS[0]} … {SEASONS[-1]})",
                  fontsize=11, color=INK_SECONDARY)
    subtitle = textwrap.fill(
        "Each dot: the correlation between a player's rate in one season "
        "and the next, over player-season pairs where he stayed with one "
        f"team (blue, n = {len(stayers)} transitions) or changed teams "
        f"between seasons (orange, n = {len(movers)}; {len(mixed)} pairs "
        "with a midseason move excluded). Whiskers: player-cluster "
        "bootstrap 95% intervals; the text under each row is the interval "
        "for the blue-orange gap. Gray tick: within-season (split-half) "
        "reliability.",
        width=92)
    ax.set_title("Channels persist differentially; non-shooting bonus trips "
                 "persist least",
                 fontsize=14, color=INK, loc="left",
                 pad=14 + 13.5 * subtitle.count("\n") + 13.5)
    ax.text(0, 1.035, subtitle, transform=ax.transAxes, fontsize=9.5,
            color=INK_SECONDARY, va="bottom", linespacing=1.4)
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
