# Submission notes — SSAC27 research papers competition

## The rules that bind the abstract

- Due **Oct 1, 2026, 11:59 p.m. EST**, submitted online.
- **Under 500 words including the title.** Verify with the counter before
  any submission:
  `python -c "import re,pathlib;t=pathlib.Path('paper/abstract.md').read_text(encoding='utf-8');print(len(re.findall(r'\S+',re.sub(r'^#+\s*','',t,flags=re.M))))"`
- **At most two tables/figures combined.** Ours: Figure 1 =
  `analysis/output/exhibit1-persistence.png`, Table 1 =
  `analysis/output/exhibit2-taxonomy.md` (typeset at submission).
- Required sections: Introduction, Methods, Results, Conclusion — Results
  must be actual, not promised.
- **Blind review**: no author names, no naming the author's other
  projects. The Sanders & Ehrlich positioning stays as "recent work"
  (cite fully only in the manuscript phase).
- Submission requires a link to the public repository (this one).

## Draft state

- v2 (2026-08-11): 488 words including title, both exhibits cited, all
  numbers verified against `analysis/output/`. Every future edit that
  touches a number gets re-checked there before landing.
- v3 (2026-09-21, red-pen in progress): title tightened to "The Trip
  Economy: Which Foul-Drawing Skills Travel?"; the Introduction's
  positioning sentence de-jargoned ("shot-pursuant" is gone; "the rest
  of the trip economy" picks up the title's coined term); Methods'
  "versioned grammar" sentence replaced with plain tracing/classifying
  language (the grammar story is manuscript material); Results' back
  half rewritten for readability (dangling "279 of 284" resolved,
  "median premium" spelled out, Fisher z dropped in favor of p, "travels
  intact" echoes the title, 0.44 sentence opens with the finding);
  Conclusion opens by answering the title's question in two short
  sentences, and the redundant dataset-release closer is cut (Methods
  already says it; the form has a repo-link field); final consistency
  read fixed the pooled-panel parenthetical to "across two season pairs,
  same ordering in both" (the replication claim, now legible). 487 words
  incl. title — 12 of headroom.
- v4 (2026-09-23, after the external review — see docs/build-plan.md):
  reframed on the corrected analysis. The headline is the gradient with
  rate-based reliability ceilings; the team-change comparison is a
  secondary result stated with its uncertainty (54 clean movers; every
  channel drops; the bonus gap is largest but its bootstrap CI spans
  zero). Cut for words: the line premium (and its question in the
  Introduction) and the Jokić example (its punchline was the withdrawn
  off-ball mechanism). Wording fixes from the review: "non-shooting" for
  bonus, "regular-season", the 1,723 count refers to reconciled league
  player-seasons, "the pattern holds in both season pairs" (SF3 and
  and-one swap between transitions), scoring-attempt language for the
  attempt-equivalent tier, existing trip-classification tooling
  acknowledged ("countable with existing tools but unstudied as a
  skill"), the TS median beside the max, and "discount" replaced by
  destination-context projection with wider uncertainty. 484 words incl.
  title — 15 of headroom.

## The submission file (checked 2026-09-21)

The portal (linked from the SSAC research-paper page; a Google Form,
sign-in required) takes ONE uploaded file plus separate text fields for
the title, category (Basketball), and the open-source repo link. So the
abstract, Figure 1, and Table 1 are submitted as a single PDF:

- `python paper/build_submission.py` -> `paper/submission.pdf`,
  assembled from `abstract.md` + the committed `analysis/output/`
  exhibits (the table is parsed, never hand-transcribed). The build
  hard-fails at >= 500 words including title and on any
  author-identifying string (blind review). Rebuild after ANY edit to
  the abstract or a re-render of the exhibits.
- Page 1 of the form is author info (name, contact, demographics) —
  filled by the author at submission time.

## If the full-paper invitation arrives (due Dec 4, 2026)

Planned upgrades, in order (see docs/build-plan.md):

1. Per-game player lines — DONE 2026-09-23 (`player_games.csv`). Next on
   top of them: the midseason-trade event study (the 84 mixed transitions
   plus every midseason move — within-player pre/post rates by channel),
   the causal upgrade of the team-change comparison; and the reviewer's
   forecasting test (fit a projection on the first transition, evaluate
   on the second; aggregate FT-rate forecast vs channel-specific,
   especially for movers) — direct evidence of practical value.
2. Hierarchical Poisson modeling of channel rates (game-grain counts with
   exposure offsets) as the dressed-up version of the correlation
   analyses.
3. Full citations (Kubatko et al. 2007 for the 0.44 derivation; Sanders &
   Ehrlich 2024; the Four Factors literature for foul-rate stability;
   pbpstats for prior exact-counting practice).
4. Do NOT add seasons before 2023-24: the transition-take rule (2022-23)
   and the one-free-throw flopping technical (2023-24) bound the clean
   same-rules era.
