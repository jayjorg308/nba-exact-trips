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

## If the full-paper invitation arrives (due Dec 4, 2026)

Planned upgrades, in order (see docs/build-plan.md):

1. Per-game player lines from the already-parsed box scores (zero new
   pulls) — enables the midseason-trade event study: within-player
   pre/post-trade bonus vs shooting-foul rates, the causal upgrade of the
   context test.
2. Hierarchical Poisson modeling of channel rates (game-grain counts with
   exposure offsets) as the dressed-up version of the correlation
   analyses.
3. Full citations (Kubatko et al. 2007 for the 0.44 derivation; Sanders &
   Ehrlich 2024; the Four Factors literature for foul-rate stability;
   pbpstats for prior exact-counting practice).
4. Do NOT add seasons before 2023-24: the transition-take rule (2022-23)
   and the one-free-throw flopping technical (2023-24) bound the clean
   same-rules era.
