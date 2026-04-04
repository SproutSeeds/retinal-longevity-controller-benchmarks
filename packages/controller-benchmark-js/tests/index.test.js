import test from "node:test";
import assert from "node:assert/strict";

import {
  BASELINE_OUTPUTS,
  CONTROLLER_OUTPUTS,
  PASSIVE_RECOMMENDATION_POSTURES,
  buildBenchmarkSnapshot,
  compareOutputs,
  countBy,
  groupConditionRecordsByPhase,
  groupConditionRecordsByStudyFamily,
  indexConditionRecords,
  listNegativePressureConditions,
  summarizeCx004ValidationHandoff,
  summarizeContradictionLedger,
  summarizeCoverageTrust,
  summarizePassiveRecommendationScaffold,
  summarizeShellReceipt,
} from "../src/index.js";

import {
  loadLatestBundle,
  readAgeOnlyBaselineOutputRows,
  readControllerOutputRows,
} from "../../controller-benchmark-data/src/index.js";

const bundle = loadLatestBundle();
const ageOnlyRows = readAgeOnlyBaselineOutputRows();
const controllerRows = readControllerOutputRows();

test("output constants remain stable", () => {
  assert.deepEqual(BASELINE_OUTPUTS, ["promote", "downgrade"]);
  assert.deepEqual(CONTROLLER_OUTPUTS, [
    "promote",
    "downgrade",
    "abstain",
    "hazard_blocked",
    "insufficient_evidence",
  ]);
  assert.deepEqual(PASSIVE_RECOMMENDATION_POSTURES, [
    "candidate_scaffold_only",
    "deferred_abstention",
    "deferred_insufficient_evidence",
    "boundary_downgraded",
    "preserve_block",
    "reference_only_boundary",
  ]);
});

test("countBy can count object fields", () => {
  assert.deepEqual(countBy(bundle.conditionRecords, "study_family_id"), {
    gill_2022: 3,
    human_full_reprog_d14: 1,
    ohnishi_2014: 1,
    olova_ohnuki: 1,
    roux_2022_sc: 1,
    sarkar_2020: 1,
  });
});

test("condition records can be indexed and grouped", () => {
  const index = indexConditionRecords(bundle.conditionRecords);
  const byPhase = groupConditionRecordsByPhase(bundle.conditionRecords);
  const byStudy = groupConditionRecordsByStudyFamily(bundle.conditionRecords);

  assert.equal(index.VITA_CTRL_003.study_family_id, "gill_2022");
  assert.equal(byPhase.initiation_phase_heterogeneity.length, 3);
  assert.equal(byStudy.gill_2022.length, 3);
});

test("negative pressure conditions are surfaced", () => {
  const negativeConditions = listNegativePressureConditions(bundle.conditionRecords);
  assert.deepEqual(
    negativeConditions.map((record) => record.condition_id).sort(),
    ["VITA_CTRL_002", "VITA_CTRL_004", "VITA_CTRL_006", "VITA_CTRL_007"],
  );
});

test("coverage trust summary captures the main trust boundary", () => {
  const summary = summarizeCoverageTrust(bundle.coverageTrustReceipt);

  assert.equal(summary.condition_count, 8);
  assert.equal(summary.rule_backed_condition_count, 8);
  assert.equal(summary.fixture_backed_condition_count, 0);
  assert.equal(summary.coverage_verdict, "all_live_conditions_rule_backed");
});

test("shell summary preserves fail-closed interpretation", () => {
  const summary = summarizeShellReceipt(bundle.benchmarkShellReceipt);

  assert.equal(summary.condition_count, 8);
  assert.equal(summary.baseline_promoted_negative_count, 4);
  assert.equal(summary.controller_promoted_negative_count, 0);
  assert.equal(summary.controller_hazard_blocked_count, 2);
  assert.equal(summary.fail_closed, true);
});

test("contradiction summary preserves live disagreement counts", () => {
  const summary = summarizeContradictionLedger(bundle.contradictionLedger);

  assert.equal(summary.live_contradiction_count, 8);
  assert.equal(summary.contradicted_condition_count, 5);
  assert.equal(summary.contradiction_class_counts["CX-004"], 2);
  assert.equal(summary.contradiction_class_counts["CX-003"], 3);
  assert.equal(summary.kernel_resolution_counts.downgrade, 4);
  assert.equal(summary.kernel_resolution_counts.review_required, 2);
  assert.deepEqual(summary.armed_not_triggered_class_ids, ["CX-WATCH-002"]);
});

test("passive recommendation summary preserves dormant forward objects", () => {
  const summary = summarizePassiveRecommendationScaffold(
    bundle.passiveRecommendationScaffold,
    bundle.passiveRecommendationReceipt,
  );

  assert.equal(summary.protocol_object_count, 8);
  assert.equal(summary.live_recommendation_active_count, 0);
  assert.equal(summary.passive_posture_counts.candidate_scaffold_only, 1);
  assert.equal(summary.passive_posture_counts.preserve_block, 2);
  assert.equal(summary.passive_posture_counts.reference_only_boundary, 1);
  assert.equal(summary.contradiction_cited_protocol_object_count, 5);
  assert.deepEqual(summary.armed_watch_class_ids, ["CX-WATCH-002"]);
  assert.equal(
    summary.dormant_verdict,
    "passive_scaffolding_only_live_recommendation_dormant",
  );
});

test("cx004 validation handoff summary preserves the live pair object", () => {
  const summary = summarizeCx004ValidationHandoff(
    bundle.cx004ValidationHandoff,
    bundle.cx004ValidationHandoffReceipt,
  );

  assert.equal(summary.handoff_id, "CTRL-VITA-CX004-HANDOFF-V0-001");
  assert.equal(summary.driver_contradiction_class_id, "CX-004");
  assert.deepEqual(summary.pair_condition_ids, [
    "VITA_CTRL_003",
    "VITA_CTRL_005",
  ]);
  assert.equal(summary.required_timepoint_count, 9);
  assert.equal(summary.required_readout_count, 4);
  assert.equal(summary.handoff_verdict, "cx004_validation_handoff_frozen");
});

test("output comparison captures transition structure", () => {
  const comparison = compareOutputs(ageOnlyRows, controllerRows);

  assert.equal(comparison.condition_count, 8);
  assert.equal(comparison.baseline_output_counts.promote, 7);
  assert.equal(comparison.controller_output_counts.promote, 1);
  assert.equal(comparison.transition_counts["promote->hazard_blocked"], 2);
  assert.deepEqual(comparison.controller_promoted_negative_conditions, []);
  assert.equal(comparison.fail_closed, true);
});

test("benchmark snapshot composes the main summary layers", () => {
  const snapshot = buildBenchmarkSnapshot({
    conditionRecords: bundle.conditionRecords,
    coverageTrustReceipt: bundle.coverageTrustReceipt,
    benchmarkShellReceipt: bundle.benchmarkShellReceipt,
    contradictionLedger: bundle.contradictionLedger,
    cx004ValidationHandoff: bundle.cx004ValidationHandoff,
    cx004ValidationHandoffReceipt: bundle.cx004ValidationHandoffReceipt,
    passiveRecommendationScaffold: bundle.passiveRecommendationScaffold,
    passiveRecommendationReceipt: bundle.passiveRecommendationReceipt,
    ageOnlyRows,
    controllerRows,
  });

  assert.equal(snapshot.condition_count, 8);
  assert.equal(snapshot.phase_counts.maturation_phase_bulk_plus_abstention, 4);
  assert.equal(snapshot.study_family_counts.gill_2022, 3);
  assert.deepEqual(snapshot.negative_pressure_condition_ids, [
    "VITA_CTRL_002",
    "VITA_CTRL_004",
    "VITA_CTRL_006",
    "VITA_CTRL_007",
  ]);
  assert.equal(snapshot.shell.fail_closed, true);
  assert.equal(snapshot.contradictions.live_contradiction_count, 8);
  assert.equal(snapshot.validation_handoff.handoff_verdict, "cx004_validation_handoff_frozen");
  assert.equal(snapshot.recommendations.protocol_object_count, 8);
  assert.equal(snapshot.recommendations.live_recommendation_active_count, 0);
  assert.equal(snapshot.outputs.transition_counts["promote->downgrade"], 3);
});
