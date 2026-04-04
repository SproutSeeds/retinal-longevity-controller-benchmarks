import { readFileSync, readdirSync } from "node:fs";

export const BUNDLE_ID = "phase-stratified-controller-benchmark-v0";

const BUNDLE_ROOT_URL = new URL(`../data/${BUNDLE_ID}/`, import.meta.url);
const COMPILER_RULES_DIR_URL = new URL("compiler-rules/", BUNDLE_ROOT_URL);

function readText(url) {
  return readFileSync(url, "utf-8");
}

function readJson(url) {
  return JSON.parse(readText(url));
}

function parseJsonl(text) {
  return text
    .split(/\r?\n/)
    .map((line) => line.trim())
    .filter(Boolean)
    .map((line) => JSON.parse(line));
}

function parseCsv(text) {
  const rows = [];
  let currentField = "";
  let currentRow = [];
  let inQuotes = false;

  for (let index = 0; index < text.length; index += 1) {
    const char = text[index];
    const next = text[index + 1];

    if (char === "\"") {
      if (inQuotes && next === "\"") {
        currentField += "\"";
        index += 1;
      } else {
        inQuotes = !inQuotes;
      }
      continue;
    }

    if (!inQuotes && char === ",") {
      currentRow.push(currentField);
      currentField = "";
      continue;
    }

    if (!inQuotes && (char === "\n" || char === "\r")) {
      if (char === "\r" && next === "\n") {
        index += 1;
      }
      currentRow.push(currentField);
      rows.push(currentRow);
      currentField = "";
      currentRow = [];
      continue;
    }

    currentField += char;
  }

  if (currentField.length > 0 || currentRow.length > 0) {
    currentRow.push(currentField);
    rows.push(currentRow);
  }

  if (rows.length === 0) {
    return [];
  }

  const [header, ...dataRows] = rows;
  return dataRows
    .filter((row) => row.some((value) => value !== ""))
    .map((row) =>
      Object.fromEntries(
        header.map((column, index) => [column, row[index] ?? ""]),
      ),
    );
}

export const BUNDLE_MANIFEST = Object.freeze(
  readJson(new URL("bundle-manifest.json", BUNDLE_ROOT_URL)),
);

const ARTIFACTS = Object.freeze(BUNDLE_MANIFEST.artifacts);
const COMPILER_RULE_FILE_MAP = Object.freeze(
  Object.fromEntries(
    readdirSync(COMPILER_RULES_DIR_URL)
      .filter((filename) => filename.endsWith(".json"))
      .sort()
      .map((filename) => [filename.replace(/\.json$/, ""), filename]),
  ),
);

export function listArtifacts() {
  return Object.freeze(Object.keys(ARTIFACTS));
}

export function getArtifactPath(name) {
  if (!Object.hasOwn(ARTIFACTS, name)) {
    throw new Error(
      `Unknown artifact name: ${name}. Expected one of: ${Object.keys(ARTIFACTS).join(", ")}`,
    );
  }

  return ARTIFACTS[name].path;
}

export function getArtifactUrl(name) {
  return new URL(getArtifactPath(name), BUNDLE_ROOT_URL);
}

export function readArtifactRaw(name) {
  return readText(getArtifactUrl(name));
}

export function readStudyCorpusRaw() {
  return readArtifactRaw("studyCorpus");
}

export function readStudyCorpusRows() {
  return parseCsv(readStudyCorpusRaw());
}

export function readNegativeFamilyRegistry() {
  return readJson(getArtifactUrl("negativeFamilyRegistry"));
}

export function readConditionFixture() {
  return parseJsonl(readArtifactRaw("conditionFixture"));
}

export function readConditionRecords() {
  return parseJsonl(readArtifactRaw("conditionRecords"));
}

export function readCompileReceipt() {
  return readJson(getArtifactUrl("compileReceipt"));
}

export function readCoverageTrustReceipt() {
  return readJson(getArtifactUrl("coverageTrustReceipt"));
}

export function readAgeOnlyBaselineOutputRaw() {
  return readArtifactRaw("ageOnlyBaselineOutput");
}

export function readAgeOnlyBaselineOutputRows() {
  return parseCsv(readAgeOnlyBaselineOutputRaw());
}

export function readControllerOutputRaw() {
  return readArtifactRaw("controllerOutput");
}

export function readControllerOutputRows() {
  return parseCsv(readControllerOutputRaw());
}

export function readBenchmarkShellReceipt() {
  return readJson(getArtifactUrl("benchmarkShellReceipt"));
}

export function readContradictionLedger() {
  return readJson(getArtifactUrl("contradictionLedger"));
}

export function readContradictionKernelReceipt() {
  return readJson(getArtifactUrl("contradictionKernelReceipt"));
}

export function readCx004ValidationHandoff() {
  return readJson(getArtifactUrl("cx004ValidationHandoff"));
}

export function readCx004ValidationHandoffReceipt() {
  return readJson(getArtifactUrl("cx004ValidationHandoffReceipt"));
}

export function readPassiveRecommendationScaffold() {
  return readJson(getArtifactUrl("passiveRecommendationScaffold"));
}

export function readPassiveRecommendationReceipt() {
  return readJson(getArtifactUrl("passiveRecommendationReceipt"));
}

export function listCompilerRules() {
  return Object.freeze(Object.keys(COMPILER_RULE_FILE_MAP));
}

export function readCompilerRule(name) {
  if (!Object.hasOwn(COMPILER_RULE_FILE_MAP, name)) {
    throw new Error(
      `Unknown compiler rule: ${name}. Expected one of: ${Object.keys(COMPILER_RULE_FILE_MAP).join(", ")}`,
    );
  }

  return readJson(new URL(COMPILER_RULE_FILE_MAP[name], COMPILER_RULES_DIR_URL));
}

export function loadLatestBundle() {
  return {
    bundleId: BUNDLE_ID,
    manifest: BUNDLE_MANIFEST,
    studyCorpusRows: readStudyCorpusRows(),
    negativeFamilyRegistry: readNegativeFamilyRegistry(),
    conditionRecords: readConditionRecords(),
    compileReceipt: readCompileReceipt(),
    coverageTrustReceipt: readCoverageTrustReceipt(),
    benchmarkShellReceipt: readBenchmarkShellReceipt(),
    contradictionLedger: readContradictionLedger(),
    contradictionKernelReceipt: readContradictionKernelReceipt(),
    cx004ValidationHandoff: readCx004ValidationHandoff(),
    cx004ValidationHandoffReceipt: readCx004ValidationHandoffReceipt(),
    passiveRecommendationScaffold: readPassiveRecommendationScaffold(),
    passiveRecommendationReceipt: readPassiveRecommendationReceipt(),
  };
}
