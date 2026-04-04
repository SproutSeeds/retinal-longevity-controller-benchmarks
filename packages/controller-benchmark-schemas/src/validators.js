export const PHASE_LAYERS = Object.freeze([
  "initiation_phase_heterogeneity",
  "maturation_phase_bulk_plus_abstention",
  "hazard_stop_rule_negative_family",
]);

export const EVIDENCE_CLASSES = Object.freeze([
  "observed_temporal",
  "single_cell_snapshot_heterogeneity",
  "pseudotime_support",
  "bulk_proxy_support",
  "hazard_outcome_support",
  "opponent_calibration_support",
]);

export const AGE_SIGNAL_STATUSES = Object.freeze([
  "strong_positive",
  "moderate_positive",
  "weak_positive",
  "not_earned",
]);

export const PRESSURE_LEVELS = Object.freeze([
  "low",
  "moderate",
  "high",
  "unresolved",
]);

export const PRESSURE_STATUSES = Object.freeze([
  "bounded_support",
  "pressured",
  "blocked_pressure",
  "unresolved",
]);

export const SOURCE_KINDS = Object.freeze([
  "study_specific_rule",
  "study_specific_rule_with_matrix_age_override",
  "study_specific_rule_with_matrix_field_overrides",
  "frozen_fixture",
  "curated_manual",
  "accession_derived",
  "mixed",
]);

const PROVENANCE_STATUSES = new Set(["draft", "reviewed", "accepted", "superseded"]);

function makeResult(errors) {
  return {
    valid: errors.length === 0,
    errors,
  };
}

function isObject(value) {
  return value !== null && typeof value === "object" && !Array.isArray(value);
}

function pushError(errors, path, message) {
  errors.push(`${path}: ${message}`);
}

function expectObject(value, path, errors) {
  if (!isObject(value)) {
    pushError(errors, path, "expected object");
    return false;
  }
  return true;
}

function expectString(value, path, errors) {
  if (typeof value !== "string" || value.trim() === "") {
    pushError(errors, path, "expected non-empty string");
    return false;
  }
  return true;
}

function expectNumber(value, path, errors) {
  if (typeof value !== "number" || Number.isNaN(value) || !Number.isFinite(value)) {
    pushError(errors, path, "expected finite number");
    return false;
  }
  return true;
}

function expectArray(value, path, errors) {
  if (!Array.isArray(value)) {
    pushError(errors, path, "expected array");
    return false;
  }
  return true;
}

function expectEnum(value, allowed, path, errors) {
  if (typeof value !== "string" || !allowed.includes(value)) {
    pushError(errors, path, `expected one of: ${allowed.join(", ")}`);
    return false;
  }
  return true;
}

function expectStringArray(value, path, errors) {
  if (!expectArray(value, path, errors)) {
    return false;
  }
  value.forEach((item, index) => {
    expectString(item, `${path}[${index}]`, errors);
  });
  return true;
}

function expectNumberMap(value, path, errors) {
  if (!expectObject(value, path, errors)) {
    return false;
  }
  for (const [key, item] of Object.entries(value)) {
    expectNumber(item, `${path}.${key}`, errors);
  }
  return true;
}

function validateSourceTrace(value, path, errors) {
  if (!expectObject(value, path, errors)) {
    return;
  }
  expectEnum(value.source_kind, SOURCE_KINDS, `${path}.source_kind`, errors);
  expectStringArray(value.derived_from, `${path}.derived_from`, errors);
  if (value.notes !== undefined) {
    expectStringArray(value.notes, `${path}.notes`, errors);
  }
}

function validateProvenance(value, path, errors) {
  if (!expectObject(value, path, errors)) {
    return;
  }
  expectString(value.reviewer, `${path}.reviewer`, errors);
  if (
    typeof value.status !== "string" ||
    !PROVENANCE_STATUSES.has(value.status)
  ) {
    pushError(
      errors,
      `${path}.status`,
      "expected one of: draft, reviewed, accepted, superseded",
    );
  }
  if (value.reviewed_on !== undefined) {
    expectString(value.reviewed_on, `${path}.reviewed_on`, errors);
  }
  if (value.benchmark_links !== undefined) {
    expectStringArray(value.benchmark_links, `${path}.benchmark_links`, errors);
  }
}

export function validateConditionRecord(value) {
  const errors = [];
  if (!expectObject(value, "conditionRecord", errors)) {
    return makeResult(errors);
  }

  expectString(value.condition_id, "conditionRecord.condition_id", errors);
  expectString(value.study_family_id, "conditionRecord.study_family_id", errors);
  expectString(value.accession_bundle, "conditionRecord.accession_bundle", errors);
  expectEnum(value.phase_layer, PHASE_LAYERS, "conditionRecord.phase_layer", errors);
  expectEnum(
    value.primary_evidence_class,
    EVIDENCE_CLASSES,
    "conditionRecord.primary_evidence_class",
    errors,
  );
  if (expectArray(value.supporting_evidence_classes, "conditionRecord.supporting_evidence_classes", errors)) {
    value.supporting_evidence_classes.forEach((item, index) => {
      expectEnum(
        item,
        EVIDENCE_CLASSES,
        `conditionRecord.supporting_evidence_classes[${index}]`,
        errors,
      );
    });
  }

  expectNumber(value.age_signal_score, "conditionRecord.age_signal_score", errors);
  expectEnum(
    value.age_signal_status,
    AGE_SIGNAL_STATUSES,
    "conditionRecord.age_signal_status",
    errors,
  );
  expectEnum(
    value.identity_pressure_level,
    PRESSURE_LEVELS,
    "conditionRecord.identity_pressure_level",
    errors,
  );
  expectEnum(
    value.identity_status,
    PRESSURE_STATUSES,
    "conditionRecord.identity_status",
    errors,
  );
  expectEnum(
    value.risk_pressure_level,
    PRESSURE_LEVELS,
    "conditionRecord.risk_pressure_level",
    errors,
  );
  expectEnum(
    value.risk_status,
    PRESSURE_STATUSES,
    "conditionRecord.risk_status",
    errors,
  );

  expectStringArray(
    value.active_negative_family_ids,
    "conditionRecord.active_negative_family_ids",
    errors,
  );
  expectStringArray(
    value.negative_family_roles ?? [],
    "conditionRecord.negative_family_roles",
    errors,
  );
  expectStringArray(
    value.negative_family_tiers ?? [],
    "conditionRecord.negative_family_tiers",
    errors,
  );
  expectString(value.condition_summary, "conditionRecord.condition_summary", errors);
  validateSourceTrace(value.source_trace, "conditionRecord.source_trace", errors);
  validateProvenance(value.provenance, "conditionRecord.provenance", errors);

  return makeResult(errors);
}

export function validateConditionRecordCompileReceipt(value) {
  const errors = [];
  if (!expectObject(value, "conditionRecordCompileReceipt", errors)) {
    return makeResult(errors);
  }

  expectString(value.artifact_name, "conditionRecordCompileReceipt.artifact_name", errors);
  expectString(value.compiled_on, "conditionRecordCompileReceipt.compiled_on", errors);
  expectString(value.script_path, "conditionRecordCompileReceipt.script_path", errors);

  if (expectObject(value.inputs, "conditionRecordCompileReceipt.inputs", errors)) {
    expectString(value.inputs.study_corpus, "conditionRecordCompileReceipt.inputs.study_corpus", errors);
    expectString(value.inputs.negative_families, "conditionRecordCompileReceipt.inputs.negative_families", errors);
    expectString(value.inputs.conditions, "conditionRecordCompileReceipt.inputs.conditions", errors);
    expectString(value.inputs.compiler_rules_dir, "conditionRecordCompileReceipt.inputs.compiler_rules_dir", errors);
    if (value.inputs.matrix_field_layers_dir !== undefined) {
      expectString(
        value.inputs.matrix_field_layers_dir,
        "conditionRecordCompileReceipt.inputs.matrix_field_layers_dir",
        errors,
      );
    }
  }

  if (expectObject(value.outputs, "conditionRecordCompileReceipt.outputs", errors)) {
    expectString(value.outputs.condition_records, "conditionRecordCompileReceipt.outputs.condition_records", errors);
    expectString(value.outputs.receipt, "conditionRecordCompileReceipt.outputs.receipt", errors);
    expectString(
      value.outputs.coverage_trust_receipt,
      "conditionRecordCompileReceipt.outputs.coverage_trust_receipt",
      errors,
    );
  }

  expectNumber(
    value.condition_fixture_count,
    "conditionRecordCompileReceipt.condition_fixture_count",
    errors,
  );
  expectNumber(
    value.compiled_condition_record_count,
    "conditionRecordCompileReceipt.compiled_condition_record_count",
    errors,
  );
  expectNumberMap(
    value.source_kind_counts,
    "conditionRecordCompileReceipt.source_kind_counts",
    errors,
  );
  if (value.matrix_derived_condition_count !== undefined) {
    expectNumber(
      value.matrix_derived_condition_count,
      "conditionRecordCompileReceipt.matrix_derived_condition_count",
      errors,
    );
  }
  if (value.matrix_derived_condition_ids !== undefined) {
    expectStringArray(
      value.matrix_derived_condition_ids,
      "conditionRecordCompileReceipt.matrix_derived_condition_ids",
      errors,
    );
  }
  expectString(value.claim, "conditionRecordCompileReceipt.claim", errors);

  return makeResult(errors);
}

export function validateBenchmarkShellReceipt(value) {
  const errors = [];
  if (!expectObject(value, "benchmarkShellReceipt", errors)) {
    return makeResult(errors);
  }

  expectString(value.artifact_name, "benchmarkShellReceipt.artifact_name", errors);
  expectString(value.executed_on, "benchmarkShellReceipt.executed_on", errors);
  expectString(value.script_path, "benchmarkShellReceipt.script_path", errors);

  if (expectObject(value.inputs, "benchmarkShellReceipt.inputs", errors)) {
    expectString(value.inputs.study_corpus, "benchmarkShellReceipt.inputs.study_corpus", errors);
    expectString(value.inputs.negative_families, "benchmarkShellReceipt.inputs.negative_families", errors);
    expectString(value.inputs.condition_records, "benchmarkShellReceipt.inputs.condition_records", errors);
    expectString(value.inputs.compile_receipt, "benchmarkShellReceipt.inputs.compile_receipt", errors);
  }

  if (expectObject(value.outputs, "benchmarkShellReceipt.outputs", errors)) {
    expectString(value.outputs.age_only_output, "benchmarkShellReceipt.outputs.age_only_output", errors);
    expectString(value.outputs.controller_output, "benchmarkShellReceipt.outputs.controller_output", errors);
    expectString(value.outputs.receipt, "benchmarkShellReceipt.outputs.receipt", errors);
  }

  expectNumber(value.condition_count, "benchmarkShellReceipt.condition_count", errors);
  expectNumberMap(value.source_kind_counts, "benchmarkShellReceipt.source_kind_counts", errors);

  if (expectObject(value.summary, "benchmarkShellReceipt.summary", errors)) {
    expectNumber(value.summary.condition_count, "benchmarkShellReceipt.summary.condition_count", errors);
    expectNumberMap(
      value.summary.baseline_output_counts,
      "benchmarkShellReceipt.summary.baseline_output_counts",
      errors,
    );
    expectNumberMap(
      value.summary.controller_output_counts,
      "benchmarkShellReceipt.summary.controller_output_counts",
      errors,
    );
    expectStringArray(
      value.summary.baseline_promoted_negative_conditions,
      "benchmarkShellReceipt.summary.baseline_promoted_negative_conditions",
      errors,
    );
    expectStringArray(
      value.summary.controller_promoted_negative_conditions,
      "benchmarkShellReceipt.summary.controller_promoted_negative_conditions",
      errors,
    );
    expectStringArray(
      value.summary.controller_hazard_blocked_conditions,
      "benchmarkShellReceipt.summary.controller_hazard_blocked_conditions",
      errors,
    );
    expectString(value.summary.shell_claim, "benchmarkShellReceipt.summary.shell_claim", errors);
  }

  return makeResult(errors);
}

export function validateCompilerCoverageTrustReceipt(value) {
  const errors = [];
  if (!expectObject(value, "compilerCoverageTrustReceipt", errors)) {
    return makeResult(errors);
  }

  expectString(value.artifact_name, "compilerCoverageTrustReceipt.artifact_name", errors);
  expectString(value.generated_on, "compilerCoverageTrustReceipt.generated_on", errors);
  expectString(value.script_path, "compilerCoverageTrustReceipt.script_path", errors);

  if (expectObject(value.inputs, "compilerCoverageTrustReceipt.inputs", errors)) {
    expectString(value.inputs.study_corpus, "compilerCoverageTrustReceipt.inputs.study_corpus", errors);
    expectString(value.inputs.negative_families, "compilerCoverageTrustReceipt.inputs.negative_families", errors);
    expectString(value.inputs.conditions, "compilerCoverageTrustReceipt.inputs.conditions", errors);
    expectString(value.inputs.compiler_rules_dir, "compilerCoverageTrustReceipt.inputs.compiler_rules_dir", errors);
  }

  if (expectObject(value.outputs, "compilerCoverageTrustReceipt.outputs", errors)) {
    expectString(value.outputs.condition_records, "compilerCoverageTrustReceipt.outputs.condition_records", errors);
    expectString(
      value.outputs.coverage_trust_receipt,
      "compilerCoverageTrustReceipt.outputs.coverage_trust_receipt",
      errors,
    );
  }

  expectNumber(value.condition_count, "compilerCoverageTrustReceipt.condition_count", errors);
  expectNumberMap(
    value.source_kind_counts,
    "compilerCoverageTrustReceipt.source_kind_counts",
    errors,
  );
  expectNumber(
    value.rule_backed_condition_count,
    "compilerCoverageTrustReceipt.rule_backed_condition_count",
    errors,
  );
  expectNumber(
    value.fixture_backed_condition_count,
    "compilerCoverageTrustReceipt.fixture_backed_condition_count",
    errors,
  );
  expectStringArray(
    value.rule_backed_condition_ids,
    "compilerCoverageTrustReceipt.rule_backed_condition_ids",
    errors,
  );
  expectStringArray(
    value.fixture_backed_condition_ids,
    "compilerCoverageTrustReceipt.fixture_backed_condition_ids",
    errors,
  );
  expectStringArray(
    value.common_bounded_manual_judgment_fields,
    "compilerCoverageTrustReceipt.common_bounded_manual_judgment_fields",
    errors,
  );
  expectStringArray(
    value.common_derived_fields,
    "compilerCoverageTrustReceipt.common_derived_fields",
    errors,
  );
  expectStringArray(
    value.common_matrix_extracted_fields,
    "compilerCoverageTrustReceipt.common_matrix_extracted_fields",
    errors,
  );
  if (value.common_matrix_support_fields !== undefined) {
    expectStringArray(
      value.common_matrix_support_fields,
      "compilerCoverageTrustReceipt.common_matrix_support_fields",
      errors,
    );
  }
  expectString(
    value.trust_boundary_claim,
    "compilerCoverageTrustReceipt.trust_boundary_claim",
    errors,
  );
  expectString(
    value.coverage_verdict,
    "compilerCoverageTrustReceipt.coverage_verdict",
    errors,
  );

  if (expectArray(value.condition_rows, "compilerCoverageTrustReceipt.condition_rows", errors)) {
    value.condition_rows.forEach((row, index) => {
      const path = `compilerCoverageTrustReceipt.condition_rows[${index}]`;
      if (!expectObject(row, path, errors)) {
        return;
      }
      expectString(row.condition_id, `${path}.condition_id`, errors);
      expectString(row.study_family_id, `${path}.study_family_id`, errors);
      expectEnum(row.source_kind, SOURCE_KINDS, `${path}.source_kind`, errors);
      expectString(row.trust_status, `${path}.trust_status`, errors);
      if (expectObject(row.traceable_support, `${path}.traceable_support`, errors)) {
        expectString(row.traceable_support.study_family_id, `${path}.traceable_support.study_family_id`, errors);
        expectString(row.traceable_support.accession_bundle, `${path}.traceable_support.accession_bundle`, errors);
        expectStringArray(row.traceable_support.derived_from, `${path}.traceable_support.derived_from`, errors);
      }
      expectStringArray(row.bounded_manual_judgment_fields, `${path}.bounded_manual_judgment_fields`, errors);
      expectStringArray(row.derived_fields, `${path}.derived_fields`, errors);
      expectStringArray(row.matrix_extracted_fields, `${path}.matrix_extracted_fields`, errors);
      if (row.matrix_support_fields !== undefined) {
        expectStringArray(row.matrix_support_fields, `${path}.matrix_support_fields`, errors);
      }
      expectStringArray(row.compiler_trust_notes, `${path}.compiler_trust_notes`, errors);
      expectString(row.condition_summary, `${path}.condition_summary`, errors);
    });
  }

  return makeResult(errors);
}
