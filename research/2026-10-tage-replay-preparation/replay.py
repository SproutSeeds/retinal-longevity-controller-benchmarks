#!/usr/bin/env python3
"""Offline preparation checks for a historical tAge replay; never executes a model."""

import argparse
import csv
import hashlib
import io
import json
import re
import sys
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation, localcontext
from pathlib import Path, PurePosixPath

ROOT = Path(__file__).resolve().parent
CONTRACT = ROOT / "workflow-contract.json"
ARTIFACT_ROLES = {
    "model", "preprocessing", "environment", "provenance", "gene_map",
    "sample_map", "feature_matrix", "expected_predictions", "reference_values",
}
MANIFEST_KEYS = {
    "schema", "evidence_kind", "study_accession", "model_identity", "provenance",
    "preprocessing", "reference_value_keys", "reference_values_explanation",
    "tolerances", "artifacts",
}
IDENTITY_KEYS = {
    "model_id", "historical_version", "training_target", "species", "tissue_scope",
    "feature_namespace", "prediction_unit", "historical_equivalence_declaration",
}
PROVENANCE_KEYS = {"declared_by", "source_locator", "received_utc", "historical_basis"}
PREPROCESSING_KEYS = {
    "input_scale", "normalization", "gene_mapping", "missing_gene_policy",
    "control_centering", "reference_cohorts", "fixture_stage",
}
FROZEN_KEYS = {
    "schema", "created_utc", "manifest_sha256", "validator_sha256",
    "contract_sha256", "artifact_sha256", "evidence_kind", "tolerances",
    "planning_context", "gates",
}
RUN_KEYS = {
    "schema", "evidence_kind", "freeze_sha256", "manifest_sha256",
    "declared_input_sha256", "execution_evidence", "prediction_unit",
    "observed_predictions",
}
MAX_JSON_BYTES = 2 * 1024 * 1024
MAX_TABLE_BYTES = 64 * 1024 * 1024
SHA = re.compile(r"^[0-9a-f]{64}$")
SYNTHETIC = "synthetic_demo"
HISTORICAL = "author_supplied_historical"


class InvalidPacket(ValueError):
    """A required preparation check failed."""


def require(condition, message):
    if not condition:
        raise InvalidPacket(message)


def exact_keys(value, keys, label):
    require(isinstance(value, dict), f"{label}: expected an object")
    require(set(value) == set(keys), f"{label}: missing or unexpected fields: {sorted(set(value) ^ set(keys))}")


def clean_text(value, label):
    require(isinstance(value, str) and bool(value.strip()), f"{label}: expected nonempty text")
    require(value == value.strip() and not any(ord(c) < 32 for c in value), f"{label}: whitespace/control character ambiguity")
    return value


def unique_strings(values, label):
    require(isinstance(values, list), f"{label}: expected a list")
    for value in values:
        clean_text(value, label)
    require(len(values) == len(set(values)), f"{label}: duplicate identifiers")
    return values


def digest(path):
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def reject_constant(value):
    raise InvalidPacket(f"JSON nonfinite constant rejected: {value}")


def unique_object(pairs):
    obj = {}
    for key, value in pairs:
        require(key not in obj, f"JSON duplicate key: {key}")
        obj[key] = value
    return obj


def read_json(path):
    require(path.is_file() and not path.is_symlink(), f"JSON file missing or symlink: {path.name}")
    require(path.stat().st_size <= MAX_JSON_BYTES, "JSON exceeds preparation size limit")
    return json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=unique_object, parse_constant=reject_constant)


def finite_number(value, label):
    clean_text(value, label)
    require(len(value) <= 80, f"{label}: numeric representation too long")
    try:
        number = Decimal(value)
    except InvalidOperation as exc:
        raise InvalidPacket(f"{label}: invalid number") from exc
    require(number.is_finite(), f"{label}: nonfinite value")
    require(re.fullmatch(r"[+-]?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)(?:[eE][+-]?[0-9]+)?", value),
            f"{label}: require a decimal numeric string")
    # Bound the parser's arithmetic workload; no scientific values are clipped.
    require(abs(number.adjusted()) <= 300, f"{label}: unsupported numeric exponent")
    return number


def timestamp(value, label):
    clean_text(value, label)
    require(value.endswith("Z"), f"{label}: require UTC ISO-8601 ending in Z")
    try:
        datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError as exc:
        raise InvalidPacket(f"{label}: invalid timestamp") from exc


def artifact_path(root, artifact, label):
    exact_keys(artifact, {"path", "sha256", "bytes"}, label)
    name = clean_text(artifact["path"], label + ".path")
    part = PurePosixPath(name)
    require(not part.is_absolute() and ".." not in part.parts and "\\" not in name,
            f"{label}: path must stay inside its packet directory")
    require(name == part.as_posix() and name != ".", f"{label}: noncanonical path")
    base = root.resolve()
    candidate = base
    for piece in part.parts:
        candidate = candidate / piece
        require(not candidate.is_symlink(), f"{label}: symlinks are not accepted")
    require(candidate.is_file(), f"{label}: artifact missing")
    require(candidate.resolve().is_relative_to(base), f"{label}: path escapes packet directory")
    require(isinstance(artifact["sha256"], str) and SHA.fullmatch(artifact["sha256"]), f"{label}: invalid sha256")
    require(type(artifact["bytes"]) is int and artifact["bytes"] > 0, f"{label}: invalid byte count")
    require(candidate.stat().st_size == artifact["bytes"], f"{label}: byte count mismatch")
    require(digest(candidate) == artifact["sha256"], f"{label}: sha256 mismatch")
    return candidate


def table(path, columns):
    require(path.stat().st_size <= MAX_TABLE_BYTES, f"{path.name}: CSV exceeds preparation size limit")
    raw = path.read_text(encoding="utf-8")
    reader = csv.DictReader(io.StringIO(raw, newline=""), strict=True)
    require(reader.fieldnames == columns, f"{path.name}: expected exact CSV columns {columns}")
    rows = list(reader)
    for row in rows:
        require(set(row) == set(columns) and all(value is not None for value in row.values()),
                f"{path.name}: malformed CSV row")
        for key, value in row.items():
            clean_text(value, f"{path.name}.{key}")
    return rows


def unique_column(rows, column, label):
    values = [row[column] for row in rows]
    require(len(values) == len(set(values)), f"{label}: duplicate {column}")
    return set(values)


def prediction_table(path, expected_samples):
    rows = table(path, ["reference_sample_id", "prediction"])
    keys = unique_column(rows, "reference_sample_id", path.name)
    require(keys == expected_samples, f"{path.name}: missing or unexpected reference sample keys")
    return {row["reference_sample_id"]: finite_number(row["prediction"], path.name) for row in rows}


def gates():
    # This preparation release has no configurable path around the missing adapter.
    return {
        "artifact_intake": "VALIDATED_DECLARATIONS_ONLY",
        "reference_ready": "BLOCKED_ADAPTER_UNRESOLVED",
        "reference_pass": "BLOCKED_NO_VERIFIED_EXECUTION",
        "study_calculation": "NOT_RUN",
        "biological_interpretation": "INCONCLUSIVE",
    }


def validate_manifest(manifest_path):
    manifest_path = Path(manifest_path)
    manifest = read_json(manifest_path)
    exact_keys(manifest, MANIFEST_KEYS, "manifest")
    require(manifest["schema"] == "cx004.tage_received_manifest.v1", "unsupported manifest schema")
    require(isinstance(manifest["evidence_kind"], str) and manifest["evidence_kind"] in {SYNTHETIC, HISTORICAL}, "invalid evidence kind")
    require(manifest["study_accession"] == "GSE304044", "wrong study accession")
    for key, keys in [("model_identity", IDENTITY_KEYS), ("provenance", PROVENANCE_KEYS), ("preprocessing", PREPROCESSING_KEYS)]:
        exact_keys(manifest[key], keys, key)
        for field, value in manifest[key].items():
            clean_text(value, key + "." + field)
            require(not re.search(r"\b(UNRESOLVED|UNKNOWN|TBD|TODO|REPLACE_ME)\b", value, re.I),
                    f"{key}.{field}: unresolved declaration")
            if manifest["evidence_kind"] == HISTORICAL:
                require("synthetic" not in value.lower() and "placeholder" not in value.lower(),
                        f"{key}.{field}: synthetic declaration cannot be relabeled historical")
    timestamp(manifest["provenance"]["received_utc"], "received_utc")
    require(manifest["preprocessing"]["fixture_stage"] == "already_preprocessed_model_input",
            "fixture must be already-preprocessed model input; no transforms are implemented")
    reference_keys = set(unique_strings(manifest["reference_value_keys"], "reference_value_keys"))
    clean_text(manifest["reference_values_explanation"], "reference_values_explanation")
    tolerance = manifest["tolerances"]
    exact_keys(tolerance, {"absolute", "relative", "unit", "rationale"}, "tolerances")
    for key in ["absolute", "relative"]:
        require(finite_number(tolerance[key], "tolerances." + key) >= 0, "tolerances must be nonnegative")
    require(tolerance["unit"] == manifest["model_identity"]["prediction_unit"], "tolerance and prediction units differ")
    clean_text(tolerance["rationale"], "tolerance rationale")
    exact_keys(manifest["artifacts"], ARTIFACT_ROLES, "artifacts")
    paths = {role: artifact_path(manifest_path.parent, artifact, role) for role, artifact in manifest["artifacts"].items()}
    require(len(set(paths.values())) == len(paths), "each artifact role needs its own unambiguous path")

    genes = table(paths["gene_map"], ["source_gene_id", "model_gene_id", "model_position"])
    require(bool(genes), "gene map is empty")
    source_genes = unique_column(genes, "source_gene_id", "gene map")
    unique_column(genes, "model_gene_id", "gene map")
    positions = []
    for row in genes:
        require(re.fullmatch(r"[1-9][0-9]*", row["model_position"]), "gene map: invalid model position")
        positions.append(int(row["model_position"]))
    require(sorted(positions) == list(range(1, len(genes) + 1)), "gene map: positions must be unique contiguous 1..N")
    samples = table(paths["sample_map"], ["source_sample_id", "reference_sample_id"])
    require(bool(samples), "sample map is empty")
    source_samples = unique_column(samples, "source_sample_id", "sample map")
    reference_samples = unique_column(samples, "reference_sample_id", "sample map")
    all_ids = source_genes | {row["model_gene_id"] for row in genes} | source_samples | reference_samples
    if manifest["evidence_kind"] == SYNTHETIC:
        require(all(value.startswith("SYNTHETIC_") for value in all_ids), "synthetic identifiers require SYNTHETIC_ prefix")
        require(manifest["model_identity"]["model_id"].startswith("SYNTHETIC_"), "synthetic model identity requires SYNTHETIC_ prefix")
    else:
        require(all("synthetic" not in value.lower() for value in all_ids), "synthetic identifiers cannot be relabeled historical")
    matrix = table(paths["feature_matrix"], ["source_sample_id", "source_gene_id", "value"])
    seen = set()
    for row in matrix:
        key = (row["source_sample_id"], row["source_gene_id"])
        require(key not in seen, "feature matrix: duplicate sample/gene pair")
        require(key[0] in source_samples and key[1] in source_genes, "feature matrix: unexpected sample or gene")
        finite_number(row["value"], "feature matrix value")
        seen.add(key)
    require(len(seen) == len(source_samples) * len(source_genes), "feature matrix: missing sample/gene values; no implicit imputation")
    values = table(paths["reference_values"], ["reference_key", "value", "unit"])
    require(unique_column(values, "reference_key", "reference values") == reference_keys, "missing or unexpected reference value keys")
    for row in values:
        finite_number(row["value"], "reference value")
    expected = prediction_table(paths["expected_predictions"], reference_samples)
    return manifest, paths, expected


def frozen_fields(manifest_path, manifest):
    contract = read_json(CONTRACT)
    require(contract.get("historical_adapter") == "UNRESOLVED_NOT_IMPLEMENTED", "preparation contract cannot enable an adapter")
    return {
        "schema": "cx004.tage_frozen_preparation.v1",
        "manifest_sha256": digest(Path(manifest_path)),
        "validator_sha256": digest(Path(__file__).resolve()),
        "contract_sha256": digest(CONTRACT),
        "artifact_sha256": {role: value["sha256"] for role, value in manifest["artifacts"].items()},
        "evidence_kind": manifest["evidence_kind"],
        "tolerances": manifest["tolerances"],
        "planning_context": contract["planning_context"],
        "gates": gates(),
    }


def freeze(manifest_path):
    manifest, _, _ = validate_manifest(manifest_path)
    frozen = frozen_fields(manifest_path, manifest)
    frozen["created_utc"] = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    return frozen


def compare(manifest_path, freeze_path, freeze_sha256, run_path):
    require(isinstance(freeze_sha256, str) and SHA.fullmatch(freeze_sha256), "a retained freeze sha256 is required")
    frozen = read_json(Path(freeze_path))
    require(digest(Path(freeze_path)) == freeze_sha256, "frozen plan differs from retained sha256")
    exact_keys(frozen, FROZEN_KEYS, "frozen plan")
    timestamp(frozen["created_utc"], "frozen plan created_utc")
    manifest, _, expected = validate_manifest(manifest_path)
    required = frozen_fields(manifest_path, manifest)
    require({k: v for k, v in frozen.items() if k != "created_utc"} == required,
            "manifest, artifacts, tolerance, provenance, validator or contract changed after freeze")
    run_path = Path(run_path)
    run = read_json(run_path)
    exact_keys(run, RUN_KEYS, "observed run declaration")
    require(run["schema"] == "cx004.tage_external_output.v1", "unsupported run declaration schema")
    require(run["evidence_kind"] == manifest["evidence_kind"], "run evidence kind mismatch")
    require(run["freeze_sha256"] == freeze_sha256, "run declaration has wrong freeze sha256")
    require(run["manifest_sha256"] == required["manifest_sha256"], "run declaration has wrong manifest sha256")
    require(run["declared_input_sha256"] == required["artifact_sha256"], "run input provenance differs from frozen artifacts")
    require(run["execution_evidence"] == "externally_supplied_unverified", "this release cannot attest model execution")
    require(run["prediction_unit"] == manifest["model_identity"]["prediction_unit"], "observed prediction units differ")
    observed_path = artifact_path(run_path.parent, run["observed_predictions"], "observed predictions")
    observed = prediction_table(observed_path, set(expected))
    abs_tolerance = finite_number(manifest["tolerances"]["absolute"], "absolute tolerance")
    rel_tolerance = finite_number(manifest["tolerances"]["relative"], "relative tolerance")
    rows = []
    # Parser bounds + precision keep all accepted decimal arithmetic exact.
    with localcontext() as ctx:
        ctx.prec = 2048
        for sample in sorted(expected):
            delta = abs(observed[sample] - expected[sample])
            allowance = abs_tolerance + rel_tolerance * abs(expected[sample])
            rows.append({"reference_sample_id": sample, "expected": str(expected[sample]),
                         "observed": str(observed[sample]), "absolute_difference": str(delta),
                         "allowed_difference": str(allowance), "within_tolerance": delta <= allowance})
    matches = all(row["within_tolerance"] for row in rows)
    return {
        "schema": "cx004.tage_output_comparison.v1",
        "evidence_kind": manifest["evidence_kind"],
        "claim_level": "Verified" if matches else "Heuristic",
        "verification_scope": "Software validation and supplied numeric agreement only; model execution and historical provenance remain unverified.",
        "freeze_sha256": freeze_sha256,
        "manifest_sha256": required["manifest_sha256"],
        "run_declaration_sha256": digest(run_path),
        "observed_predictions_sha256": digest(observed_path),
        "numeric_comparison": "MATCH" if matches else "MISMATCH",
        "rows": rows,
        "gates": gates(),
        "reproduction_pass": False,
        "biological_pass": False,
    }


def write_json(path, value):
    # Exclusive creation preserves previous plans and receipts.
    with Path(path).open("x", encoding="utf-8") as handle:
        json.dump(value, handle, indent=2, sort_keys=True, allow_nan=False)
        handle.write("\n")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    intake = sub.add_parser("freeze", help="Validate received inputs and freeze their hashes; does not execute models")
    intake.add_argument("--manifest", required=True, type=Path)
    intake.add_argument("--out", required=True, type=Path)
    check = sub.add_parser("compare", help="Check externally supplied keyed values against the frozen reference")
    check.add_argument("--manifest", required=True, type=Path)
    check.add_argument("--freeze", required=True, type=Path)
    check.add_argument("--freeze-sha256", required=True)
    check.add_argument("--run", required=True, type=Path)
    check.add_argument("--out", required=True, type=Path)
    args = parser.parse_args(argv)
    try:
        if args.command == "freeze":
            result = freeze(args.manifest)
        else:
            result = compare(args.manifest, args.freeze, args.freeze_sha256, args.run)
        write_json(args.out, result)
        json.dump({"output": str(args.out), "sha256": digest(args.out), "gates": result["gates"],
                   "numeric_comparison": result.get("numeric_comparison", "NOT_RUN")}, sys.stdout, sort_keys=True)
        print()
        return 1 if result.get("numeric_comparison") == "MISMATCH" else 0
    except (InvalidPacket, OSError, ValueError, csv.Error, UnicodeError, RecursionError) as exc:
        blocked = gates()
        blocked["artifact_intake"] = "REJECTED"
        json.dump({"status": "REJECTED", "reason": str(exc), "gates": blocked,
                   "reproduction_pass": False, "biological_pass": False}, sys.stderr)
        print(file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
