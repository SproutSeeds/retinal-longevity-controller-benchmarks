export const BASELINE_OUTPUTS = Object.freeze([
  "promote",
  "downgrade",
]);

export const CONTROLLER_OUTPUTS = Object.freeze([
  "promote",
  "downgrade",
  "abstain",
  "hazard_blocked",
  "insufficient_evidence",
]);

export const PASSIVE_RECOMMENDATION_POSTURES = Object.freeze([
  "candidate_scaffold_only",
  "deferred_abstention",
  "deferred_insufficient_evidence",
  "boundary_downgraded",
  "preserve_block",
  "reference_only_boundary",
]);

function assertArray(value, label) {
  if (!Array.isArray(value)) {
    throw new TypeError(`${label} must be an array`);
  }
}

function normalizeSelector(selector) {
  if (typeof selector === "function") {
    return selector;
  }

  if (typeof selector === "string" && selector.length > 0) {
    return (item) => item?.[selector];
  }

  throw new TypeError("selector must be a function or non-empty string");
}

function normalizeDelimitedIds(value) {
  if (Array.isArray(value)) {
    return value.filter(Boolean);
  }

  if (typeof value !== "string" || value.trim() === "") {
    return [];
  }

  return value
    .split(/[;,]/)
    .map((item) => item.trim())
    .filter(Boolean);
}

function makeCountsObject(counts) {
  return Object.freeze(Object.fromEntries(
    Object.entries(counts).sort(([left], [right]) => left.localeCompare(right)),
  ));
}

export function countBy(items, selector) {
  assertArray(items, "items");
  const pick = normalizeSelector(selector);
  const counts = {};

  for (const item of items) {
    const key = pick(item);
    const normalizedKey = String(key ?? "undefined");
    counts[normalizedKey] = (counts[normalizedKey] ?? 0) + 1;
  }

  return makeCountsObject(counts);
}

export function indexConditionRecords(records) {
  assertArray(records, "records");
  return Object.freeze(
    Object.fromEntries(records.map((record) => [record.condition_id, record])),
  );
}

export function groupConditionRecordsByPhase(records) {
  assertArray(records, "records");
  const groups = {};

  for (const record of records) {
    const key = record.phase_layer ?? "unknown";
    if (!groups[key]) {
      groups[key] = [];
    }
    groups[key].push(record);
  }

  return Object.freeze(groups);
}

export function groupConditionRecordsByStudyFamily(records) {
  assertArray(records, "records");
  const groups = {};

  for (const record of records) {
    const key = record.study_family_id ?? "unknown";
    if (!groups[key]) {
      groups[key] = [];
    }
    groups[key].push(record);
  }

  return Object.freeze(groups);
}

export function listNegativePressureConditions(records) {
  assertArray(records, "records");
  return records.filter((record) => {
    const ids = normalizeDelimitedIds(record.active_negative_family_ids);
    return ids.length > 0;
  });
}

export function compareOutputs(ageOnlyRows, controllerRows) {
  assertArray(ageOnlyRows, "ageOnlyRows");
  assertArray(controllerRows, "controllerRows");

  const controllerById = new Map(
    controllerRows.map((row) => [row.condition_id, row]),
  );

  const transitions = {};
  const baselinePromotedNegativeConditions = [];
  const controllerPromotedNegativeConditions = [];
  const controllerHazardBlockedConditions = [];

  for (const baselineRow of ageOnlyRows) {
    const conditionId = baselineRow.condition_id;
    const controllerRow = controllerById.get(conditionId);

    if (!controllerRow) {
      continue;
    }

    const baselineOutput = baselineRow.baseline_output ?? "undefined";
    const controllerOutput = controllerRow.controller_output ?? "undefined";
    const transitionKey = `${baselineOutput}->${controllerOutput}`;
    transitions[transitionKey] = (transitions[transitionKey] ?? 0) + 1;

    const negativeIds = [
      ...normalizeDelimitedIds(baselineRow.active_negative_family_ids),
      ...normalizeDelimitedIds(controllerRow.active_negative_family_ids),
    ];

    if (baselineOutput === "promote" && negativeIds.length > 0) {
      baselinePromotedNegativeConditions.push(conditionId);
    }

    if (controllerOutput === "promote" && negativeIds.length > 0) {
      controllerPromotedNegativeConditions.push(conditionId);
    }

    if (controllerOutput === "hazard_blocked") {
      controllerHazardBlockedConditions.push(conditionId);
    }
  }

  return {
    condition_count: ageOnlyRows.length,
    baseline_output_counts: countBy(ageOnlyRows, "baseline_output"),
    controller_output_counts: countBy(controllerRows, "controller_output"),
    transition_counts: makeCountsObject(transitions),
    baseline_promoted_negative_conditions: Object.freeze(
      baselinePromotedNegativeConditions.slice().sort(),
    ),
    controller_promoted_negative_conditions: Object.freeze(
      controllerPromotedNegativeConditions.slice().sort(),
    ),
    controller_hazard_blocked_conditions: Object.freeze(
      controllerHazardBlockedConditions.slice().sort(),
    ),
    fail_closed:
      controllerPromotedNegativeConditions.length === 0 &&
      controllerHazardBlockedConditions.length > 0,
  };
}

export function summarizeCoverageTrust(coverageTrustReceipt) {
  if (!coverageTrustReceipt || typeof coverageTrustReceipt !== "object") {
    throw new TypeError("coverageTrustReceipt must be an object");
  }

  const conditionRows = Array.isArray(coverageTrustReceipt.condition_rows)
    ? coverageTrustReceipt.condition_rows
    : [];

  const countFlattenedField = (fieldName) =>
    countBy(
      conditionRows.flatMap((row) =>
        Array.isArray(row[fieldName]) ? row[fieldName] : [],
      ),
      (value) => value,
    );

  return {
    condition_count: coverageTrustReceipt.condition_count ?? 0,
    source_kind_counts: Object.freeze({
      ...(coverageTrustReceipt.source_kind_counts ?? {}),
    }),
    rule_backed_condition_count:
      coverageTrustReceipt.rule_backed_condition_count ?? 0,
    fixture_backed_condition_count:
      coverageTrustReceipt.fixture_backed_condition_count ?? 0,
    coverage_verdict: coverageTrustReceipt.coverage_verdict ?? "unknown",
    trust_status_counts: countBy(conditionRows, "trust_status"),
    bounded_manual_judgment_field_counts: countFlattenedField(
      "bounded_manual_judgment_fields",
    ),
    derived_field_counts: countFlattenedField("derived_fields"),
    matrix_extracted_field_counts: countFlattenedField(
      "matrix_extracted_fields",
    ),
  };
}

export function summarizeShellReceipt(benchmarkShellReceipt) {
  if (!benchmarkShellReceipt || typeof benchmarkShellReceipt !== "object") {
    throw new TypeError("benchmarkShellReceipt must be an object");
  }

  const summary = benchmarkShellReceipt.summary ?? {};
  const baselinePromotedNegativeConditions =
    summary.baseline_promoted_negative_conditions ?? [];
  const controllerPromotedNegativeConditions =
    summary.controller_promoted_negative_conditions ?? [];
  const controllerHazardBlockedConditions =
    summary.controller_hazard_blocked_conditions ?? [];

  return {
    condition_count: benchmarkShellReceipt.condition_count ?? 0,
    source_kind_counts: Object.freeze({
      ...(benchmarkShellReceipt.source_kind_counts ?? {}),
    }),
    baseline_output_counts: Object.freeze({
      ...(summary.baseline_output_counts ?? {}),
    }),
    controller_output_counts: Object.freeze({
      ...(summary.controller_output_counts ?? {}),
    }),
    baseline_promoted_negative_count: baselinePromotedNegativeConditions.length,
    controller_promoted_negative_count:
      controllerPromotedNegativeConditions.length,
    controller_hazard_blocked_count:
      controllerHazardBlockedConditions.length,
    fail_closed:
      controllerPromotedNegativeConditions.length === 0 &&
      controllerHazardBlockedConditions.length > 0,
    shell_claim: summary.shell_claim ?? "",
  };
}

export function summarizeContradictionLedger(contradictionLedger) {
  if (!contradictionLedger || typeof contradictionLedger !== "object") {
    throw new TypeError("contradictionLedger must be an object");
  }

  const liveContradictions = Array.isArray(contradictionLedger.live_contradictions)
    ? contradictionLedger.live_contradictions
    : [];
  const armedNotTriggeredClasses = Array.isArray(
    contradictionLedger.armed_not_triggered_classes,
  )
    ? contradictionLedger.armed_not_triggered_classes
    : [];

  return {
    live_contradiction_count: liveContradictions.length,
    contradicted_condition_count: new Set(
      liveContradictions.map((row) => row.condition_id),
    ).size,
    contradiction_class_counts: countBy(liveContradictions, "contradiction_class_id"),
    kernel_resolution_counts: countBy(liveContradictions, "kernel_resolution"),
    armed_not_triggered_class_count: armedNotTriggeredClasses.length,
    armed_not_triggered_class_ids: Object.freeze(
      armedNotTriggeredClasses
        .map((row) => row.contradiction_class_id)
        .filter(Boolean)
        .sort(),
    ),
  };
}

export function summarizePassiveRecommendationScaffold(
  passiveRecommendationScaffold,
  passiveRecommendationReceipt = null,
) {
  if (
    !passiveRecommendationScaffold ||
    typeof passiveRecommendationScaffold !== "object"
  ) {
    throw new TypeError("passiveRecommendationScaffold must be an object");
  }

  const protocolObjects = Array.isArray(
    passiveRecommendationScaffold.protocol_objects,
  )
    ? passiveRecommendationScaffold.protocol_objects
    : [];

  const contradictionCitedProtocolObjectCount = protocolObjects.filter(
    (row) =>
      Array.isArray(row?.contradiction_state?.live_contradiction_ids) &&
      row.contradiction_state.live_contradiction_ids.length > 0,
  ).length;

  const summary = {
    protocol_object_count: protocolObjects.length,
    live_recommendation_active_count: protocolObjects.filter(
      (row) => row.live_recommendation_active === true,
    ).length,
    passive_posture_counts: countBy(protocolObjects, "passive_posture"),
    controller_output_counts: countBy(protocolObjects, "controller_output"),
    contradiction_cited_protocol_object_count:
      contradictionCitedProtocolObjectCount,
    candidate_protocol_object_count: protocolObjects.filter(
      (row) => row.passive_posture === "candidate_scaffold_only",
    ).length,
    preserve_block_protocol_object_count: protocolObjects.filter(
      (row) => row.passive_posture === "preserve_block",
    ).length,
    deferred_protocol_object_count: protocolObjects.filter((row) =>
      [
        "deferred_abstention",
        "deferred_insufficient_evidence",
      ].includes(row.passive_posture),
    ).length,
    dormant_gate_state:
      passiveRecommendationScaffold.global_activation_gate?.gate_state ??
      "unknown",
  };

  if (
    passiveRecommendationReceipt &&
    typeof passiveRecommendationReceipt === "object"
  ) {
    return {
      ...summary,
      dormant_verdict: passiveRecommendationReceipt.dormant_verdict ?? "unknown",
      armed_watch_class_ids: Object.freeze(
        Array.isArray(passiveRecommendationReceipt.armed_watch_class_ids)
          ? passiveRecommendationReceipt.armed_watch_class_ids.slice().sort()
          : [],
      ),
    };
  }

  return summary;
}

export function summarizeCx004ValidationHandoff(
  cx004ValidationHandoff,
  cx004ValidationHandoffReceipt = null,
) {
  if (!cx004ValidationHandoff || typeof cx004ValidationHandoff !== "object") {
    throw new TypeError("cx004ValidationHandoff must be an object");
  }

  const summary = {
    handoff_id: cx004ValidationHandoff.handoff_id ?? "unknown",
    driver_contradiction_class_id:
      cx004ValidationHandoff.driver_contradiction_class_id ?? "unknown",
    pair_condition_ids: Object.freeze(
      Array.isArray(cx004ValidationHandoff?.target_pair?.condition_ids)
        ? cx004ValidationHandoff.target_pair.condition_ids.slice().sort()
        : [],
    ),
    pair_study_family_ids: Object.freeze(
      Array.isArray(cx004ValidationHandoff?.target_pair?.study_family_ids)
        ? cx004ValidationHandoff.target_pair.study_family_ids.slice().sort()
        : [],
    ),
    required_timepoint_count: Array.isArray(
      cx004ValidationHandoff?.minimal_validation_design?.minimum_timepoints,
    )
      ? cx004ValidationHandoff.minimal_validation_design.minimum_timepoints.length
      : 0,
    required_readout_count: Array.isArray(
      cx004ValidationHandoff?.exact_discriminating_readouts,
    )
      ? cx004ValidationHandoff.exact_discriminating_readouts.length
      : 0,
    required_assay_count: Array.isArray(
      cx004ValidationHandoff?.minimal_validation_design?.required_assays,
    )
      ? cx004ValidationHandoff.minimal_validation_design.required_assays.length
      : 0,
    optional_structural_identity_extension:
      cx004ValidationHandoff?.optional_structural_identity_extension?.status ??
      "unknown",
  };

  if (
    cx004ValidationHandoffReceipt &&
    typeof cx004ValidationHandoffReceipt === "object"
  ) {
    return {
      ...summary,
      handoff_verdict:
        cx004ValidationHandoffReceipt.handoff_verdict ?? "unknown",
      driver_contradiction_count:
        cx004ValidationHandoffReceipt.driver_contradiction_count ?? 0,
    };
  }

  return summary;
}

export function summarizeCx004ResolutionReviewGate(
  cx004ResolutionReviewContract,
  cx004ExampleResolutionReviewReceipt = null,
) {
  if (
    !cx004ResolutionReviewContract ||
    typeof cx004ResolutionReviewContract !== "object"
  ) {
    throw new TypeError("cx004ResolutionReviewContract must be an object");
  }

  const summary = {
    contract_id: cx004ResolutionReviewContract.contract_id ?? "unknown",
    review_dependency_id:
      cx004ResolutionReviewContract.review_dependency_id ?? "unknown",
    required_anchor_condition_count: Array.isArray(
      cx004ResolutionReviewContract.required_anchor_condition_ids,
    )
      ? cx004ResolutionReviewContract.required_anchor_condition_ids.length
      : 0,
    allowed_review_verdict_count: Array.isArray(
      cx004ResolutionReviewContract.allowed_review_verdicts,
    )
      ? cx004ResolutionReviewContract.allowed_review_verdicts.length
      : 0,
  };

  if (
    cx004ExampleResolutionReviewReceipt &&
    typeof cx004ExampleResolutionReviewReceipt === "object"
  ) {
    return {
      ...summary,
      example_review_verdict:
        cx004ExampleResolutionReviewReceipt.review_verdict ?? "unknown",
      example_pair_resolution_state:
        cx004ExampleResolutionReviewReceipt.pair_resolution_state ?? "unknown",
      example_review_dependency_satisfied:
        cx004ExampleResolutionReviewReceipt.review_dependency_satisfied ?? false,
      example_live_recommendation_activation_allowed:
        cx004ExampleResolutionReviewReceipt.live_recommendation_activation_allowed ??
        false,
      example_anchor_review_count: Array.isArray(
        cx004ExampleResolutionReviewReceipt.anchor_condition_reviews,
      )
        ? cx004ExampleResolutionReviewReceipt.anchor_condition_reviews.length
        : 0,
    };
  }

  return summary;
}

export function buildBenchmarkSnapshot({
  conditionRecords,
  coverageTrustReceipt,
  benchmarkShellReceipt,
  contradictionLedger,
  cx004ValidationHandoff,
  cx004ValidationHandoffReceipt,
  cx004ResolutionReviewContract,
  cx004ExampleInsufficientResolutionReviewReceipt,
  passiveRecommendationScaffold,
  passiveRecommendationReceipt,
  ageOnlyRows,
  controllerRows,
}) {
  assertArray(conditionRecords, "conditionRecords");

  const outputComparison =
    ageOnlyRows && controllerRows
      ? compareOutputs(ageOnlyRows, controllerRows)
      : null;

  return {
    condition_count: conditionRecords.length,
    phase_counts: countBy(conditionRecords, "phase_layer"),
    study_family_counts: countBy(conditionRecords, "study_family_id"),
    negative_pressure_condition_ids: Object.freeze(
      listNegativePressureConditions(conditionRecords)
        .map((record) => record.condition_id)
        .sort(),
    ),
    coverage: coverageTrustReceipt
      ? summarizeCoverageTrust(coverageTrustReceipt)
      : null,
    shell: benchmarkShellReceipt
      ? summarizeShellReceipt(benchmarkShellReceipt)
      : null,
    contradictions: contradictionLedger
      ? summarizeContradictionLedger(contradictionLedger)
      : null,
    validation_handoff: cx004ValidationHandoff
      ? summarizeCx004ValidationHandoff(
          cx004ValidationHandoff,
          cx004ValidationHandoffReceipt,
        )
      : null,
    resolution_review_gate: cx004ResolutionReviewContract
      ? summarizeCx004ResolutionReviewGate(
          cx004ResolutionReviewContract,
          cx004ExampleInsufficientResolutionReviewReceipt,
        )
      : null,
    recommendations: passiveRecommendationScaffold
      ? summarizePassiveRecommendationScaffold(
          passiveRecommendationScaffold,
          passiveRecommendationReceipt,
        )
      : null,
    outputs: outputComparison,
  };
}
