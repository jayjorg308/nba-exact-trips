# nba-exact-trips

Research repo for an SSAC27 (MIT Sloan Sports Analytics Conference)
research-paper submission: exact NBA free-throw trip reconstruction,
league-wide, and what it reveals about foul-drawing as a skill. The README
carries the current status and results; this file carries the working
rules an agent needs before touching anything.

## Deadlines

- **Abstract due Oct 1, 2026, 11:59 p.m. EST** — under 500 words including
  title, max two tables/figures combined, four sections
  (Introduction/Methods/Results/Conclusion), and Results must state ACTUAL
  results. Blind review: the abstract must stand without leaning on the
  author's other work by name.
- Full manuscript Dec 4, 2026, if invited.
- The competition requires the repo to be open (it is: MIT + committed
  derived datasets).

## The standing rules

- **No estimator, ever.** The 0.44 trip coefficient (and any successor) is
  what this project measures and replaces; it must never appear in the
  pipeline as a computational input. Hero-side/player-side quantities are
  exact or absent.
- **Exactness discipline.** Oracles (per-player per-game box-score
  free-throw lines; per-player season totals vs the league artifact) are
  hard requirements in strict mode. Never weaken an oracle, never tolerate
  an approximate reconciliation, never drop a discrepant row. A dataset
  that fails an oracle is not written.
- **The survey → strict workflow** is how grammar drift is handled: run
  `derive_league_trips.py --mode survey`, inspect every anomaly's actual
  event window with `ingestion/inspect_anomalies.py`, extend the grammar
  ONLY from inspected evidence (never guess a classification), re-survey
  to zero anomalies, then run `--mode strict`. Every extension gets a
  rationale line in `trip_grammar.py`'s GRAMMAR_VERSION docstring; bump
  the version for semantic changes.
- **PlayByPlayV3 stores amended events out of chronological list order.**
  Never rely on list position for event relationships — use the whole-game
  (period, clock) indexes in `trip_grammar._GameIndex`. This bug class
  cost the original backward-scan design its correctness at league scale.
- **Raw layer is append-only** (`data/raw/`, gitignored): never overwrite
  a snapshot; a re-pull adds a dated file. Pulls are LOCAL ONLY
  (stats.nba.com blocks cloud IPs) and are the human's to run — write
  resumable scripts, don't babysit long pulls in a session.
- **Storage is files.** Verbatim raw JSON → committed CSV datasets.
  DuckDB is sanctioned as an in-script analysis query engine over those
  files; a database is never a storage tier, because the open-data
  deliverable is files a reviewer downloads.
- **Technical free throws are never trips**: counted, oracle-included,
  excluded from trip analysis.
- **Trip classes partition non-technical free throws** into two tiers:
  attempt-equivalent (shootingFoul2/3, bonus — the possession ends at the
  line) and add-on (andOne, flagrant, awayFromPlay, transitionTake,
  clearPath). The tier is what a scoring-attempt denominator adds to FGA.

## Commands

```bash
pip install -r requirements.txt
python ingestion/pull_league_games.py --season <YYYY-YY>   # user-run, resumable
python ingestion/pull_league_totals.py --season <YYYY-YY>  # user-run, one call
python ingestion/derive_league_trips.py --season <YYYY-YY> --mode survey|strict
python ingestion/inspect_anomalies.py --season <YYYY-YY>   # triage evidence
python analysis/economy.py --season <YYYY-YY>
python analysis/persistence.py
python analysis/robustness.py
python analysis/exhibits.py
```

Analysis scripts read the committed dataset plus the league totals
artifact (`data/raw/_league/<season>/totals/`) for denominators (FGA, MIN,
PTS); shared loaders and stats helpers live in `analysis/lib.py`.

## Relationship to nba-analytics

The trip grammar originated in the author's nba-analytics product repo
(sibling checkout; per-hero grain, its own ADR discipline). It was PORTED
here (`ingestion/corpus.py`, `ingestion/trip_grammar.py`) and generalized;
the repos are deliberately independent — never import across them. The one
remaining cross-repo file, `ingestion/pilot_derive_trips.py`, is the
historical 11-player pilot and reaches into nba-analytics by path; it is
kept as history, not a pattern to extend. nba-analytics' storage layout
for game pairs is identical, which is why its corpus could be copied in.

## Key numbers (2026-08-10, dataset v0)

Two seasons (2024-25, 2025-26), 2,460 games, 59,566 trips, 1,151
player-seasons, all oracle-exact. Persistence gradient (per 100 FGA, YoY,
207-player panel): SF2 .856 > and-one .772 > SF3 .741 > bonus .603 >
other add-on .314; split-half reliabilities .85–.94. Context test: bonus
.664 stayers vs .438 movers (p = .042); SF2 travels (p = .20). True 0.44
coefficient: median .427, span .277–.481, persists at r = .51, ΔTS up to
1.5pp. Premium: two-shot trip beats own field PPS for 279/284 players.
