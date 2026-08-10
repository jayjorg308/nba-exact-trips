# nba-exact-trips

Exact NBA free-throw trip reconstruction from play-by-play, league-wide.

A **trip** is the set of free throws awarded from a single non-technical foul, shot as one visit to the line. This project reconstructs every trip exactly from official play-by-play, classifies how each arose (shooting foul, bonus, and-one, and the rarer classes), and verifies the reconstruction against independent oracles: every player-game reconciles with the official box-score free-throw line, and every player-season reconciles with official season totals. No estimators, no tolerances.

The research this supports:

1. **Replacing the 0.44 coefficient.** True Shooting and possession arithmetic estimate scoring attempts as `FGA + 0.44 × FTA`. Exact trips make the true count computable: attempt-equivalent trips (shooting fouls, bonus) each end a possession in place of a field-goal attempt; add-on trips (and-ones, flagrants, and the rest) do not. The estimator's error is player-shaped, and this dataset measures it.
2. **Pricing foul-drawing into shot selection.** A two-shot trip at league free-throw conversion is worth more expected points than a field-goal attempt from any zone on the floor. With exact trips on a scoring-attempt denominator, foul generation becomes a measurable component of shot selection rather than an invisible one.

## Data notice

Datasets in this repository are derived from publicly available NBA Stats (stats.nba.com) data. The underlying game data remains the property of the NBA. The code is MIT-licensed; the derived datasets are provided for research reproducibility.

Raw verbatim API responses are not committed (size and redistribution restraint); the pull scripts reproduce them, and the derived, oracle-verified trip datasets are committed in full.

## Layout

- `ingestion/` — pull and derive scripts (local-only: stats.nba.com blocks cloud IPs)
- `data/raw/` — verbatim API snapshots, gitignored, append-only
- `data/derived/` — committed, oracle-verified trip datasets
- `analysis/` — the research: estimator error, valuation, context models
- `paper/` — abstract and manuscript materials
