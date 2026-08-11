# nba-exact-trips

Exact NBA free-throw trip reconstruction from play-by-play, league-wide —
the dataset and analysis behind a research submission to the MIT Sloan
Sports Analytics Conference (SSAC27) research papers competition.

A **trip** is the set of free throws awarded from a single non-technical
foul, shot as one visit to the line. This project reconstructs every trip
exactly from official play-by-play, classifies how each arose (its
**channel**: shooting foul, bonus, and-one, and the rarer classes), and
verifies the reconstruction against independent oracles: every player-game
reconciles with the official box-score free-throw line, and every
player-season reconciles with official season totals. No estimators, no
tolerances, no dropped discrepancies.

## Status (2026-08-11)

**The dataset covers three full regular seasons** (2023-24, 2024-25,
2025-26 — the clean same-rules era), 88,347 trips across 3,690 games,
derived in strict mode with **zero anomalies and zero oracle exceptions**:
all 1,723 player-seasons with free-throw activity reconcile exactly
against both the per-game box scores and the independent league
season-totals source.

**The analysis core is complete, and the headline replicates across two
independent season transitions.** All findings reproducible from the
committed dataset (reports in `analysis/output/`):

- **Channels persist differentially** (422 pooled player-transitions, ≥300
  FGA both seasons; ordering identical in each transition): two-shot
  shooting fouls r = 0.87 > three-shot fouls 0.76 ≈ and-ones 0.75 >
  bonus 0.58 > residual add-on classes 0.31, with within-season
  (split-half) reliabilities of 0.85–0.95 showing the bonus gap is not
  measurement noise.
- **The context test**: bonus-trip persistence collapses for players who
  changed teams (0.635 stayers vs 0.420 movers over 306/116 pooled
  transitions, Fisher z = 2.75, p = .006) while every other channel
  travels intact (gaps ≤ 0.04, all p > .2) — off-ball foul-drawing partly
  belongs to the team; shooting-foul drawing is the player's.
- **The 0.44 coefficient's error is player-shaped and persistent**: the
  true attempt-equivalent coefficient spans 0.277–0.481 across qualified
  players (median 0.427), correlates with how a player's line is built
  (technicals, three-shot fouls, and-ones), moves True Shooting by up to
  1.5 percentage points, and persists at r = 0.53 — the estimator
  mis-measures the same players every year.
- **The line premium**: a two-shot trip at the player's own conversion
  out-values his average field attempt for 279 of 284 qualified players
  (median +0.51 points per attempt).

The two draft abstract exhibits are `analysis/output/exhibit1-persistence.png`
and `analysis/output/exhibit2-taxonomy.md`, rendered by `analysis/exhibits.py`.
Remaining work: the abstract itself (due Oct 1, 2026), then manuscript-phase
extensions if invited.

## The dataset

Committed under `data/derived/<season>/`:

- **`trips.csv`** — one row per trip: `game_id`, `player_id`,
  `player_name`, `team_id`, `team_tricode`, `period`, `clock` (ISO
  duration, time remaining), `trip_class` (one of `shootingFoul2`,
  `shootingFoul3`, `bonus`, `andOne`, `flagrant`, `awayFromPlay`,
  `transitionTake`, `clearPath`), `tier` (`attemptEquivalent` — the trip
  ends the possession in place of a field-goal attempt — or `addOn`),
  `ftm`, `fta`, `and_one_shot_id` (the made basket's actionNumber in the
  same game's PlayByPlayV3 feed, when the shooter's own basket is
  identified; empty otherwise).
- **`players.csv`** — per player-season: trip totals, per-class counts,
  technical free-throw lines.
- **`meta.json`** — provenance: games processed, grammar version, derive
  mode, oracle results.

Technical free throws are never trips (a designated shooter's points, not
an earned visit); they are counted separately and included in every oracle.

## Reproducing from scratch

Requires Python 3.12+ and `pip install -r requirements.txt`. Data
collection hits stats.nba.com's unofficial endpoints, which **block cloud
IPs — pulls are local-machine only**. Pulls are append-only and resumable:
rerun until "CORPUS COMPLETE".

```bash
python ingestion/pull_league_games.py --season 2025-26   # ~1,230 game pairs
python ingestion/pull_league_totals.py --season 2025-26  # one call
python ingestion/derive_league_trips.py --season 2025-26 --mode strict
python analysis/economy.py --season 2025-26
python analysis/persistence.py
python analysis/robustness.py
python analysis/exhibits.py
```

The derive has two modes. `--mode survey` processes everything and collects
grammar gaps and oracle mismatches into `anomalies.csv` (the triage list);
`--mode strict` hard-fails on the first violation and is the only mode a
publishable dataset comes from. The workflow when new data surfaces drift:
survey → inspect each anomaly's event window (`ingestion/inspect_anomalies.py`)
→ extend the versioned grammar from evidence → re-survey to zero → strict.
The grammar's version history and every extension's rationale live in
`ingestion/trip_grammar.py`'s docstring.

## Research context

- `docs/build-plan.md` — the build plan and its status.
- `docs/prior-art/` — dissections of the closest prior work (Sanders &
  Ehrlich's SSAC 2024 true shot charts, and what it does and doesn't claim).
- `docs/probes/` — empirical probes of data availability (notably: no
  public NBA endpoint serves fouled-miss shot locations, any era).
- `analysis/output/` — the generated reports and exhibits.

The trip grammar originated in the author's
[nba-analytics](https://github.com/jayjorg308/nba-analytics) product repo
(per-hero, 146-game corpus, four-oracle discipline) and was ported and
generalized here; the two repos are deliberately independent.

## Data notice

Datasets in this repository are derived from publicly available NBA Stats
(stats.nba.com) data. The underlying game data remains the property of the
NBA. The code is MIT-licensed; the derived datasets are provided for
research reproducibility.

Raw verbatim API responses are not committed (size and redistribution
restraint); the pull scripts reproduce them, and the derived,
oracle-verified trip datasets are committed in full.
