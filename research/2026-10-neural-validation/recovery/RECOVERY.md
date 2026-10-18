# SVZ sample recovery and source admission

**Verified — metadata and availability only, 2026-10-18.** Cohort 1 supplies a
same-study direction comparator with independent animals: two treated and two
controls, all male, 18–20 months, 1,194 cells, one 10x v3.0 lane. Cohort 2 uses
24–26-month old animals of both sexes and v3.1 chemistry. Ten named cell-type
labels agree, with different annotation collapses and 70 unresolved numeric
labels in cohort 2. These differences preclude exact replication.

The immutable [admission](cohort1-admission.json) was frozen in commit
`3adb9829224af9f17a6d6d01439ed91188f08c22`, SHA-256
`9dc8818d059d68f3991b3aa569e504e603cee1234e5e58f4bcb3ebf6c9eb3148`.
The separate [supplement corroboration](supplement-corroboration.json) preserves
that freeze. No expression outcomes were computed by this recovery lane.

The [source paper](https://pmc.ncbi.nlm.nih.gov/articles/PMC12036604/) specifies
three two-day doxycycline pulses separated by five-day intervals, with the
included treated animals harvested immediately after the last pulse. There is
no final-pulse withdrawal observation in either shared whole-body object.

| Cohort 1 animal | Treatment label | Cells | Supplementary Table 1 row |
|---|---|---:|---:|
| 961L | 2Dox0 | 212 | 5 |
| 955L | untr | 347 | 6 |
| 960L | 2Dox0 | 432 | 7 |
| 953L | untr | 203 | 8 |

The [publisher workbook](https://static-content.springer.com/esm/art%3A10.1038%2Fs43587-024-00594-3/MediaObjects/43587_2024_594_MOESM2_ESM.xlsx)
confirms the omitted animals were sequenced. Table 1 rows 9–10 list cohort 1
928L/929L; rows 18–22 list cohort 2 999L, B1, B2, B3 and L0034. The three B labels
join the author's BL61/BL62/BL63 via sample code, oligo, batch and lane. All 18
whole-body sample joins are preserved in [full-animal-source-map.json](full-animal-source-map.json).
Five animals have the author-code label `2Dox5`; none is observed in the shared
objects. Exact final withdrawal duration and blank sex/genotype entries for the
excluded animals remain unresolved. A treatment token is not a timing record.

Only `SuppTable1` worksheet XML and its referenced strings were read. Other
result worksheets were not opened. Code comments containing historical cell
counts were visible during source tracing; those comments were not treated as
newly recovered observations.

The deposited RNA headers contain 10,842 cohort 1 barcodes. Its 1,194 object
barcodes all match after validating and removing the uniform `-1` suffix within
GSM7022367. The remaining 9,648 barcodes have no recovered animal assignments.
The raw feature list has 31,054 rows versus 31,057 in the shared object, requiring
explicit alignment before any reconstruction. The three cohort 2 libraries
contain 3,006, 2,715 and 8,182 raw barcodes. All four feature lists contain only
Gene Expression entries.

[SRA original-file metadata](sources/ncbi-wholebody-runs.xml) lists 21 GEX files
for seven whole-body runs, with no separate LMO or Undetermined FASTQ listed.
The pinned author code uses Undetermined-derived LMO counts. FASTQ contents
remain uninspected; the catalog cannot establish whether barcode reads are
embedded in GEX files. Cohort 1 converted FASTQs alone total 44,207,239,760 bytes.
Acquisition is deferred until the exact multiplexing source is identified.
The [missing-input specification](missing-inputs.json) names the full
barcode-to-animal map, six/twelve-feature LMO matrices, pre-subsetting objects,
and timing records needed. No requests were sent and prior requests were left
untouched.

[Zenodo v2](https://zenodo.org/records/12613762), published July 1, 2024, replaces
the corrupted 161,955,840-byte continuous ciOSKM object with a 753,766,915-byte
file. The two whole-body files are byte-size/checksum identical across versions.
The corrected continuous object is deferred: it has one-week SVZ-targeted
induction, no withdrawal, and treated/control animals on entirely disjoint 10x
lanes. It does not resolve the present replication or withdrawal question.

The focused human/retinal search surfaced Yongmin Kwon's
[Cambridge thesis record](https://www.repository.cam.ac.uk/items/d696e1f1-d49a-4edb-878b-22133a7b15cd),
which describes inducible OKS and time-resolved single-cell induction/withdrawal
in human RPE1 cells. Official metadata confirms an embargo until **2027-04-07**.
No usable public counts, sample map or withdrawal timings were identified, so
this candidate is not admitted. It was accessioned April 7, 2026: newly found
in this search, not newly published since the previous audit. The bounded
Europe PMC publication-date query for October 16–18 returned zero hits; that is
not an exhaustive absence claim.

Source URLs, sizes, SHA-256 hashes and repository checksums are recorded in
[source-manifest.json](source-manifest.json). The two main downloads total
177,485,449 bytes: cohort 1 RDS MD5 `2dc0d3b98a3d5b257710352b2a69156d`;
workbook MD5 `a78aada4da430056e95d44851c6ba3e8`. Raw files remain in the documented
`/tmp` cache, within the 1 GB acquisition budget. Failures and exact next hooks
are in [failed-paths.json](failed-paths.json).

Verification from this folder:

```sh
PYTHONDONTWRITEBYTECODE=1 python3 build_recovery.py
PYTHONDONTWRITEBYTECODE=1 python3 verify_recovery.py
```

Expected: `PASS recovery verification 56/56`, including nine adversarial barcode
tests and source-byte validation. [verification.json](verification.json) is the
record. Checks are deterministic for pinned inputs; its timestamp varies. The
preliminary RDS count-integrity inspection validated integer, nonnegative sparse
counts and exact metadata totals without testing treatment effects.

**Next bounded computation:** the separately frozen cohort 1 direction
comparison can run on the cached 94 MB object. Metadata/hash regeneration takes
seconds and needs no additional downloads. Withdrawal reconstruction is blocked
on the specified assignment/timing inputs; its raw-read budget cannot yet be
justified. All four CX004 readouts remain `insufficient_signal` in this source
admission packet.
