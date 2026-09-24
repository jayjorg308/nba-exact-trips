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

## Status (2026-09-23)

**The dataset covers three full regular seasons** (2023-24, 2024-25,
2025-26 — the clean same-rules era), 88,347 trips across 3,690 games,
derived in strict mode with **zero anomalies and zero oracle exceptions**:
every one of the 1,723 league player-seasons (1,647 with free-throw
activity, 1,646 with trips) reconciles exactly against both the per-game
box scores and the independent league season-totals source.

**The analysis runs from a fresh clone** — every report under
`analysis/output/` regenerates from the committed datasets alone (the
per-game `player_games.csv` supplies denominators and game-level team
histories; nothing under `analysis/` reads `data/raw`). Findings:

- **Channels persist differentially** (422 pooled player-transitions, ≥300
  FGA both seasons; two-shot highest and bonus lowest in each transition):
  two-shot shooting fouls r = 0.87 > three-shot fouls 0.76 ≈ and-ones
  0.75 > bonus 0.58 > residual add-on classes 0.31. Against rate-based
  within-season (split-half) reliability, two-shot fouls persist near
  their reliability (0.89–0.92) while bonus trips fall short of a lower
  0.65–0.78: the non-shooting bonus channel is both noisier to measure
  and less stable.
- **Movers persist less in every main channel.** Grouping by game-level
  team history (284 stayer transitions from 199 players, 54 mover
  transitions from 51 players, 84 midseason moves excluded), all-trip
  persistence is 0.74 for movers against 0.87 for stayers (player-cluster
  bootstrap 95% interval for the gap +0.02 to +0.26). The bonus gap is
  the largest (0.62 → 0.40) but its interval spans zero (−0.05 to +0.58),
  and the two transitions disagree on which channel gaps most — so
  channel-specific differences remain uncertain. (An earlier version of
  this result, built on the league artifact's team labels, claimed a
  bonus-only effect; that grouping was wrong and the claim is withdrawn.)
- **The 0.44 coefficient's error is player-shaped and persistent**: the
  true attempt-equivalent coefficient spans 0.277–0.481 across qualified
  players (median 0.427), correlates with how a player's line is built
  (technicals, three-shot fouls, and-ones), moves True Shooting by a
  median 0.15 and up to 1.5 percentage points, and persists at r = 0.53 —
  the estimator tends to mis-measure the same players every year.
- **The line premium**: a two-shot trip at the player's own conversion
  out-values his average field attempt for 279 of 284 qualified players
  (median +0.51 points per attempt).

**The abstract is red-penned, reframed on the corrected analysis, and
submission-ready**: `paper/abstract.md`
(v5, 486 words including title), citing the two exhibits rendered by
`analysis/exhibits.py` (`analysis/output/exhibit1-persistence.png`,
`analysis/output/exhibit2-taxonomy.md`). The single-file submission PDF
is assembled by `python paper/build_submission.py` →
`paper/submission.pdf`, which re-verifies the word count and blind-review
constraints on every build; submission logistics in `paper/NOTES.md`.
Remaining work: submit by the Oct 1, 2026 deadline, then
manuscript-phase extensions if invited.

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
- **`player_games.csv`** — one row per player-game from the official box
  score (team, minutes, FGM/FGA, FTM/FTA, points): the analysis layer's
  denominators, exposure, and game-level team histories, so every report
  reproduces from a fresh clone without stats.nba.com. Its sidecar
  `player_games.meta.json` records the oracle — FTA/FTM/PTS sums equal
  the league season totals for every player-season — and lists the three
  known ±1 FGA disagreements between the NBA's two endpoints.
- **`meta.json`** — provenance: games processed, grammar version, derive
  mode, oracle results.

Technical free throws are never trips (a designated shooter's points, not
an earned visit); they are counted separately and included in every oracle.

## Reproducing the analysis (offline, from the committed data)

Every report and exhibit regenerates from `data/derived/` alone — no NBA
endpoint is contacted, and `data/raw/` need not exist. Requires Python
3.12+.

```bash
pip install -r requirements.txt
python analysis/economy.py --season 2025-26     # also 2024-25, 2023-24
python analysis/persistence.py
python analysis/robustness.py
python analysis/exhibits.py
python paper/build_submission.py                # -> paper/submission.pdf
```

## Reproducing from scratch

Data collection hits stats.nba.com's unofficial endpoints, which **block
cloud IPs — pulls are local-machine only**. Pulls are append-only and
resumable: rerun until "CORPUS COMPLETE".

```bash
python ingestion/pull_league_games.py --season 2025-26   # ~1,230 game pairs
python ingestion/pull_league_totals.py --season 2025-26  # one call
python ingestion/derive_league_trips.py --season 2025-26 --mode strict
python ingestion/derive_player_games.py --season 2025-26  # per-game lines + oracle
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
- `docs/grammar-triage.md` — every survey anomaly across all three
  seasons (47 cases, six families), its evidence, and the rule it
  produced.
- `docs/prior-art/` — dissections of the closest prior work (Sanders &
  Ehrlich's SSAC 2024 true shot charts, and what it does and doesn't claim).
- `docs/probes/` — empirical probes of data availability (notably: no
  public NBA endpoint serves fouled-miss shot locations, any era).
- `analysis/output/` — the generated reports and exhibits.
- `paper/` — the abstract draft, submission notes, and the
  submission-PDF builder.

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
