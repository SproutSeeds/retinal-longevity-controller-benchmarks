# Gill archive recovery and source compatibility

Claim level: **Verified**, confined to source identity, archive inventories and the reviewed admission disposition.

Three Cambridge source objects recovered on November 1 match the previously recorded repository sizes and MD5 checksums. A publisher-hosted accepted-manuscript ZIP was also recovered. Both ZIPs have intact CRCs, and their workbooks and reporting form match byte-for-byte. Their inventories supply no new numerical migration table or culture/RNA crosswalk.

The thesis places scratch-wound assays in future work and presents a clock result with different reported error and group coverage from final-paper Figure 3C. This establishes a source-version distinction, without identifying its cause or proving which internal model artifacts changed. No thesis plot-derived age is admitted as a final-paper per-RNA age.

Verification hook, from the repository root:

```sh
python3 programs/partial-reprogramming-controller/benchmarks/gill-archive-review-2026-11-01/verify.py
python3 programs/partial-reprogramming-controller/benchmarks/gill-archive-review-2026-11-01/verify.py --sources programs/partial-reprogramming-controller/.data/gill-source-recovery-2026-11-01
```

Expected: PASS for the bound artifacts and frozen inputs; the second command additionally checks four retained source files and 21 archive-member occurrences. Full source checks are deterministic for the pinned files. Network reacquisition is separate. Missing source files yield INCONCLUSIVE; changed source bytes yield FAIL. See `VERIFICATION_RECORD.md` for the executed verification.

The original 13-contrast contract is unchanged, no numerical analysis is run, and new joint admissions remain zero. The comparison stays DEFERRED / INCONCLUSIVE. The three required input roles and Phase 483 external-exchange gate remain open. The finding covers only the reviewed files and does not establish global data absence. Gill et al. retain biological-discovery credit.
