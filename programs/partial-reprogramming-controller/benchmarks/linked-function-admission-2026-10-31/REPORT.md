# RNA and measured function across eight human-cell studies

Title: RNA and measured function across eight human-cell studies

**Verified, source-audit scope:** the bounded eight-study review recovered 177 public RNA metadata records, 13 source-labeled treated/control RNA contrasts from three Gill donor labels, and ten Schiff functional-line summaries covering 26 reported experiments. These are input and provenance results. **Joint RNA/function analysis remains deferred for all eight candidates.** No new expression effects or molecular/function correlations were computed.

**Heuristic priority:** recover Gill's culture-labeled migration observations and their mapping to the RNA samples. This is the most direct next acquisition question for the current molecular/function gap. The adult-origin fibroblast lineage and its temporary identity transition require their own scope; this source does not replace adult-primary ocular evidence.

| Acquisition priority | Source | RNA records recovered | Functional context | Remaining decision-critical input |
|---|---|---:|---|---|
| 1 | Gill 2022, GSE165177 | 95 | Fibroblast migration after transient reprogramming | Exact migration observations, culture mapping and compatible collection context |
| 2 | Schiff 2019, GSE126633 | 8 | Adult-primary RPE pathological contraction | Map A-J functional lines to the deposited RNA donor labels and assay experiments |
| 3 | Sarkar 2020, PRJNA598923 | 18 | Adult-origin cell physiology; lineage-specific assays | Processed RNA inputs and same-cell-type donor/culture/function mapping |
| 4 | Inana 2018 | 0 | Adult-primary RPE outer-segment uptake | Public per-sample matrix and culture-linked uptake data not recovered |
| 5 | Piskova 2026, GSE297557 | 8 | iPSC-RPE uptake impairment and separate rescue | RNA/function experiment crosswalk; rescue RNA if recovery is evaluated |
| 6 | Schreiter 2020, GSE132828 | 21 | Stem-cell-derived RPE uptake | Assay/batch mapping, numerical functional inputs and dose/vehicle reconciliation |
| 7 | Saini 2017, GSE90889 | 14 | iPSC-RPE disease biomarkers | A mapped direct functional endpoint and complete source/reuse review |
| 8 | Butler 2021, GSE159435 | 13 | Adult-primary RPE age reference | This reference supplies no admitted linked functional endpoint |

The priority order is a provisional internal acquisition heuristic, pending human priority review. The 177 records include repeated donors, culture states, treatments and reference libraries; they are not 177 independent biological units. A zero in this table means zero RNA records recovered by this audit, not zero samples in the original experiment. The [candidate registry](CANDIDATES.json) retains narrower allowed uses even when joint admission fails.

## The RNA-side comparison now has exact identifiers

[Gill et al.](https://elifesciences.org/articles/71624) report variable migration responses and discuss their relationship to molecular aging measures. Those published observations make a useful known-outcome challenge; they are the investigators' findings.

The SuperSeries GSE165180 mixes expression and methylation studies. Its transient RNA subseries is [GSE165177](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE165177). The 95 RNA records contain 55 final-outgrowth libraries, 35 intermediate libraries, three starting-fibroblast libraries and two iPSC references. Their source titles yield 13 final-treated/control contrasts, distributed across donor labels O1/O2/O3 and experiments 1/2 at 10, 13, 15 or 17 reprogramming days. Those source duration labels are not measurements of withdrawal persistence.

[gill-rna-pairs.tsv](gill-rna-pairs.tsv) retains every control/treated accession, donor label, recorded donor age, duration and experiment. Each row explicitly leaves the function-unit field empty and marks joint function admission false. Repeated contrasts from the same three donor labels remain repeated donor observations. Unequal final-outgrowth representation, intermediate states and iPSC references must be handled before any new RNA comparison. Matching this manifest to migration measurements is a separate source-admission step.

## The RPE function table uses a different identifier system

[Schiff et al.](https://www.nature.com/articles/s42003-019-0406-6) supply RNA samples labeled with donor identifiers 15, 18 and 37, alongside two separately scoped patient membranes. Supplementary Table 1 on PDF page 7 supplies ten functional-line summaries labeled A-J. The experiment counts sum to 26. The reported mean and variability are line summaries rather than raw per-experiment measurements; a zero reported variability for a single experiment does not establish absence of biological variation.

[schiff-function-line-summaries.tsv](schiff-function-line-summaries.tsv) preserves those summaries without assigning RNA donor identities. A-to-15 or B-to-18 pairing by position would fabricate an assay crosswalk. The main article and reporting documents use broader line/replication descriptions; the ten-row table's coverage alone cannot resolve all line identities. Existing condition-level RNA and contraction observations remain useful within their original scope.

## Other sources keep distinct roles

The current [Sarkar article](https://www.nature.com/articles/s41467-020-15174-3) and ENA records identify PRJNA598923 as the RNA source, with 18 human RNA-Seq run records. GSE142439 is a methylation study. The alternative PRJNA589823 query returned no read-run rows in this ENA view; this bounded response is not a global absence claim. Raw reads were not downloaded or processed. Muscle or chondrocyte outcomes cannot be attached to fibroblast/endothelial RNA simply because they appear in the same article.

[Inana et al.](https://link.springer.com/article/10.1186/s12967-018-1434-6) offer a particularly relevant adult-primary RPE functional context, while their reviewed availability statement directs data requests to the authors. A reusable per-sample matrix and assay crosswalk were not recovered in this bounded pass. This remains a specific acquisition lead.

The Piskova, Schreiter and Saini inputs preserve useful impairment, compound-response and biomarker challenges. Their pluripotent-derived systems remain distinct from adult-primary cells. Butler's completed age reference stays a calibration source. Full Saini article XML retrieval failed; the current review retains its GEO metadata, primary bibliographic record and earlier analysis limits rather than presenting an exhaustive supplement review.

## Decision and verification boundary

The next input object is an existing migration table with original culture/experiment IDs, donor labels, treatment/duration, collection context, numerical values, units and technical-replicate handling, plus an authoritative crosswalk to the listed RNA accessions. Explicitly matched sibling cultures may support a culture-level comparison when their contexts agree. A donor-only association, condition-only match or local row number is insufficient for this contract. Destructive molecular assays do not establish same-cell continuity.

The executable intake checks reject missing authority, row-order joins, mismatched donor/culture/exposure/collection fields, reused observations, biomarkers substituted for direct function and unsupported system promotion. The synthetic positive control exists only in tests and never enters the observed candidate roster. The checks establish deterministic handling of the reviewed inputs; source biology and the curation require scientific review.

This packet supports no new rejuvenation, clinical, safety, persistence or wet-lab-replacement conclusion. The existing human readouts remain insufficient_signal, wet-lab replacement remains INCONCLUSIVE, and the RGC assessment remains maturation/support_only. Phase 483 still requires a genuine supervised external packet exchange. No further correspondence, paid compute or experiment was initiated.

See [VERIFICATION_RECORD.md](VERIFICATION_RECORD.md) for hooks and [FAILED_PATHS.json](FAILED_PATHS.json) for preserved acquisition and admission failures. Original investigators retain biological discovery credit; the project contribution is the source-bound admission audit and its reproducible input checks.
