import {
  BENCHMARK_SHELL_RECEIPT_SCHEMA,
  COMPILER_COVERAGE_TRUST_RECEIPT_SCHEMA,
  CONDITION_RECORD_COMPILE_RECEIPT_SCHEMA,
  CONDITION_RECORD_SCHEMA,
  getSchema,
  listSchemas,
  validateBenchmarkShellReceipt,
  validateCompilerCoverageTrustReceipt,
  validateConditionRecord,
  validateConditionRecordCompileReceipt,
} from "controller-benchmark-schemas";

import {
  BUNDLE_ID,
  BUNDLE_MANIFEST,
  getArtifactPath,
  getArtifactUrl,
  listArtifacts,
  listCompilerRules,
  loadLatestBundle,
  readAgeOnlyBaselineOutputRows,
  readBenchmarkShellReceipt,
  readCompileReceipt,
  readCompilerRule,
  readConditionFixture,
  readConditionRecords,
  readControllerOutputRows,
  readCoverageTrustReceipt,
  readNegativeFamilyRegistry,
  readStudyCorpusRows,
} from "controller-benchmark-data";

import {
  BASELINE_OUTPUTS,
  CONTROLLER_OUTPUTS,
  buildBenchmarkSnapshot,
  compareOutputs,
  countBy,
  groupConditionRecordsByPhase,
  groupConditionRecordsByStudyFamily,
  indexConditionRecords,
  listNegativePressureConditions,
  summarizeCoverageTrust,
  summarizeShellReceipt,
} from "controller-benchmark-js";

export {
  BASELINE_OUTPUTS,
  BENCHMARK_SHELL_RECEIPT_SCHEMA,
  BUNDLE_ID,
  BUNDLE_MANIFEST,
  COMPILER_COVERAGE_TRUST_RECEIPT_SCHEMA,
  CONDITION_RECORD_COMPILE_RECEIPT_SCHEMA,
  CONDITION_RECORD_SCHEMA,
  CONTROLLER_OUTPUTS,
  buildBenchmarkSnapshot,
  compareOutputs,
  countBy,
  getArtifactPath,
  getArtifactUrl,
  getSchema,
  groupConditionRecordsByPhase,
  groupConditionRecordsByStudyFamily,
  indexConditionRecords,
  listArtifacts,
  listCompilerRules,
  listNegativePressureConditions,
  listSchemas,
  readAgeOnlyBaselineOutputRows,
  readBenchmarkShellReceipt,
  readCompileReceipt,
  readCompilerRule,
  readConditionFixture,
  readConditionRecords,
  readControllerOutputRows,
  readCoverageTrustReceipt,
  readNegativeFamilyRegistry,
  readStudyCorpusRows,
  summarizeCoverageTrust,
  summarizeShellReceipt,
  validateBenchmarkShellReceipt,
  validateCompilerCoverageTrustReceipt,
  validateConditionRecord,
  validateConditionRecordCompileReceipt,
};

function assertBundle(value) {
  if (!value || typeof value !== "object") {
    throw new TypeError("bundle must be an object");
  }
}

export const RELEASE_METADATA = Object.freeze({
  package_name: "controller-benchmark",
  release_channel: "public",
  steward: "SproutSeeds",
  research_stewardship: "Fractal Research Group",
  bundle_id: BUNDLE_ID,
  bundle_condition_count: BUNDLE_MANIFEST.condition_count ?? 0,
  package_layers: Object.freeze([
    "controller-benchmark-schemas",
    "controller-benchmark-data",
    "controller-benchmark-js",
  ]),
});

export function loadCurrentBenchmark() {
  return {
    ...loadLatestBundle(),
    ageOnlyRows: readAgeOnlyBaselineOutputRows(),
    controllerRows: readControllerOutputRows(),
  };
}

export function validateCurrentBenchmark(bundle = loadCurrentBenchmark()) {
  assertBundle(bundle);

  const conditionRecordResults = (bundle.conditionRecords ?? []).map((record) => ({
    condition_id: record.condition_id ?? "unknown",
    ...validateConditionRecord(record),
  }));

  const compileReceiptResult = validateConditionRecordCompileReceipt(
    bundle.compileReceipt,
  );
  const coverageTrustReceiptResult = validateCompilerCoverageTrustReceipt(
    bundle.coverageTrustReceipt,
  );
  const benchmarkShellReceiptResult = validateBenchmarkShellReceipt(
    bundle.benchmarkShellReceipt,
  );

  const invalidConditionIds = Object.freeze(
    conditionRecordResults
      .filter((result) => result.valid === false)
      .map((result) => result.condition_id)
      .sort(),
  );

  return {
    valid:
      invalidConditionIds.length === 0 &&
      compileReceiptResult.valid === true &&
      coverageTrustReceiptResult.valid === true &&
      benchmarkShellReceiptResult.valid === true,
    bundle_id: bundle.bundleId ?? BUNDLE_ID,
    condition_record_count: Array.isArray(bundle.conditionRecords)
      ? bundle.conditionRecords.length
      : 0,
    invalid_condition_ids: invalidConditionIds,
    validation: Object.freeze({
      condition_records: Object.freeze(conditionRecordResults),
      compile_receipt: compileReceiptResult,
      coverage_trust_receipt: coverageTrustReceiptResult,
      benchmark_shell_receipt: benchmarkShellReceiptResult,
    }),
  };
}

export function buildCurrentBenchmarkSnapshot(bundle = loadCurrentBenchmark()) {
  assertBundle(bundle);

  return buildBenchmarkSnapshot({
    conditionRecords: bundle.conditionRecords ?? [],
    coverageTrustReceipt:
      bundle.coverageTrustReceipt ?? readCoverageTrustReceipt(),
    benchmarkShellReceipt:
      bundle.benchmarkShellReceipt ?? readBenchmarkShellReceipt(),
    ageOnlyRows: bundle.ageOnlyRows ?? readAgeOnlyBaselineOutputRows(),
    controllerRows: bundle.controllerRows ?? readControllerOutputRows(),
  });
}

export function loadValidatedCurrentBenchmark() {
  const benchmark = loadCurrentBenchmark();
  return {
    benchmark,
    validation: validateCurrentBenchmark(benchmark),
    snapshot: buildCurrentBenchmarkSnapshot(benchmark),
  };
}
