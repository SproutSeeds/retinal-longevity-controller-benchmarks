#!/usr/bin/env python3
"""Verify this dated source review, optionally replaying retained source bytes.

Offline by default. No source code execution, plot digitization, clock fitting,
mail access or numerical biological comparison is performed.
"""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import sys
import zipfile


HERE = Path(__file__).resolve().parent


def sha(data):
    return hashlib.sha256(data).hexdigest()


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def inventory(path):
    with zipfile.ZipFile(path) as archive:
        if archive.testzip() is not None:
            raise ValueError("Archive CRC failure: " + path.name)
        entries = []
        for member in archive.infolist():
            data = archive.read(member)
            entries.append({"name": member.filename, "bytes": len(data),
                            "sha256": sha(data), "compression": member.compress_type})
        return {"archive": path.name, "crc_check": None, "members": entries}


def verify(source_dir=None):
    manifest = read_json(HERE / "ARTIFACT_MANIFEST.json")
    for name, expected in manifest["files"].items():
        if Path(name).name != name or sha((HERE / name).read_bytes()) != expected:
            raise ValueError("Released artifact changed: " + name)

    review = read_json(HERE / "REVIEW.json")
    acquisition = read_json(HERE / "ACQUISITION.json")
    archives = read_json(HERE / "ARCHIVE_INVENTORY.json")
    for name, expected in review["protected_dependencies"].items():
        if sha((HERE.parent / name).read_bytes()) != expected:
            raise ValueError("Frozen dependency changed: " + name)
    freeze = read_json(HERE.parent / "gill-migration-comparison-2026-10-31/FREEZE.json")
    for name, expected in freeze["files"].items():
        if sha((HERE.parent / "gill-migration-comparison-2026-10-31" / name).read_bytes()) != expected:
            raise ValueError("Original freeze differs: " + name)

    successful = [item for item in acquisition["requests"] if item.get("status") == 200]
    failed = [item for item in acquisition["requests"] if item.get("status") != 200]
    expected_names = {"cambridge-additional-files.zip", "gill-thesis.pdf",
                      "gill-thesis.txt", "elife-71624-supp-v1.zip"}
    if len(successful) != 4 or {row["name"] for row in successful} != expected_names:
        raise ValueError("Source acquisition roster differs")
    if len(failed) != 1 or failed[0]["status"] != 404 or failed[0]["name"] != "elife-71624-supp-v2.zip":
        raise ValueError("Failed speculative URL disposition differs")
    for item in successful:
        if item["name"].startswith("cambridge") or item["name"].startswith("gill-thesis"):
            if item["bytes"] != item["expected_bytes"] or item["md5"] != item["expected_md5"]:
                raise ValueError("Repository metadata mismatch: " + item["name"])

    if len(archives) != 2 or [len(a["members"]) for a in archives] != [13, 8]:
        raise ValueError("Archive inventory coverage differs")
    by_archive = {a["archive"]: a for a in archives}
    for archive in archives:
        names = [m["name"] for m in archive["members"]]
        if len(names) != len(set(names)) or archive["crc_check"] is not None:
            raise ValueError("Archive member identity or CRC record differs")
    counts = [Counter(Path(m["name"]).suffix for m in a["members"]) for a in archives]
    if counts != [Counter({".tif": 9, ".xlsx": 3, ".docx": 1}),
                  Counter({".pdf": 4, ".xlsx": 3, ".docx": 1})]:
        raise ValueError("Archive file types differ")
    shared = set(m["sha256"] for m in archives[0]["members"]) & set(m["sha256"] for m in archives[1]["members"])
    if shared != set(review["shared_workbook_and_form_sha256"]):
        raise ValueError("Cross-archive shared file identities differ")
    if (review["admission"]["status"], review["admission"]["new_joint_pairs"],
            review["admission"]["eligible_frozen_pairs"]) != ("DEFERRED", 0, 13):
        raise ValueError("Admission scope changed")
    if review["clock_version"]["equivalence"] != "NOT_ESTABLISHED":
        raise ValueError("Clock equivalence overclaimed")

    replay = "NOT_RUN"
    if source_dir is not None:
        source_dir = Path(source_dir)
        missing = [r["name"] for r in successful if not (source_dir / r["name"]).is_file()]
        if missing:
            raise FileNotFoundError("Missing pinned sources: " + ", ".join(missing))
        for item in successful:
            path = source_dir / item["name"]
            data = path.read_bytes()
            if len(data) != item["bytes"] or sha(data) != item["sha256"] or hashlib.md5(data).hexdigest() != item["md5"]:
                raise ValueError("Source bytes changed: " + item["name"])
            if path.suffix == ".zip" and inventory(path) != by_archive[path.name]:
                raise ValueError("Source member inventory changed: " + path.name)
        text = (source_dir / "gill-thesis.txt").read_text(encoding="utf-8")
        for phrase in ["13.48 years", "Figure 4.16:", "scratch wound assays"]:
            if phrase not in text:
                raise ValueError("Thesis source marker absent: " + phrase)
        replay = "PASS"
    return {"schema": "gill.archive-review-verification/1", "status": "PASS",
            "claim_level": "Verified source integrity and scoped intake disposition",
            "released_artifacts_verified": len(manifest["files"]),
            "frozen_inputs_verified": len(freeze["files"]),
            "protected_dependencies_verified": len(review["protected_dependencies"]),
            "source_files": 4, "archive_member_occurrences": 21,
            "full_source_replay": replay, "joint_admission": "DEFERRED",
            "new_joint_pairs": 0, "biological_comparison": "INCONCLUSIVE"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sources", type=Path, help="Directory containing the four original, pinned files")
    args = parser.parse_args()
    try:
        result = verify(args.sources)
        code = 0
    except FileNotFoundError as error:
        result = {"status": "INCONCLUSIVE", "reason": str(error)}
        code = 2
    except (ValueError, OSError, KeyError, zipfile.BadZipFile) as error:
        result = {"status": "FAIL", "reason": str(error)}
        code = 1
    print(json.dumps(result, indent=2, sort_keys=True))
    return code


if __name__ == "__main__":
    sys.exit(main())
