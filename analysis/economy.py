"""The league-wide trip economy report for one season: channel mix and rate
distributions, the 0.44 coefficient's error structure, and the line premium.

  python analysis/economy.py --season 2025-26
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib import ANALYSIS, pearson, player_seasons, quantiles  # noqa: E402

QUALIFY_FGA = 300


def fmt(x: float, digits: int = 2) -> str:
    return f"{x:.{digits}f}"


def dist_row(label: str, values: list[float], digits: int = 2) -> str:
    qs = quantiles(values)
    return (f"| {label} | {fmt(min(values), digits)} | "
            + " | ".join(fmt(q, digits) for q in qs)
            + f" | {fmt(max(values), digits)} |")


def top_table(rows: list[dict], key: str, count: int, digits: int = 2,
              extra: str | None = None) -> list[str]:
    lines = []
    ordered = sorted(rows, key=lambda r: -r[key])[:count]
    for r in ordered:
        extra_txt = f" · {extra}={fmt(r[extra], 2)}" if extra else ""
        lines.append(f"- {r['name']} ({r['team']}): {fmt(r[key], digits)}{extra_txt}")
    return lines


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--season", required=True)
    args = ap.parse_args()

    players = player_seasons(args.season)
    qualified = [r for r in players.values()
                 if r["fga"] >= QUALIFY_FGA and r.get("trips", 0) > 0]
    out: list[str] = []
    o = out.append

    o(f"# The trip economy, {args.season} (league-wide, exact)")
    o("")
    o(f"{len(players)} players with any free-throw activity; "
      f"{len(qualified)} qualified at ≥{QUALIFY_FGA} FGA. All rates per 100 FGA "
      f"unless noted.")
    o("")

    o("## Channel generation rates — distribution across qualified players")
    o("")
    o("| rate | min | p10 | p25 | median | p75 | p90 | max |")
    o("|---|--:|--:|--:|--:|--:|--:|--:|")
    for key, label in [
        ("shootingFoul2Per100Fga", "SF2 trips"),
        ("shootingFoul3Per100Fga", "SF3 trips"),
        ("bonusPer100Fga", "bonus trips"),
        ("andOnePer100Fga", "and-one trips"),
        ("otherAddonPer100Fga", "other add-on"),
        ("tripsPer100Fga", "all trips"),
    ]:
        o(dist_row(label, [r[key] for r in qualified]))
    o("")

    o("## Channel mix — share of trips")
    o("")
    o("| share | min | p10 | p25 | median | p75 | p90 | max |")
    o("|---|--:|--:|--:|--:|--:|--:|--:|")
    for cls, label in [
        ("shootingFoul2Share", "SF2"), ("shootingFoul3Share", "SF3"),
        ("bonusShare", "bonus"), ("andOneShare", "and-one"),
    ]:
        o(dist_row(label, [r[cls] for r in qualified]))
    o("")

    o("## The 0.44 coefficient's error structure")
    o("")
    coefs = [r["trueCoef"] for r in qualified]
    deltas = [r["tsDeltaPp"] for r in qualified]
    o("| quantity | min | p10 | p25 | median | p75 | p90 | max |")
    o("|---|--:|--:|--:|--:|--:|--:|--:|")
    o(dist_row("true coefficient", coefs, 3))
    o(dist_row("ΔTS (pp)", deltas, 2))
    o("")
    o(f"Correlates of the true coefficient (Pearson): and-one share "
      f"{fmt(pearson([r['andOneShare'] for r in qualified], coefs), 2)} · "
      f"technical FTA share "
      f"{fmt(pearson([r['technicalFta'] / r['fta'] for r in qualified], coefs), 2)} · "
      f"SF3 share {fmt(pearson([r['shootingFoul3Share'] for r in qualified], coefs), 2)} · "
      f"FTA rate {fmt(pearson([r['ftaRate'] for r in qualified], coefs), 2)}")
    o("")
    o("Largest TS understatements (conventional below exact):")
    out.extend(top_table(qualified, "tsDeltaPp", 8, 2, extra="trueCoef"))
    o("")
    o("Largest TS overstatements:")
    neg = sorted(qualified, key=lambda r: r["tsDeltaPp"])[:8]
    for r in neg:
        o(f"- {r['name']} ({r['team']}): {fmt(r['tsDeltaPp'], 2)} · "
          f"trueCoef={fmt(r['trueCoef'], 2)}")
    o("")

    o("## The line premium (two-shot trip EV at own conversion vs own field PPS)")
    o("")
    premiums = [r["premium"] for r in qualified]
    o("| quantity | min | p10 | p25 | median | p75 | p90 | max |")
    o("|---|--:|--:|--:|--:|--:|--:|--:|")
    o(dist_row("premium (pts/attempt)", premiums, 3))
    below = [r for r in qualified if r["premium"] <= 0]
    o("")
    o(f"Players whose two-shot trip is worth LESS than their average field "
      f"attempt: {len(below)} of {len(qualified)}"
      + (": " + ", ".join(f"{r['name']} ({fmt(r['premium'], 2)})" for r in below)
         if below else ""))
    o("")

    o("## Channel extremes (qualified players)")
    o("")
    o("Highest SF3 generation (fouled on threes, per 100 FGA):")
    out.extend(top_table(qualified, "shootingFoul3Per100Fga", 8))
    o("")
    o("Highest bonus generation (off-ball, per 100 FGA):")
    out.extend(top_table(qualified, "bonusPer100Fga", 8))
    o("")
    o("Highest and-one generation (per 100 FGA):")
    out.extend(top_table(qualified, "andOnePer100Fga", 8))

    report = "\n".join(out)
    out_path = ANALYSIS / "output" / f"economy-{args.season}.md"
    out_path.parent.mkdir(exist_ok=True)
    out_path.write_text(report, encoding="utf-8")
    print(report)
    print(f"\nreport -> {out_path}")


if __name__ == "__main__":
    main()
