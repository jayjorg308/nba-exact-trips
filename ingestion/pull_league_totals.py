"""Pull a season's league player-totals artifact (the season-total oracle
and league baseline; same shape as nba-analytics' artifact so either repo's
copy is interchangeable).

LOCAL ONLY. One call per season:

  python ingestion/pull_league_totals.py --season 2024-25
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date
from pathlib import Path

try:
    from nba_api.stats.endpoints import leaguedashplayerstats
except ImportError:
    sys.exit("nba_api not installed. Run: pip install nba_api")


def main() -> None:
    ap = argparse.ArgumentParser(description="Pull the league season-totals artifact.")
    ap.add_argument("--season", required=True)
    ap.add_argument("--raw-root", default="data/raw")
    ap.add_argument("--timeout", type=int, default=60)
    args = ap.parse_args()

    out_dir = Path(args.raw_root) / "_league" / args.season / "totals"
    pull_date = date.today().isoformat()
    out_path = out_dir / f"{pull_date}.json"
    if out_path.exists():
        sys.exit(f"refusing to overwrite append-only artifact: {out_path}")

    response = leaguedashplayerstats.LeagueDashPlayerStats(
        season=args.season,
        season_type_all_star="Regular Season",
        per_mode_detailed="Totals",
        timeout=args.timeout,
    ).get_dict()

    rows = response["resultSets"][0]["rowSet"]
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path.write_text(
        json.dumps(
            {
                "_meta": {
                    "source": "stats.nba.com leaguedashplayerstats (unofficial)",
                    "season": args.season,
                    "season_type": "Regular Season",
                    "per_mode": "Totals",
                    "pull_date": pull_date,
                },
                "response": response,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"league totals ({len(rows)} player rows) -> {out_path}")


if __name__ == "__main__":
    main()
