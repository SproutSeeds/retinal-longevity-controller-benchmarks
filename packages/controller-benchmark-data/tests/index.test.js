import test from "node:test";
import assert from "node:assert/strict";

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
  readCompilerRule,
  readConditionFixture,
  readConditionRecords,
  readContradictionKernelReceipt,
  readContradictionLedger,
  readCx004ValidationHandoff,
  readCx004ValidationHandoffReceipt,
  readControllerOutputRows,
  readCoverageTrustReceipt,
  readNegativeFamilyRegistry,
  readPassiveRecommendationReceipt,
  readPassiveRecommendationScaffold,
  readStudyCorpusRows,
} from "../src/index.js";

test("bundle metadata is available", () => {
  assert.equal(BUNDLE_ID, "phase-stratified-controller-benchmark-v0");
  assert.equal(BUNDLE_MANIFEST.condition_count, 8);
  assert.equal(BUNDLE_MANIFEST.coverage_verdict, "all_live_conditions_rule_backed");
});

test("artifact registry exposes the core bundle surfaces", () => {
  assert.deepEqual(listArtifacts(), [
    "studyCorpus",
    "negativeFamilyRegistry",
    "conditionFixture",
    "conditionRecords",
    "compileReceipt",
    "coverageTrustReceipt",
    "matrixExtractionIntermediate",
    "matrixFieldLayer",
    "matrixExtractionReceipt",
    "ageOnlyBaselineOutput",
    "controllerOutput",
    "benchmarkShellReceipt",
    "contradictionLedger",
    "contradictionKernelReceipt",
    "cx004ValidationHandoff",
    "cx004ValidationHandoffReceipt",
    "passiveRecommendationScaffold",
    "passiveRecommendationReceipt",
  ]);
  assert.equal(
    getArtifactPath("conditionRecords"),
    "controller-benchmark-condition-records-v0.jsonl",
  );
  assert.equal(
    getArtifactUrl("conditionRecords").pathname.endsWith(
      "/controller-benchmark-condition-records-v0.jsonl",
    ),
    true,
  );
});

test("study corpus and negative family registry are readable", () => {
  const studyCorpus = readStudyCorpusRows();
  const negativeFamilies = readNegativeFamilyRegistry();

  assert.equal(studyCorpus.length, 10);
  assert.equal(studyCorpus[0].study_family_id, "sarkar_2020");
  assert.equal(negativeFamilies.length, 4);
  assert.equal(negativeFamilies[0].family_id, "ohnishi_premature_termination_tumor_hazard");
});

test("compiled condition records and fixture are readable", () => {
  const fixture = readConditionFixture();
  const records = readConditionRecords();

  assert.equal(fixture.length, 8);
  assert.equal(records.length, 8);
  assert.equal(records[0].condition_id, "VITA_CTRL_001");
  assert.equal(records[2].study_family_id, "gill_2022");
});

test("compiler rules are readable", () => {
  const rules = listCompilerRules();
  const gillRule = readCompilerRule("gill_2022-v0");

  assert.deepEqual(rules, [
    "gill_2022-v0",
    "human_full_reprog_d14-v0",
    "ohnishi_2014-v0",
    "olova_ohnuki-v0",
    "roux_2022_sc-v0",
    "sarkar_2020-v0",
  ]);
  assert.equal(gillRule.study_family_id, "gill_2022");
});

test("receipts and output tables remain aligned with the live shell", () => {
  const coverage = readCoverageTrustReceipt();
  const shell = readBenchmarkShellReceipt();
  const contradictionLedger = readContradictionLedger();
  const contradictionKernelReceipt = readContradictionKernelReceipt();
  const cx004ValidationHandoff = readCx004ValidationHandoff();
  const cx004ValidationHandoffReceipt = readCx004ValidationHandoffReceipt();
  const passiveRecommendationScaffold = readPassiveRecommendationScaffold();
  const passiveRecommendationReceipt = readPassiveRecommendationReceipt();
  const ageOnlyRows = readAgeOnlyBaselineOutputRows();
  const controllerRows = readControllerOutputRows();

  assert.equal(coverage.rule_backed_condition_count, 8);
  assert.equal(coverage.fixture_backed_condition_count, 0);
  assert.equal(shell.summary.controller_output_counts.promote, 1);
  assert.equal(contradictionLedger.live_contradictions.length, 8);
  assert.equal(
    contradictionKernelReceipt.kernel_verdict,
    "first_live_contradiction_classes_frozen",
  );
  assert.deepEqual(cx004ValidationHandoff.target_pair.condition_ids, [
    "VITA_CTRL_003",
    "VITA_CTRL_005",
  ]);
  assert.equal(
    cx004ValidationHandoffReceipt.handoff_verdict,
    "cx004_validation_handoff_frozen",
  );
  assert.deepEqual(contradictionKernelReceipt.armed_not_triggered_class_ids, [
    "CX-WATCH-002",
  ]);
  assert.equal(passiveRecommendationScaffold.protocol_objects.length, 8);
  assert.equal(
    passiveRecommendationReceipt.dormant_verdict,
    "passive_scaffolding_only_live_recommendation_dormant",
  );
  assert.equal(passiveRecommendationReceipt.contradiction_cited_protocol_object_count, 5);
  assert.equal(ageOnlyRows.length, 8);
  assert.equal(controllerRows.length, 8);
});

test("latest bundle loader returns a coherent snapshot", () => {
  const bundle = loadLatestBundle();

  assert.equal(bundle.bundleId, BUNDLE_ID);
  assert.equal(bundle.manifest.bundle_id, BUNDLE_ID);
  assert.equal(bundle.conditionRecords.length, 8);
  assert.equal(bundle.benchmarkShellReceipt.condition_count, 8);
  assert.equal(bundle.contradictionLedger.live_contradictions.length, 8);
  assert.equal(bundle.contradictionKernelReceipt.live_contradiction_count, 8);
  assert.equal(bundle.cx004ValidationHandoff.handoff_id, "CTRL-VITA-CX004-HANDOFF-V0-001");
  assert.equal(
    bundle.cx004ValidationHandoffReceipt.handoff_verdict,
    "cx004_validation_handoff_frozen",
  );
  assert.equal(bundle.passiveRecommendationScaffold.protocol_objects.length, 8);
  assert.equal(bundle.passiveRecommendationReceipt.protocol_object_count, 8);
});
