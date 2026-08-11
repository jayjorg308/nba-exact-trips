# Grammar triage log — every survey anomaly, its evidence, its resolution

The record behind grammar v3 and v4 (`ingestion/trip_grammar.py`): all 47
cases the survey mode surfaced across three seasons, by family, with the
game IDs so any case can be re-inspected
(`python ingestion/inspect_anomalies.py` after re-running a survey, or
directly from the raw pair). Every resolution was written from the
inspected event window, never from the anomaly line alone, and every one
was validated by the per-player box-score oracle and the season-total
oracle after adoption. Grammar v2 (the hero-corpus port plus the pilot's
two extensions) is the baseline these were surveyed against.

## Family 1 — causing foul invisible to the backward scan (7 cases, v3)

PlayByPlayV3 stores amended events out of chronological list order, so a
trip's causing foul can sit AFTER the free throws in the raw actions list
(or beyond a fixed backward window when replays, technicals, and
substitutions intervene). Resolution: causing-foul lookup became a
whole-game (period, clock) foul index; the backward scan survives only as
a fallback for clock-drifted fouls.

- 2024-25: 0022400090 (Bagley III), 0022400138 (Hawkins), 0022400249
  (G. Allen), 0022400458 (Payne), 0022400592 (Ware), 0022401084 (Garza —
  an altercation-review barrage of seven technicals between foul and
  free throws).

One sub-case: 0022400303 (G. Allen) — free throws at the fourth quarter's
opening clock whose causing penalty foul was recorded late in the third,
with no administration at its own clock. Resolution: a period-opening trip
with no same-clock foul inherits the previous period's last opponent
non-technical foul.

## Family 2 — one free throw from a shooting foul (19 cases, v3)

A shooting foul awards exactly one free throw only when the basket
counted: the and-one administration. The exact own-made-shot match fails
three ways, all observed: the fouled scorer left the game and a teammate
shot the free throw (the replacement rule); the made basket's clock
drifted sub-second from the free throw's (0022500684, Hardaway Jr.,
0.1s); or the basket was awarded without a Made Shot event (goaltending).
Resolution: declared 1 + causing foul Shooting classifies andOne, with
the shot link kept only for an own-basket match (exact clock or ≤1s
drift) and null otherwise.

- 2025-26: 0022500028 (González), 0022500054 (Sengun), 0022500116
  (Mann), 0022500138 (Bitadze), 0022500286 (Larsson), 0022500311
  (Antetokounmpo — a 10-second violation on the attempt), 0022500684
  (Hardaway Jr.), 0022501009 (Watkins), 0022501066 (Nesmith).
- 2024-25: 0022400020 (Gobert), 0022400120 (Beasley), 0022400251
  (Coffey), 0022400275 (Okoro), 0022400512 (Holmes), 0022400546
  (Sensabaugh), 0022400876 (Avdija), 0022401206 (Poeltl).

## Family 3 — trip sequences truncated by a cancellation (19 cases, v3+v4)

An own-team violation cancels the remaining attempt(s) of a trip: the
recorded sequence is a strict subset of the declared one, paired with a
same-clock own-team lane Violation or Turnover (the league-common
Turnover-typed offensive lane violation; one with a blank subtype,
0022500944 Knueppel). v4 (0022300173, Banchero) showed the cancelled
attempt can be the FIRST, leaving only "2 of 2". Resolution: any distinct
subset of the declared sequence plus a same-clock own-team cancellation
record truncates the trip to the free throws actually shot.

- 2025-26: 0022500065 (Edey), 0022500070 (Clowney), 0022500101
  (Holmgren), 0022500104 (Braun), 0022500133 (Walker), 0022500404
  (Martin), 0022500584 (Green), 0022500646 (Porter Jr.), 0022500657
  (Bridges), 0022500781 (Smith), 0022500940 (Capela), 0022500944
  (Knueppel), 0022501009 (Jenkins), 0022501101 (Ingram), 0022501179
  (Kuzma).
- 2024-25: 0022400086 (Henderson), 0022400885 (Butler III), 0022400999
  (Adams).
- 2023-24: 0022300173 (Banchero — cancelled first attempt, v4).

## Family 4 — administrations mis-subtyped by the scorer (2 cases, v3)

Three free throws are awarded only for a foul on a three-point attempt,
whatever subtype the scorer typed (0022400645, T. Jones — coded
"Personal"). Two free throws from an Away From Play foul is the penalty
administration (0022501070, Jay. Williams — the foul's own "(PN)" marker
confirms). Resolutions: declared 3 + any non-technical foul classifies
shootingFoul3; declared 2 + Away From Play classifies bonus.

## Family 5 — mid-trip declared-size correction (1 case, v3)

0022401150 (Brooks Jr.): "Free Throw 1 of 3" followed by "Free Throw
2 of 2" — the scorer corrected the administration mid-trip. Resolution:
when observed positions form 1..K and the final event declares K, the
trip's size is K.

## Family 6 — the feed omits the causing foul entirely (1 case, v4)

0022301195 (Prince): two free throws at a first-quarter-end clock with no
opponent foul anywhere in the game's feed at that clock or either period
edge (verified against the whole-game index). Resolution: a period-end
two-shot trip with a feed-omitted foul classifies shootingFoul2 as the
documented least-assumption fallback — the dominant buzzer
administration, and both candidate classes share the attempt-equivalent
tier, so tier arithmetic is invariant to the choice. The only occurrence
in 3,690 games.
