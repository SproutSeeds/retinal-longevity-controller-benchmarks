import { writeFileSync } from "node:fs";

import {
  BUNDLE_ID,
  loadLatestBundle,
  readAgeOnlyBaselineOutputRows,
  readCx004ExampleInsufficientResolutionReviewReceipt,
  readCx004ResolutionReviewContract,
  readControllerOutputRows,
  readCx004ValidationHandoff,
  readCx004ValidationHandoffReceipt,
  readPassiveRecommendationReceipt,
  readPassiveRecommendationScaffold,
} from "../../../controller-benchmark-data/src/index.js";

import {
  buildBenchmarkSnapshot,
  compareOutputs,
  summarizeCx004ResolutionReviewGate,
  summarizeCx004ValidationHandoff,
  summarizeCoverageTrust,
  summarizePassiveRecommendationScaffold,
  summarizeShellReceipt,
} from "../../../controller-benchmark-js/src/index.js";

import {
  validateBenchmarkShellReceipt,
  validateCompilerCoverageTrustReceipt,
  validateConditionRecord,
} from "../../../controller-benchmark-schemas/src/index.js";

const bundle = loadLatestBundle();
const ageOnlyRows = readAgeOnlyBaselineOutputRows();
const controllerRows = readControllerOutputRows();
const cx004ValidationHandoff = readCx004ValidationHandoff();
const cx004ValidationHandoffReceipt = readCx004ValidationHandoffReceipt();
const cx004ResolutionReviewContract = readCx004ResolutionReviewContract();
const cx004ExampleInsufficientResolutionReviewReceipt =
  readCx004ExampleInsufficientResolutionReviewReceipt();
const passiveRecommendationScaffold = readPassiveRecommendationScaffold();
const passiveRecommendationReceipt = readPassiveRecommendationReceipt();

const conditionValidation = bundle.conditionRecords.map((record) => ({
  condition_id: record.condition_id,
  ...validateConditionRecord(record),
}));

const payload = {
  generated_on: new Date().toISOString(),
  bundle_id: BUNDLE_ID,
  validation: {
    valid:
      conditionValidation.every((result) => result.valid) &&
      validateCompilerCoverageTrustReceipt(bundle.coverageTrustReceipt).valid &&
      validateBenchmarkShellReceipt(bundle.benchmarkShellReceipt).valid,
    condition_record_count: bundle.conditionRecords.length,
    invalid_condition_ids: conditionValidation
      .filter((result) => result.valid === false)
      .map((result) => result.condition_id),
  },
  coverage: summarizeCoverageTrust(bundle.coverageTrustReceipt),
  shell: summarizeShellReceipt(bundle.benchmarkShellReceipt),
  validation_handoff: summarizeCx004ValidationHandoff(
    cx004ValidationHandoff,
    cx004ValidationHandoffReceipt,
  ),
  resolution_review_gate: summarizeCx004ResolutionReviewGate(
    cx004ResolutionReviewContract,
    cx004ExampleInsufficientResolutionReviewReceipt,
  ),
  recommendations: summarizePassiveRecommendationScaffold(
    passiveRecommendationScaffold,
    passiveRecommendationReceipt,
  ),
  outputs: compareOutputs(ageOnlyRows, controllerRows),
  snapshot: buildBenchmarkSnapshot({
    conditionRecords: bundle.conditionRecords,
    coverageTrustReceipt: bundle.coverageTrustReceipt,
    benchmarkShellReceipt: bundle.benchmarkShellReceipt,
    contradictionLedger: bundle.contradictionLedger,
    cx004ValidationHandoff,
    cx004ValidationHandoffReceipt,
    cx004ResolutionReviewContract,
    cx004ExampleInsufficientResolutionReviewReceipt,
    passiveRecommendationScaffold,
    passiveRecommendationReceipt,
    ageOnlyRows,
    controllerRows,
  }),
  condition_records: bundle.conditionRecords,
};

writeFileSync(
  new URL("./benchmark-snapshot.json", import.meta.url),
  `${JSON.stringify(payload, null, 2)}\n`,
);

console.log(
  `Wrote browser demo snapshot for ${payload.bundle_id} to benchmark-snapshot.json`,
);
