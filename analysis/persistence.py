"""The headline analysis: which trip channels persist as skills?

Three seasons, two adjacent transitions: per-transition and pooled
year-over-year correlations of per-channel generation rates, the two-year
lag (decay), split-half (odd/even game) reliability of the RATES within
each season, and the context test — players who stayed with one team vs
players who changed teams, grouped by game-level team history (a
midseason change in either season is 'mixed' and reported separately),
with each transition shown on its own and player-cluster bootstrap
intervals beside the Fisher z tests.

  python analysis/persistence.py
"""

from __future__ import annotations

import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib import (  # noqa: E402
    ANALYSIS, bootstrap_gap, bootstrap_r, build_panel, classify_transition,
    corr, fisher_p, player_seasons, spearman, split_half_reliability,
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


def fmt_p(p: float) -> str:
    return f"{p:.3f}"


def main() -> None:
    by_season = {s: player_seasons(s) for s in SEASONS}
    transitions = [
        (SEASONS[0], SEASONS[1],
         build_panel(by_season[SEASONS[0]], by_season[SEASONS[1]], PANEL_MIN_FGA)),
        (SEASONS[1], SEASONS[2],
         build_panel(by_season[SEASONS[1]], by_season[SEASONS[2]], PANEL_MIN_FGA)),
    ]
    lag_panel = build_panel(by_season[SEASONS[0]], by_season[SEASONS[2]], PANEL_MIN_FGA)
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
    o("Split-half: odd/even-game rates per 100 FGA within a season, "
      "Spearman-Brown corrected — the within-season ceiling.")
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

    o("## The context test — by game-level team history")
    o("")
    groups: dict[str, list[tuple[dict, dict]]] = defaultdict(list)
    per_transition: list[tuple[str, dict[str, list]]] = []
    for earlier, later, panel in transitions:
        local: dict[str, list[tuple[dict, dict]]] = defaultdict(list)
        for a, b in panel:
            group = classify_transition(a, b)
            groups[group].append((a, b))
            local[group].append((a, b))
        per_transition.append((f"{earlier}→{later}", local))
    stayers, movers, mixed = groups["stayer"], groups["mover"], groups["mixed"]
    o("Stayer: one team in both seasons, the same one. Mover: one team each "
      "season, different. Mixed: a midseason change in either season "
      "(excluded from the main comparison; folded into movers below).")
    o("")
    o(f"Stayer transitions: {len(stayers)} · mover transitions: {len(movers)} "
      f"· mixed transitions: {len(mixed)}")
    o("")
    o("### Pooled, stayers vs movers (mixed excluded)")
    o("")
    o("Bootstrap: player-cluster resampling (2,000 reps) of the gap, so a "
      "player's two transitions and their shared middle season travel together.")
    o("")
    o("| channel | stayers r [95% CI] | movers r [95% CI] | gap [95% CI] "
      "| P(gap ≤ 0) | Fisher p (independent samples, reference only) |")
    o("|---|--:|--:|--:|--:|--:|")
    for key, label in CHANNEL_KEYS:
        rs, rm = corr(stayers, key), corr(movers, key)
        s_lo, s_hi = bootstrap_r(stayers, key)
        m_lo, m_hi = bootstrap_r(movers, key)
        _, p = fisher_p(rs, len(stayers), rm, len(movers))
        lo, hi, p_le0 = bootstrap_gap(stayers, movers, key)
        o(f"| {label} | {rs:.3f} [{s_lo:.3f}, {s_hi:.3f}] "
          f"| {rm:.3f} [{m_lo:.3f}, {m_hi:.3f}] "
          f"| {rs - rm:+.3f} [{lo:+.3f}, {hi:+.3f}] | {p_le0:.3f} | {fmt_p(p)} |")
    o("")
    o("### Per transition (mixed excluded)")
    o("")
    o("| transition | channel | stayers r (n) | movers r (n) | gap | Fisher p |")
    o("|---|---|--:|--:|--:|--:|")
    for name, local in per_transition:
        s_panel, m_panel = local["stayer"], local["mover"]
        for key, label in CHANNEL_KEYS:
            rs, rm = corr(s_panel, key), corr(m_panel, key)
            _, p = fisher_p(rs, len(s_panel), rm, len(m_panel))
            o(f"| {name} | {label} | {rs:.3f} ({len(s_panel)}) | {rm:.3f} ({len(m_panel)}) "
              f"| {rs - rm:+.3f} | {fmt_p(p)} |")
    o("")
    o("### Sensitivity: mixed transitions folded into movers")
    o("")
    movers_plus = movers + mixed
    o("| channel | stayers r | movers+mixed r | gap | Fisher p |")
    o("|---|--:|--:|--:|--:|")
    for key, label in CHANNEL_KEYS:
        rs, rm = corr(stayers, key), corr(movers_plus, key)
        _, p = fisher_p(rs, len(stayers), rm, len(movers_plus))
        o(f"| {label} | {rs:.3f} | {rm:.3f} | {rs - rm:+.3f} | {fmt_p(p)} |")
    o("")
    o("### Mean change in rate, season to season (per 100 FGA)")
    o("")
    o("| channel | stayers mean Δ | movers mean Δ | movers − stayers |")
    o("|---|--:|--:|--:|")
    for key, label in CHANNEL_KEYS:
        ds = sum(b[key] - a[key] for a, b in stayers) / len(stayers)
        dm = sum(b[key] - a[key] for a, b in movers) / len(movers)
        o(f"| {label} | {ds:+.3f} | {dm:+.3f} | {dm - ds:+.3f} |")
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
