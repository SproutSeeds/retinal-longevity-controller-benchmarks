# Acute NSC culture comparator

**Verified metadata; analysis contract proposed before new expression outcomes.**
[GSE245385](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE245385)
contains 65 libraries from nine mouse donors. A18h has nine complete paired
control/treated cultures: old donors 940, 946, 966 and 967; young donors 1892,
1893, 1894, 1914 and 1926. Each pair has matching sex, NSC medium and 18-hour
sampling time. The old donors are 25 months (two female, two male); the young
donors are 3–4 months (three female, two male). Repeated time points do not add
independent donors. The exact GEO accessions and count columns are in
[admission.json](admission.json).

The [paper's Fig. 7a](https://pmc.ncbi.nlm.nih.gov/articles/PMC12036604/#F7)
confirms continued doxycycline after the switch to differentiation medium.
D06h/D18h/D48h therefore represent 24/36/66 hours of ongoing induction, not
withdrawal. A06h/A48h have old treated samples only; comparing either with A18h
controls would confound time. [Methods](https://pmc.ncbi.nlm.nih.gov/articles/PMC12036604/#S40)
also identify lower plating density at A48h. The proposed contract uses A18h
alone and retains all other samples as metadata.

The count header has 65 unique library columns. It joins GEO by explicitly
normalizing only the six-hour token (`A6h`/`D6h` to `A06h`/`D06h`). The leading
token is a **well**, as explicitly named by the
[author code](https://github.com/gitlucyxu/SVZreprogramming/blob/011586aea2e8612c794e57d2a260fa1a29d417a0/bulkRNAseq/DESeq2_analysis_chimeric_clean.R#L183).
It is not an inferred batch. H8's historical treatment mislabel is documented
in that code and already corrected to Dox in both the deposited header and GEO;
H8 is outside the A18h contrast. The detailed source protocol pools libraries
across three sequencing lanes; those lanes are technical replication.

The main paper already reports age-associated signatures and their reversal
with reprogramming, including selected 18-hour genes. Its
[bulk analysis methods](https://pmc.ncbi.nlm.nih.gov/articles/PMC12036604/#S41)
and pinned code use a combined condition factor with pairwise comparisons,
without a donor term. The contribution proposed here is a fixed-panel,
donor-paired audit and an age-group comparison of paired responses. It does not
establish a new biological discovery of age reversal or broader methodological
novelty.

The [contract](contract.json) retains the four pre-existing marker panels,
with the same orthology and transgene-overlap exclusion. Primary inference is
the age-group difference in paired CPM responses, with all 126 four-versus-five
age assignments and Holm correction across four panels. Overall donor sign
tests, median-ratio normalization and within-library ranks are separate
secondary families. Age-label exchangeability is an observational assumption;
all individual responses and gene contributions will be shown. A nonsignificant
result cannot establish equivalence.

The source custom reference includes rtTA and the three 2A sequences. Those
features do not prove that endogenous OSKM expression is separately measured.
The full reprogramming panel remains transgene-overlapping, and the restricted
panel remains a marker score without calibrated identity or safety meaning.
Bulk NSC cultures cannot supply human retinal recovery or per-cell rare-state
evidence.

**Bounded next computation:** download the 2,745,316-byte raw count gzip after
the root freeze, validate header and count integrity, and run the frozen
18-library analysis locally. Expected use is a few minutes and well below
1 GB RAM; this is an estimate, not a measured runtime. Only the first 1,024
compressed bytes were read for the header during admission; no count rows were
inspected. Published result text and author-code comments were seen and are
recorded as prior exposure. Source hashes and the header receipt are in
[source-manifest.json](source-manifest.json) and
[header-exposure.json](header-exposure.json).
