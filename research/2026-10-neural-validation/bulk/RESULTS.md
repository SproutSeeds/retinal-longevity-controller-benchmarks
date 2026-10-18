# Nine-donor acute NSC panel responses

**Heuristic biological interpretation; verified arithmetic.** The frozen A18h
analysis finds four CPM age-response differences with Holm-adjusted p-values
below 0.05 under the declared age-label exchangeability assumption. Median-ratio
normalization agrees. The rank sensitivity retains no age-test rejection and
reverses the stress-panel difference. The cycle-panel score decreases in all
nine donors under all three methods, including every single-gene omission.
The overlap-excluded reprogramming age contrast depends on Nanog and changes
sign when that gene is omitted. These are acute expression summaries in mouse
NSC cultures.

The source is [GSE245385](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE245385).
The 18-hour cultures remain under doxycycline/OSKM exposure. Four old and five
young donors provide paired treated/untreated cultures; each donor has equal
weight. The 65 libraries across the full experiment are not 65 donors. All 18
selected libraries pass the frozen support rule, with 19,356–20,304 detected
features. The matrix has 31,057 features. Panel coverage is 20/20 cycle, 7/8
stress (CXCL8 unmapped), 9/9 full reprogramming and 7/7 overlap-excluded.

The primary scale is the difference in a panel's unweighted mean
`log2(1 + CPM)` score. Delta is treated minus untreated within each donor; the
age statistic is old mean Delta minus young mean Delta. These are score units,
not a cell fraction, age change or gene-expression fold ratio.

| Panel | Old mean Delta | Young mean Delta | Age difference | Exact age p | Holm p |
|---|---:|---:|---:|---:|---:|
| Cycle | −0.179293 | −0.265831 | +0.086538 | 2/126 | 0.047619 |
| Stress | −0.023910 | +0.071493 | −0.095404 | 3/126 | 0.047619 |
| Full reprogramming | +0.021855 | +0.073004 | −0.051149 | 1/126 | 0.031746 |
| Overlap-excluded reprogramming | −0.008146 | +0.013840 | −0.021986 | 3/126 | 0.047619 |

All four tests belong to the predeclared primary Holm family. The smallest p
passes the first step; later steps allow the 2/126 and 3/126 results to pass.
There was no reduction of the family after seeing outcomes.

Every primary paired response is shown below; [paired-responses.csv](paired-responses.csv)
contains all 108 panel/method/donor rows, exact values, well labels and GEO IDs.

| Donor | Age | Control → treated well | Cycle | Stress | Full reprogramming | Overlap-excluded |
|---|---|---|---:|---:|---:|---:|
| 940 | old | A3 → E3 | −0.197374 | +0.021041 | −0.009275 | −0.007923 |
| 946 | old | B2 → G2 | −0.187888 | −0.032160 | +0.029371 | −0.014497 |
| 966 | old | B3 → F3 | −0.194136 | −0.045208 | +0.016127 | −0.015871 |
| 967 | old | C2 → H2 | −0.137774 | −0.039314 | +0.051196 | +0.005706 |
| 1892 | young | E1 → D2 | −0.247309 | +0.121945 | +0.069711 | +0.014213 |
| 1893 | young | F1 → C3 | −0.270974 | +0.085377 | +0.072203 | +0.017763 |
| 1894 | young | G1 → E2 | −0.212467 | +0.066101 | +0.067832 | +0.014425 |
| 1914 | young | H1 → D3 | −0.258553 | +0.088894 | +0.091767 | −0.002369 |
| 1926 | young | A2 → F2 | −0.339856 | −0.004850 | +0.063505 | +0.025167 |

Median-ratio age differences are +0.088794 cycle, −0.093549 stress,
−0.050824 full reprogramming and −0.021581 overlap-excluded, with the same exact
p-value numerators and Holm values as CPM. Rank differences are +0.005881,
+0.009515, −0.003533 and −0.001099 respectively; rank age-test Holm values are
0.063492 for cycle and 1 for the other panels. Rank has a different scale and
is also sensitive to expression composition and detection. This disagreement
limits interpretation of the CPM age comparisons.

The overlap-excluded score is particularly gene-sensitive. Nanog contributes
−0.028038 to its net CPM age difference of −0.021986; the other genes partly
offset that contribution. Omitting Nanog changes the age difference to
+0.007061. Median-ratio scoring has the same dependence: net −0.021581,
Nanog contribution −0.028005, and omission result +0.007495. Its rank age-test
Holm p is 1. This contrast therefore does not demonstrate a broad coordinated
endogenous reprogramming response. Independently, the stress age difference
changes from −0.095404 under CPM to +0.009515 under rank scoring.

The separate overall-response sign-test family supports the cycle-score
decrease: 9/9 negative donor responses, exact p = 2/512 and Holm p = 0.015625
under all three methods. The other overall sign-test Holm values exceed 0.05.
Those results do not establish equivalence or absence of a response.

The cycle result is distributed across its fixed genes. All twenty genes have
negative overall mean contributions. Ccnb1, Birc5 and Ube2c contribute most to
the CPM mean decrease; the largest single contribution is about 6.9% of that
signed mean. Cenpf and Mki67 together contribute about 34.8% of the CPM
old-minus-young response difference. Under all three methods, removing any one
cycle gene preserves every donor's negative response and the positive age
difference. For CPM, the overall mean is −0.227370 and the single-gene-omission
range is −0.232975 to −0.222812.

Removing any one donor also preserves the overall negative mean and positive
age difference under all three methods. The CPM overall-mean range is
−0.238569 to −0.213309. The additional overall-mean omission summaries and
MR/rank donor summaries were requested after outcomes and hold the frozen
normalization fixed; they are labeled post hoc in
[cycle-robustness.json](cycle-robustness.json). No additional p-values were
introduced. The original gene omissions and CPM age-statistic donor omissions
were predeclared.

Age-label inference requires exchangeability of the complete donor-response
distribution, not simply equality of means. Age was not randomized. The paired
well labels align differently with age groups, but they do not establish
preparation batch, plate identity or chronological processing order. An
unmeasured technical trend following that layout remains a possible explanation.
Pairing also cannot separate doxycycline from OSKM or remove bulk cell-mixture
effects. The full reprogramming panel overlaps introduced factors; the four
custom features (`M2rtTAADDGENE20342FULL`, P2A, T2A, E2A) do not make endogenous
OSKM expression separately identifiable. The fixed overlap-excluded panel is
not a calibrated identity or pluripotency assay.

The source paper already reported age/reprogramming transcriptional changes.
This result adds the specified paired-panel audit; it does not establish an
age-specific mechanism, cell-cycle arrest, rejuvenation, lasting recovery,
human retinal efficacy or safety. All four CX004 readouts remain
`insufficient_signal`.

The contract and code were frozen at
`60a4fc5f1dc86f73e18d137f6bf50a2e8a92a63a`. The raw count gzip is 2,745,316
bytes, SHA-256 `8a057b616cc6807534650b83d40bbbae8dc50bdfdb5a47ce02dd93e8dc5d76be`.
Acquisition plus analysis took 3.64 seconds in the initial run. No frozen code
amendment was needed.

Verification:

- [VERIFICATION.json](VERIFICATION.json): 127/127 independent raw-table checks,
  using a separate reader, SciPy tied ranks and binomial tests.
- [SAVED_VERIFICATION.json](SAVED_VERIFICATION.json): saved-output consistency,
  exact tests and artifact/source hash binding; runs without raw acquisition.
- [PORTABLE_REPLAY.json](PORTABLE_REPLAY.json): 11/11 checks from an archive
  outside git, with relocated cache/output directories. Numerical arrays and
  the gene CSV are identical. The replay receipt explicitly states that
  historical git proof was not rerun.
- [PRE_OUTCOME_VERIFICATION.json](PRE_OUTCOME_VERIFICATION.json): 14/14 metadata
  checks and twenty synthetic tests before outcomes. The final freeze also
  includes the root's documented prose clarifications.

CI commands from this folder, with no biological raw-data acquisition:

```sh
python3 verify_saved.py
PYTHONDONTWRITEBYTECODE=1 uv run --python 3.12 --with numpy==2.5.4 python -B -m unittest -v test_bulk.py
```

Explicit source replay from an exported archive:

```sh
uv run --script analyze.py --replay-frozen-hashes --cache /path/to/cache --output /path/to/results
uv run --script verify_results.py --cache /path/to/cache --result-dir /path/to/results --output /path/to/verification
```

If the count cache is absent, the first command downloads the public 2.7 MB file
and validates its archived hash. Omit `--replay-frozen-hashes` in the original
repository to require historical committed-byte verification.
