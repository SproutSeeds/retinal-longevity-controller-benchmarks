import test from "node:test";
import assert from "node:assert/strict";

import {
  BUNDLE_ID,
  CONDITION_RECORD_SCHEMA,
  RELEASE_METADATA,
  buildCurrentBenchmarkSnapshot,
  getSchema,
  loadCurrentBenchmark,
  loadValidatedCurrentBenchmark,
  validateCurrentBenchmark,
} from "../src/index.js";

test("release metadata stays aligned with the current public bundle", () => {
  assert.equal(RELEASE_METADATA.package_name, "controller-benchmark");
  assert.equal(RELEASE_METADATA.bundle_id, "phase-stratified-controller-benchmark-v0");
  assert.deepEqual(RELEASE_METADATA.package_layers, [
    "controller-benchmark-schemas",
    "controller-benchmark-data",
    "controller-benchmark-js",
  ]);
});

test("curated schema re-exports are available", () => {
  assert.equal(BUNDLE_ID, "phase-stratified-controller-benchmark-v0");
  assert.equal(CONDITION_RECORD_SCHEMA.title, "Controller Benchmark Condition Record");
  assert.equal(getSchema("benchmarkShellReceipt").title, "Benchmark Shell Receipt");
});

test("current benchmark loader exposes the happy path object", () => {
  const benchmark = loadCurrentBenchmark();

  assert.equal(benchmark.bundleId, "phase-stratified-controller-benchmark-v0");
  assert.equal(benchmark.conditionRecords.length, 8);
  assert.equal(benchmark.ageOnlyRows.length, 8);
  assert.equal(benchmark.controllerRows.length, 8);
});

test("current benchmark validation stays green on the released bundle", () => {
  const benchmark = loadCurrentBenchmark();
  const validation = validateCurrentBenchmark(benchmark);

  assert.equal(validation.valid, true);
  assert.equal(validation.condition_record_count, 8);
  assert.deepEqual(validation.invalid_condition_ids, []);
});

test("snapshot helper preserves fail-closed shell behavior", () => {
  const benchmark = loadCurrentBenchmark();
  const snapshot = buildCurrentBenchmarkSnapshot(benchmark);

  assert.equal(snapshot.condition_count, 8);
  assert.equal(snapshot.outputs.fail_closed, true);
  assert.equal(snapshot.shell.fail_closed, true);
  assert.equal(snapshot.phase_counts.maturation_phase_bulk_plus_abstention, 4);
});

test("validated loader composes benchmark, validation, and snapshot", () => {
  const result = loadValidatedCurrentBenchmark();

  assert.equal(result.validation.valid, true);
  assert.equal(result.snapshot.study_family_counts.gill_2022, 3);
  assert.equal(result.snapshot.coverage.rule_backed_condition_count, 8);
});
