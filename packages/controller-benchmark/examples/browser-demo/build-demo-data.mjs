import { writeFileSync } from "node:fs";

import {
  BUNDLE_ID,
  loadLatestBundle,
  readAgeOnlyBaselineOutputRows,
  readControllerOutputRows,
} from "../../../controller-benchmark-data/src/index.js";

import {
  buildBenchmarkSnapshot,
  compareOutputs,
  summarizeCoverageTrust,
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
  outputs: compareOutputs(ageOnlyRows, controllerRows),
  snapshot: buildBenchmarkSnapshot({
    conditionRecords: bundle.conditionRecords,
    coverageTrustReceipt: bundle.coverageTrustReceipt,
    benchmarkShellReceipt: bundle.benchmarkShellReceipt,
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
