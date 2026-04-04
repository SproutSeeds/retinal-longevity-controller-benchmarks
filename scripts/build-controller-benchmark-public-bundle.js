import { mkdirSync, readFileSync, readdirSync, rmSync, writeFileSync } from "node:fs";
import { dirname, extname, join } from "node:path";
import { fileURLToPath } from "node:url";

const REPO_ROOT = dirname(dirname(fileURLToPath(import.meta.url)));
const SOURCE_ROOT = join(
  REPO_ROOT,
  "programs",
  "partial-reprogramming-controller",
  "benchmarks",
  "phase-stratified-controller-benchmark-v0",
);
const TARGET_ROOT = join(
  REPO_ROOT,
  "packages",
  "controller-benchmark-data",
  "data",
  "phase-stratified-controller-benchmark-v0",
);
const DATA_PACKAGE_JSON = join(
  REPO_ROOT,
  "packages",
  "controller-benchmark-data",
  "package.json",
);

const FILE_RENAMES = new Map([
  ["controller-benchmark-study-corpus-v0.csv", "controller-benchmark-study-corpus-v0.csv"],
  ["controller-benchmark-negative-family-registry-v0.json", "controller-benchmark-negative-family-registry-v0.json"],
  ["controller-benchmark-condition-fixture-v0.jsonl", "controller-benchmark-condition-fixture-v0.jsonl"],
  ["controller-benchmark-condition-records-v0.jsonl", "controller-benchmark-condition-records-v0.jsonl"],
  ["controller-benchmark-condition-record-compile-receipt-v0.json", "controller-benchmark-condition-record-compile-receipt-v0.json"],
  ["controller-benchmark-compiler-coverage-trust-receipt-v0.json", "controller-benchmark-compiler-coverage-trust-receipt-v0.json"],
  ["controller-benchmark-age-only-baseline-outputs-v0.csv", "controller-benchmark-age-only-baseline-outputs-v0.csv"],
  ["controller-benchmark-controller-outputs-v0.csv", "controller-benchmark-controller-outputs-v0.csv"],
  ["controller-benchmark-shell-receipt-v0.json", "controller-benchmark-shell-receipt-v0.json"],
  ["controller-benchmark-contradiction-ledger-v0.json", "controller-benchmark-contradiction-ledger-v0.json"],
  ["controller-benchmark-contradiction-kernel-receipt-v0.json", "controller-benchmark-contradiction-kernel-receipt-v0.json"],
  ["controller-benchmark-cx004-validation-handoff-v0.json", "controller-benchmark-cx004-validation-handoff-v0.json"],
  ["controller-benchmark-cx004-validation-handoff-receipt-v0.json", "controller-benchmark-cx004-validation-handoff-receipt-v0.json"],
  ["controller-benchmark-passive-recommendation-scaffold-v0.json", "controller-benchmark-passive-recommendation-scaffold-v0.json"],
  ["controller-benchmark-passive-recommendation-receipt-v0.json", "controller-benchmark-passive-recommendation-receipt-v0.json"],
]);

const TEXT_REPLACEMENTS = [
  ["/Volumes/Code_2TB/code/longevity-research/", "repo:/"],
];

function ensureDir(path) {
  mkdirSync(path, { recursive: true });
}

function writeText(path, content) {
  ensureDir(dirname(path));
  writeFileSync(path, content);
}

function renamedBasename(name) {
  return FILE_RENAMES.get(name) ?? name;
}

function sanitizeText(text) {
  let current = text;
  for (const [from, to] of TEXT_REPLACEMENTS) {
    current = current.split(from).join(to);
  }
  return current;
}

function copyDirRecursive(sourceDir, targetDir) {
  for (const entry of readdirSync(sourceDir, { withFileTypes: true })) {
    const sourcePath = join(sourceDir, entry.name);
    const targetPath = join(targetDir, renamedBasename(entry.name));

    if (entry.isDirectory()) {
      ensureDir(targetPath);
      copyDirRecursive(sourcePath, targetPath);
      continue;
    }

    const content = readFileSync(sourcePath, "utf-8");
    const extension = extname(entry.name);
    const output =
      extension === ".json" ||
      extension === ".jsonl" ||
      extension === ".csv"
        ? sanitizeText(content)
        : content;
    writeText(targetPath, output);
  }
}

function buildManifest() {
  const { version: dataPackageVersion } = JSON.parse(
    readFileSync(DATA_PACKAGE_JSON, "utf-8"),
  );

  return {
    bundle_id: "phase-stratified-controller-benchmark-v0",
    package_name: "controller-benchmark-data",
    package_version: dataPackageVersion,
    benchmark_name: "Phase-stratified controller benchmark bundle",
    description:
      "Versioned benchmark bundle for the phase-stratified, abstention-capable controller shell.",
    generated_on: new Date().toISOString(),
    condition_count: 8,
    rule_backed_condition_count: 8,
    coverage_verdict: "all_live_conditions_rule_backed",
    artifacts: {
      studyCorpus: {
        path: "controller-benchmark-study-corpus-v0.csv",
        format: "csv",
        role: "benchmark_input",
      },
      negativeFamilyRegistry: {
        path: "controller-benchmark-negative-family-registry-v0.json",
        format: "json",
        role: "benchmark_input",
      },
      conditionFixture: {
        path: "controller-benchmark-condition-fixture-v0.jsonl",
        format: "jsonl",
        role: "historical_compile_input",
      },
      conditionRecords: {
        path: "controller-benchmark-condition-records-v0.jsonl",
        format: "jsonl",
        role: "live_benchmark_object",
      },
      compileReceipt: {
        path: "controller-benchmark-condition-record-compile-receipt-v0.json",
        format: "json",
        role: "compile_receipt",
      },
      coverageTrustReceipt: {
        path: "controller-benchmark-compiler-coverage-trust-receipt-v0.json",
        format: "json",
        role: "trust_receipt",
      },
      matrixExtractionIntermediate: {
        path: "matrix-extraction/gill_2022-matrix-derived-extraction-intermediate-v0.json",
        format: "json",
        role: "matrix_extraction_intermediate",
      },
      matrixFieldLayer: {
        path: "matrix-extraction/gill_2022-matrix-derived-field-layer-v0.json",
        format: "json",
        role: "matrix_field_layer",
      },
      matrixExtractionReceipt: {
        path: "matrix-extraction/gill_2022-matrix-extraction-receipt-v0.json",
        format: "json",
        role: "matrix_extraction_receipt",
      },
      ageOnlyBaselineOutput: {
        path: "controller-benchmark-age-only-baseline-outputs-v0.csv",
        format: "csv",
        role: "benchmark_output",
      },
      controllerOutput: {
        path: "controller-benchmark-controller-outputs-v0.csv",
        format: "csv",
        role: "benchmark_output",
      },
      benchmarkShellReceipt: {
        path: "controller-benchmark-shell-receipt-v0.json",
        format: "json",
        role: "benchmark_receipt",
      },
      contradictionLedger: {
        path: "controller-benchmark-contradiction-ledger-v0.json",
        format: "json",
        role: "contradiction_ledger",
      },
      contradictionKernelReceipt: {
        path: "controller-benchmark-contradiction-kernel-receipt-v0.json",
        format: "json",
        role: "contradiction_receipt",
      },
      cx004ValidationHandoff: {
        path: "controller-benchmark-cx004-validation-handoff-v0.json",
        format: "json",
        role: "validation_handoff",
      },
      cx004ValidationHandoffReceipt: {
        path: "controller-benchmark-cx004-validation-handoff-receipt-v0.json",
        format: "json",
        role: "validation_handoff_receipt",
      },
      cx004PartnerPacket: {
        path: "controller-benchmark-cx004-partner-executable-validation-packet-v0.json",
        format: "json",
        role: "validation_partner_packet",
      },
      cx004PartnerPacketReceipt: {
        path: "controller-benchmark-cx004-partner-executable-validation-packet-receipt-v0.json",
        format: "json",
        role: "validation_partner_packet_receipt",
      },
      cx004ResolutionReceiptContract: {
        path: "controller-benchmark-cx004-resolution-receipt-contract-v0.json",
        format: "json",
        role: "resolution_receipt_contract",
      },
      cx004PartnerReturnTemplate: {
        path: "controller-benchmark-cx004-partner-return-template-v0.json",
        format: "json",
        role: "resolution_partner_return_template",
      },
      cx004ExampleInsufficientPartnerReturn: {
        path: "controller-benchmark-cx004-example-insufficient-partner-return-v0.json",
        format: "json",
        role: "resolution_example_partner_return",
      },
      cx004ExampleInsufficientResolutionReceipt: {
        path: "controller-benchmark-cx004-example-insufficient-resolution-receipt-v0.json",
        format: "json",
        role: "resolution_example_receipt",
      },
      cx004ResolutionReviewContract: {
        path: "controller-benchmark-cx004-resolution-review-contract-v0.json",
        format: "json",
        role: "resolution_review_contract",
      },
      cx004ExampleInsufficientResolutionReviewReceipt: {
        path: "controller-benchmark-cx004-example-insufficient-resolution-review-receipt-v0.json",
        format: "json",
        role: "resolution_review_example_receipt",
      },
      passiveRecommendationScaffold: {
        path: "controller-benchmark-passive-recommendation-scaffold-v0.json",
        format: "json",
        role: "passive_recommendation_scaffold",
      },
      passiveRecommendationReceipt: {
        path: "controller-benchmark-passive-recommendation-receipt-v0.json",
        format: "json",
        role: "passive_recommendation_receipt",
      },
    },
    compiler_rules: readdirSync(join(TARGET_ROOT, "compiler-rules"))
      .filter((filename) => filename.endsWith(".json"))
      .map((filename) => filename.replace(/\.json$/, ""))
      .sort(),
  };
}

rmSync(TARGET_ROOT, { recursive: true, force: true });
ensureDir(TARGET_ROOT);
copyDirRecursive(SOURCE_ROOT, TARGET_ROOT);
writeText(
  join(TARGET_ROOT, "bundle-manifest.json"),
  `${JSON.stringify(buildManifest(), null, 2)}\n`,
);
