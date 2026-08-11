# Two-season league-wide build plan

Scoped 2026-08-10, after the 11-player pilot and the Sanders & Ehrlich
dissection. Target: SSAC27 abstract (due Oct 1, 2026) with actual results;
manuscript depth follows if invited (due Dec 4).

**STATUS (end of 2026-08-10): weeks 1–5 of the timeline below completed in
one day.** Both corpora pulled complete (user-run, 1,230 games each, zero
failures); grammar v3 closed all 45 survey anomalies from inspected
evidence; strict derives green on both seasons (59,566 trips, every
player-season exact against box scores and league totals — dataset v0,
committed); the analysis core, robustness passes, and both draft exhibits
are committed under `analysis/`. Remaining: the abstract draft (weeks 6–7,
now with ~5 weeks of extra buffer), and manuscript-phase extensions if
invited (per-game player lines from box scores — the midseason-trade
event-study design; a DuckDB analysis layer if joins outgrow the CSV
loaders).

**Amendment (2026-08-11): the 2023-24 third season is pulled FORWARD into
the abstract window** as insurance on the context test, whose p = .042
rests on 54 movers — a second transition replicates (or kills) the paper's
boldest claim before it is submitted, and adds the two-year-lag decay
curve per channel. 2023-24 is the deliberate stopping point: the
transition-take rule (2022-23) and the one-free-throw flopping technical
(2023-24) bound the clean same-rules era; earlier seasons would model rule
changes, not players. Discovery (1,230 games, IST final correctly
excluded) and the league totals artifact (572 players) are already on
disk; the corpus pull is the user's resumable run, then: survey → triage
any new drift → strict → rerun the analysis suite with the pooled
two-transition context test and the decay curve.

## The paper

**The free-throw trip economy**: every NBA free-throw trip for two seasons,
exactly reconstructed and causally classified, answering (1) how players get
to the line, channel by channel, (2) what each channel is worth against the
player's own field value, and (3) which channels persist as skills
year-over-year. Supporting result: the player-shaped error of the 0.44
attempt estimator (honest framing: structurally systematic, small in TS
points). Prior-art positioning per docs/prior-art/.

## Seasons

2024-25 and 2025-26 (regular season only) — the two most recent completed
seasons, maximizing roster overlap for the persistence panel (~350 players
with meaningful minutes in both). A third season (2023-24) is a
manuscript-phase upgrade, deliberately out of abstract scope.

## Storage and querying

Files are the storage of record, per the nba-analytics precedent: verbatim
raw JSON (gitignored, reproducible via the pull scripts) and committed CSV
datasets (the open-data deliverable reviewers download as files). DuckDB is
sanctioned as the analysis-side query engine over those files (embedded, no
server, a tool inside analysis scripts) — never a storage tier.

## Self-containment (done 2026-08-10)

The repo runs alone: the trip grammar is ported (ingestion/trip_grammar.py,
grammar v2 = hero grammar + pilot extensions + multi-player), corpus access
is ported (ingestion/corpus.py, identical storage layout), and the 358
existing 2025-26 game pairs plus league artifacts are copied from
nba-analytics into data/raw. The pilot's cross-repo path hack remains only
in the pilot script, as history.

## Execution split

Long-running pulls are USER-RUN in a local terminal (resumable, append-only,
rerun-until-complete); sessions write the scripts and consume the completion
reports. Derives and analysis run in-session (minutes, and their output
needs interpretation).

## Data acquisition

- Discovery: league game IDs per season (leaguegamefinder or season
  schedule), regular season only, ~1,230 games each.
- Pulls: PlayByPlayV3 + BoxScoreTraditionalV3 per game, verbatim,
  append-only, skip-if-exists (resumable). Local only.
- Reuse: the nba-analytics corpus already holds 358 pairs (2025-26). The
  research pull reads that root first and pulls only what is missing into
  this repo's own data/raw (gitignored).
- League totals artifacts per season (Gate-5 analog oracle + baselines);
  2025-26 exists in nba-analytics, 2024-25 is one pull.
- Estimated volume: ~2,100 new game pairs ≈ 4,200 calls ≈ 8-10 hours at
  polite spacing, run in background/overnight sessions.

## Derive generalization (the real build)

Adapt the pilot derive from per-hero to all-players-per-game:

1. One pass per game: group FT events by (player, period, clock, kind),
   reconstruct every player's trips, not just a hero's.
2. And-one linkage: same-clock own made shot within the same play-by-play
   feed (no per-player shot payloads at league scale); the 11 pilot players'
   shot-payload cross-checks remain as spot oracles.
3. **Survey mode first**: collect every unclassifiable trip and unknown
   subtype across the whole corpus into a triage report instead of failing
   on the first. Extend the versioned grammar case by case (the pilot found
   two extensions in its first two players; league scale will find more).
   The final dataset derive then runs in hard-fail totality mode.
4. Oracle battery, league-wide: per-player per-game box-score FT equality;
   per-player season totals exact against the league artifact (the
   completeness proof, now for ~570 players per season); technicals
   reconciled; trip-sequence integrity.

## The open dataset (the reproducibility deliverable)

Per season: a documented trip table (player, team, game, period, clock,
class, tier, ftm, fta, and-one shot reference) plus a player-season summary
table, committed as CSV with a JSON metadata/provenance sidecar. ~30k trips
per season, a few MB. Schema documented in the README. Raw verbatim
snapshots stay gitignored (pull scripts reproduce them).

## Analysis

1. Economy decomposition: channel mix distributions league-wide, archetype
   structure (the pilot's 35-80% SF2 spread at full scale).
2. Channel values: points per trip by class vs own field PPS (the premium),
   league conversion pricing.
3. **Persistence (the headline)**: year-over-year correlation of per-channel
   generation rates (normalized per FGA or per minute) across the two-season
   player panel; split-half (odd/even games) within-season reliability as a
   robustness check; contrast channel persistence against overall FT-rate
   persistence (the known-stable benchmark).
4. The 0.44 table: true-coefficient distribution, TS deltas, who the
   estimator flatters and punishes — one honest supporting exhibit.

## Timeline (abstract due Oct 1)

- Week 1 (Aug 11-17): pull infra; 2025-26 completion pull running nightly;
  derive generalization + survey mode over the existing 358 games.
  _Started 2026-08-10, ahead of schedule: port + copy done, pull scripts
  delivered, first survey run complete — 9,222 trips, 496 players, 358
  games, 12 anomalies in three case families (clock-split sequences,
  and-ones without a same-clock made-shot event, a two-shot away-from-play
  administration), season oracle 77 exact / 505 short / 0 over on the
  partial corpus._
- Week 2 (Aug 18-24): 2025-26 full derive oracle-exact; grammar triage;
  2024-25 pull running.
- Week 3 (Aug 25-31): 2024-25 derive oracle-exact; dataset v0 published.
- Weeks 4-5 (Sep 1-14): analysis + figures (the two abstract exhibits:
  likely channel-persistence and the economy decomposition).
- Week 6 (Sep 15-21): abstract draft, red-pen, word-count discipline
  (<500 including title).
- Week 7 (Sep 22-Oct 1): buffer and submission.

Schedule risks: endpoint throttling (mitigation: start pulls immediately,
nightly resumable sessions) and the grammar-drift tail (mitigation: survey
mode makes every case visible at once instead of serially).
