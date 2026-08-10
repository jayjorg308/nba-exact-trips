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
from collections import defaultdict
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib import ANALYSIS, RESEARCH, pearson, player_seasons, quantiles  # noqa: E402
from persistence import split_half_reliability  # noqa: E402

SEASONS = ("2024-25", "2025-26")
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
    ("bonus", "Bonus (off-ball)", "attempt-equivalent"),
]


def build_panel(prior: dict, current: dict) -> list[tuple[dict, dict]]:
    return [
        (prior[p], current[p])
        for p in sorted(set(prior) & set(current))
        if prior[p]["fga"] >= PANEL_MIN_FGA and current[p]["fga"] >= PANEL_MIN_FGA
        and prior[p].get("trips", 0) > 0 and current[p].get("trips", 0) > 0
    ]


def corr(panel: list[tuple[dict, dict]], key: str) -> float:
    xs = [a[key] for (a, b) in panel if key in a and key in b]
    ys = [b[key] for (a, b) in panel if key in a and key in b]
    return pearson(xs, ys)


def main() -> None:
    prior = player_seasons(SEASONS[0])
    current = player_seasons(SEASONS[1])
    panel = build_panel(prior, current)
    stayers = [(a, b) for (a, b) in panel
               if a["team"] == b["team"] and a["team"] != "TOT" and b["team"] != "TOT"]
    movers = [(a, b) for (a, b) in panel if (a, b) not in stayers]
    reliability = split_half_reliability(SEASONS[1], PANEL_MIN_FGA)

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
    fig, ax = plt.subplots(figsize=(8.2, 3.4), dpi=200)
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

    top_y = ys[0]
    top = rows[0]
    ax.text(top["stayers"] + 0.012, top_y + 0.38, "stayed on team",
            ha="left", fontsize=9, color=INK_SECONDARY)
    ax.plot([top["stayers"]], [top_y + 0.38], "o", markersize=5, color=STAYERS,
            clip_on=False)
    ax.text(top["movers"] - 0.012, top_y + 0.38, "changed teams",
            ha="right", fontsize=9, color=INK_SECONDARY)
    ax.plot([top["movers"] - 0.002], [top_y + 0.38], "o", markersize=5,
            color=MOVERS, clip_on=False)
    rel_y = ys[1]
    ax.annotate("within-season reliability", (rows[1]["reliability"], rel_y),
                xytext=(rows[1]["reliability"] + 0.015, rel_y - 0.45),
                ha="left", fontsize=9, color=MUTED)
    bonus_row = next((y, r) for y, r in zip(ys, rows) if r["cls"] == "bonus")
    ax.annotate("context gap p = .042",
                ((bonus_row[1]["stayers"] + bonus_row[1]["movers"]) / 2,
                 bonus_row[0]),
                xytext=((bonus_row[1]["stayers"] + bonus_row[1]["movers"]) / 2,
                        bonus_row[0] - 0.55),
                ha="center", fontsize=9, color=INK_SECONDARY)

    ax.set_xlim(0, 1.0)
    ax.set_ylim(-0.9, len(rows) - 0.2)
    ax.set_yticks([])
    ax.set_xticks([0, 0.2, 0.4, 0.6, 0.8, 1.0])
    ax.tick_params(axis="x", colors=MUTED, labelsize=9)
    ax.grid(axis="x", color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)
    for spine in ("top", "right", "left"):
        ax.spines[spine].set_visible(False)
    ax.spines["bottom"].set_color(BASELINE)
    ax.set_xlabel("Year-over-year correlation of trip generation per 100 FGA "
                  f"({SEASONS[0]} → {SEASONS[1]})",
                  fontsize=9.5, color=INK_SECONDARY)
    ax.set_title("Foul-drawing channels persist differentially, and the "
                 "off-ball channel partly belongs to the team",
                 fontsize=11.5, color=INK, loc="left", pad=12)
    fig.tight_layout()
    fig_path = ANALYSIS / "output" / "exhibit1-persistence.png"
    fig.savefig(fig_path, facecolor=SURFACE, bbox_inches="tight")
    print(f"exhibit 1 -> {fig_path}")

    # ---- Exhibit 2: the table --------------------------------------------
    league_trips: dict[str, int] = defaultdict(int)
    with (RESEARCH / "data" / "derived" / SEASONS[1] / "trips.csv").open(
        encoding="utf-8"
    ) as handle:
        for row in csv.DictReader(handle):
            league_trips[row["trip_class"]] += 1
    qualified = [r for r in current.values()
                 if r["fga"] >= PANEL_MIN_FGA and r.get("trips", 0) > 0]

    out = []
    o = out.append
    o("# Exhibit 2 — the trip taxonomy, measured (2025-26; stability vs 2024-25)")
    o("")
    o("| channel | tier | league trips | median /100 FGA (p10–p90) | YoY r | split-half |")
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
    o(f"True attempt coefficient across qualified players: median {qs[1]:.3f} "
      f"(p10–p90 {qs[0]:.3f}–{qs[2]:.3f}, full span "
      f"{min(coefs):.3f}–{max(coefs):.3f} vs the conventional 0.44); "
      f"year-over-year r = {corr(panel, 'trueCoef'):.2f}.")
    table = "\n".join(out)
    table_path = ANALYSIS / "output" / "exhibit2-taxonomy.md"
    table_path.write_text(table, encoding="utf-8")
    print(table)
    print(f"\nexhibit 2 -> {table_path}")


if __name__ == "__main__":
    main()
