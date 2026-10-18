# Animal-level neural comparison

**Proposal / Conjecture:** test whether a within-cell-type expression difference persists after keeping animal identity, sequencing lane and cell composition explicit. The admission scout has verified the cohort-2 cell/count mapping. Expression outcomes remain unexamined.

The next implementation should freeze a separate contract before computing outcomes. Its natural primary comparison is old OSKM treated versus old OSKM untreated. Cohort 2 supplies two treated animals and three controls. A lane-balanced sensitivity restricts controls to lanes 1 and 2; the extra lane-3 control remains an explicit secondary comparison. Young controls share only lane 3 and therefore cannot supply an unconfounded age-reversal test.

1. Sum raw RNA counts by animal and existing biological cell type. Keep unresolved numeric clusters visible in composition denominators and exclude them from named-cell-type claims. Freeze the minimum cells and genes per animal/type before evaluating expression; report every failure rather than silently discarding sparse animals.
2. Report recovered-cell proportions separately from within-cell-type pseudobulk expression. The denominator must state whether it includes all recovered cells or a named subset. Neither denominator estimates tissue abundance without additional evidence.
3. Use independently fixed mouse gene sets with explicit human/mouse orthology handling, rather than selecting genes because they moved in this dataset. Report the OSKM-transgene overlap separately. Use both library-depth and median-ratio sensitivities and leave-one-animal/lane sensitivity where the remaining replication permits it.
4. Inspect the separate cohort-1 object and its animal map before treating it as a replication cohort. Freeze the discovery/replication split before opening expression outcomes. If conditions, timing or cell labels differ, report a comparator rather than claiming independent replication.
5. Publish per-animal results, sparse/failed strata, compositional limitations and any disagreement. Avoid cell-level hypothesis tests that treat thousands of cells as thousands of independent animals. Two treated animals remain weak evidence even with many cells.

The downloaded cohort-2 RDS omits five of the twelve animal labels in the author mapping, including all withdrawal and BL6 groups. Recovering a broader object or raw multiplexing assignments is a separate data task. Do not infer absent observations from unused factor levels or author-code variable names.

This analysis can assess portability of expression diagnostics to the mouse neural niche. Late human recovery, retinal function and calibrated rare-state risk remain separate validation targets.
