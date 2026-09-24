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
- **The draft is red-penned and reframed**: `paper/abstract.md` (v5,
  486 words incl. title). The submitted artifact is `paper/submission.pdf`, built by
  `python paper/build_submission.py` from the abstract plus the committed
  exhibits (never hand-transcribed); the build hard-fails at ≥500 words
  or on any author-identifying string. Rebuild after ANY edit to the
  abstract or exhibits. Submission rules, word-count command, and
  manuscript-phase plans in `paper/NOTES.md`. Any edit touching a number
  is re-verified against `analysis/output/` before landing.
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
- **Team membership comes from `player_games.csv`, never from the league
  totals artifact.** The artifact's TEAM_ABBREVIATION is the roster at
  pull time (no TOT rows; a summer trade relabels the prior season).
  This bug produced the abstract's original, withdrawn context-test
  result.
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
python ingestion/derive_player_games.py --season <YYYY-YY>  # per-game lines + oracle
python ingestion/inspect_anomalies.py --season <YYYY-YY>   # triage evidence
python analysis/economy.py --season <YYYY-YY>
python analysis/persistence.py
python analysis/robustness.py
python analysis/exhibits.py
python paper/build_submission.py   # -> paper/submission.pdf
```

Analysis scripts read ONLY committed data: the trip layer plus
`player_games.csv` (per-game box-score lines — denominators, exposure,
and game-level team histories); nothing under `analysis/` touches
`data/raw`, so a fresh clone reproduces every report. The league totals
artifact is the derives' oracle, not an analysis input. Shared loaders
and stats helpers (panels, stayer/mover/mixed grouping by team history,
rate-based split-half reliability, Fisher z, player-cluster bootstrap)
live in `analysis/lib.py`.

## Relationship to nba-analytics

The trip grammar originated in the author's nba-analytics product repo
(sibling checkout; per-hero grain, its own ADR discipline). It was PORTED
here (`ingestion/corpus.py`, `ingestion/trip_grammar.py`) and generalized;
the repos are deliberately independent — never import across them. The one
remaining cross-repo file, `ingestion/pilot_derive_trips.py`, is the
historical 11-player pilot and reaches into nba-analytics by path; it is
kept as history, not a pattern to extend. nba-analytics' storage layout
for game pairs is identical, which is why its corpus could be copied in.

## Key numbers (2026-09-23, three-season dataset, corrected analysis)

Three seasons (2023-24 through 2025-26 — the same-rules era; earlier
seasons cross rule-regime boundaries and are deliberately excluded),
3,690 games, 88,347 trips; all 1,723 league player-seasons oracle-exact
(1,647 with free-throw activity, 1,646 with trips — one is
technical-only). Uncertainty is reported as player-cluster bootstrap
intervals; Fisher p-values are reference-only. Persistence gradient (per 100 FGA, pooled
over both transitions, 422 player-transitions; SF2 highest and bonus
lowest in each, SF3/and-one swap between them): SF2 .868 > SF3 .755 ≈
and-one .750 > bonus .580 > other add-on .309. Rate-based split-half
reliability (3-season range): SF2 .89–.92, SF3 .74–.83, and-one .79,
bonus .65–.78 — bonus is both noisier to measure and less persistent.
Context test by game-level team history (284 clean stayers / 54 clean
movers / 84 mixed excluded): persistence drops for movers in EVERY
channel — all trips .870 vs .743 (p = .014), SF2 +.108 (p = .025), SF3
+.151, bonus .623 vs .401 (+.221, Fisher p = .046, player-cluster
bootstrap 95% CI [−.05, +.58]), and-one +.056 — so channel-specificity
is suggestive, not established, and the two transitions disagree on
which channel gaps most. Two-year-lag retention 90–99% by channel. True
0.44 coefficient: median .427, span .277–.481, persists at r = .53, ΔTS
median +0.15pp, max 1.5pp. Premium: two-shot trip beats own field PPS
for 279/284 qualified players (2025-26; cut from the abstract for words,
manuscript material). The pre-correction context-test numbers (.635 vs
.420, p = .006, "every other channel ≤ .04") came from the artifact's
team labels and are WRONG — never cite them.
