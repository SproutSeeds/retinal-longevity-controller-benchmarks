import test from "node:test";
import assert from "node:assert/strict";

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
} from "../src/index.js";

function makeConditionRecord() {
  return {
    condition_id: "VITA_CTRL_003",
    study_family_id: "gill_2022",
    accession_bundle: "GSE165180",
    phase_layer: "maturation_phase_bulk_plus_abstention",
    primary_evidence_class: "observed_temporal",
    supporting_evidence_classes: ["bulk_proxy_support"],
    age_signal_score: 0.83,
    age_signal_status: "strong_positive",
    identity_pressure_level: "low",
    identity_status: "bounded_support",
    risk_pressure_level: "low",
    risk_status: "bounded_support",
    active_negative_family_ids: [],
    negative_family_roles: [],
    negative_family_tiers: [],
    condition_summary:
      "Gill successful maturation branch with real later-phase timing and relatively favorable proxy identity profile.",
    source_trace: {
      source_kind: "study_specific_rule",
      derived_from: [
        "/abs/compiler-rules/gill_2022-v0.json",
        "/abs/controller-benchmark-study-corpus-v0.csv",
      ],
      notes: ["Compiled from a study-specific rule pack."],
    },
    provenance: {
      reviewer: "Codex",
      reviewed_on: "2026-04-02",
      status: "draft",
      benchmark_links: [],
    },
  };
}

function makeCompileReceipt() {
  return {
    artifact_name: "controller-benchmark-condition-record-compile-receipt-v0",
    compiled_on: "2026-04-02T15:58:03.657071+00:00",
    script_path: "/abs/controller_benchmark_compile_condition_records.py",
    inputs: {
      study_corpus: "/abs/controller-benchmark-study-corpus-v0.csv",
      negative_families: "/abs/controller-benchmark-negative-family-registry-v0.json",
      conditions: "/abs/controller-benchmark-condition-fixture-v0.jsonl",
      compiler_rules_dir: "/abs/compiler-rules",
    },
    outputs: {
      condition_records: "/abs/controller-benchmark-condition-records-v0.jsonl",
      receipt: "/abs/controller-benchmark-condition-record-compile-receipt-v0.json",
      coverage_trust_receipt: "/abs/controller-benchmark-compiler-coverage-trust-receipt-v0.json",
    },
    condition_fixture_count: 8,
    compiled_condition_record_count: 8,
    source_kind_counts: {
      study_specific_rule: 8,
    },
    claim:
      "This compile step preserves source trace and provenance for benchmarked conditions.",
  };
}

function makeBenchmarkShellReceipt() {
  return {
    artifact_name: "controller-benchmark-shell-receipt-v0",
    executed_on: "2026-04-02T15:58:03.726593+00:00",
    script_path: "/abs/controller_benchmark_phase_stratified_benchmark_runner.py",
    inputs: {
      study_corpus: "/abs/controller-benchmark-study-corpus-v0.csv",
      negative_families: "/abs/controller-benchmark-negative-family-registry-v0.json",
      condition_records: "/abs/controller-benchmark-condition-records-v0.jsonl",
      compile_receipt: "/abs/controller-benchmark-condition-record-compile-receipt-v0.json",
    },
    outputs: {
      age_only_output: "/abs/controller-benchmark-age-only-baseline-outputs-v0.csv",
      controller_output: "/abs/controller-benchmark-controller-outputs-v0.csv",
      receipt: "/abs/controller-benchmark-shell-receipt-v0.json",
    },
    condition_count: 8,
    source_kind_counts: {
      study_specific_rule: 8,
    },
    summary: {
      condition_count: 8,
      baseline_output_counts: {
        promote: 7,
        downgrade: 1,
      },
      controller_output_counts: {
        promote: 1,
        downgrade: 3,
        abstain: 1,
        hazard_blocked: 2,
        insufficient_evidence: 1,
      },
      baseline_promoted_negative_conditions: [
        "VITA_CTRL_002",
      ],
      controller_promoted_negative_conditions: [],
      controller_hazard_blocked_conditions: [
        "VITA_CTRL_002",
      ],
      shell_claim:
        "This shell demonstrates executable benchmark structure and fail-closed logic.",
    },
  };
}

function makeCoverageTrustReceipt() {
  return {
    artifact_name: "controller-benchmark-compiler-coverage-trust-receipt-v0",
    generated_on: "2026-04-02T15:58:03.657407+00:00",
    script_path: "/abs/controller_benchmark_compile_condition_records.py",
    inputs: {
      study_corpus: "/abs/controller-benchmark-study-corpus-v0.csv",
      negative_families: "/abs/controller-benchmark-negative-family-registry-v0.json",
      conditions: "/abs/controller-benchmark-condition-fixture-v0.jsonl",
      compiler_rules_dir: "/abs/compiler-rules",
    },
    outputs: {
      condition_records: "/abs/controller-benchmark-condition-records-v0.jsonl",
      coverage_trust_receipt: "/abs/controller-benchmark-compiler-coverage-trust-receipt-v0.json",
    },
    condition_count: 8,
    source_kind_counts: {
      study_specific_rule: 8,
    },
    rule_backed_condition_count: 8,
    fixture_backed_condition_count: 0,
    rule_backed_condition_ids: ["VITA_CTRL_003"],
    fixture_backed_condition_ids: [],
    common_bounded_manual_judgment_fields: [
      "phase_layer",
    ],
    common_derived_fields: [
      "primary_evidence_class",
    ],
    common_matrix_extracted_fields: [],
    trust_boundary_claim:
      "All benchmark condition records now preserve explicit source trace.",
    coverage_verdict: "all_live_conditions_rule_backed",
    condition_rows: [
      {
        condition_id: "VITA_CTRL_003",
        study_family_id: "gill_2022",
        source_kind: "study_specific_rule",
        trust_status: "rule_backed_with_bounded_manual_judgment",
        traceable_support: {
          study_family_id: "gill_2022",
          accession_bundle: "GSE165180",
          derived_from: ["/abs/compiler-rules/gill_2022-v0.json"],
        },
        bounded_manual_judgment_fields: ["phase_layer"],
        derived_fields: ["primary_evidence_class"],
        matrix_extracted_fields: [],
        compiler_trust_notes: [
          "This condition is now carried by a dedicated study-specific rule pack rather than the global fixture.",
        ],
        condition_summary: "Gill successful maturation branch.",
      },
    ],
  };
}

test("schema exports are available", () => {
  assert.equal(CONDITION_RECORD_SCHEMA.title, "Controller Benchmark Condition Record");
  assert.equal(
    CONDITION_RECORD_COMPILE_RECEIPT_SCHEMA.title,
    "Condition Record Compile Receipt",
  );
  assert.equal(BENCHMARK_SHELL_RECEIPT_SCHEMA.title, "Benchmark Shell Receipt");
  assert.equal(
    COMPILER_COVERAGE_TRUST_RECEIPT_SCHEMA.title,
    "Compiler Coverage And Trust Receipt",
  );
});

test("schema registry can list and fetch schemas", () => {
  assert.deepEqual(listSchemas(), [
    "conditionRecord",
    "conditionRecordCompileReceipt",
    "benchmarkShellReceipt",
    "compilerCoverageTrustReceipt",
  ]);
  assert.equal(getSchema("conditionRecord").$id.includes("condition-record"), true);
});

test("condition record validator accepts a valid record", () => {
  const result = validateConditionRecord(makeConditionRecord());
  assert.equal(result.valid, true);
  assert.deepEqual(result.errors, []);
});

test("condition record validator catches an invalid enum", () => {
  const record = makeConditionRecord();
  record.primary_evidence_class = "retina_only";

  const result = validateConditionRecord(record);
  assert.equal(result.valid, false);
  assert.match(result.errors[0], /primary_evidence_class/);
});

test("condition record validator rejects non-age statuses for age signal", () => {
  const record = makeConditionRecord();
  record.age_signal_status = "bounded_support";

  const result = validateConditionRecord(record);
  assert.equal(result.valid, false);
  assert.match(result.errors[0], /age_signal_status/);
});

test("compile receipt validator accepts a valid receipt", () => {
  const result = validateConditionRecordCompileReceipt(makeCompileReceipt());
  assert.equal(result.valid, true);
});

test("benchmark shell receipt validator accepts a valid receipt", () => {
  const result = validateBenchmarkShellReceipt(makeBenchmarkShellReceipt());
  assert.equal(result.valid, true);
});

test("compiler coverage trust validator accepts a valid receipt", () => {
  const result = validateCompilerCoverageTrustReceipt(makeCoverageTrustReceipt());
  assert.equal(result.valid, true);
});
