"""Negative controls: incomplete/error inventories cannot support an absence claim."""
import copy
import json
from pathlib import Path
import tempfile
import unittest
import xml.etree.ElementTree as ET

from build_audit import geo_files, read_json, sra_inventory, tree_files

ROOT = Path(__file__).resolve().parent


class InventoryFailureControls(unittest.TestCase):
    def test_html_challenge_is_not_empty_json(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "response.json"
            path.write_text("<html>challenge</html>")
            with self.assertRaises(json.JSONDecodeError):
                read_json(path)

    def test_truncated_tree_rejected(self):
        with self.assertRaises(ValueError):
            tree_files({"truncated": True, "tree": []})

    def test_duplicate_tree_path_rejected(self):
        entry = {"type": "blob", "path": "one", "sha": "a", "size": 1}
        with self.assertRaises(ValueError):
            tree_files({"truncated": False, "tree": [entry, entry]})

    def test_missing_geo_matrix_member_rejected(self):
        text = (ROOT / "inventory-sources/geo-filelist.txt").read_text()
        text = "\n".join(line for line in text.splitlines() if "GSM7022367_1_matrix.mtx.gz" not in line)
        with self.assertRaises(ValueError):
            geo_files(text)

    def test_unclassified_geo_member_rejected(self):
        text = (ROOT / "inventory-sources/geo-filelist.txt").read_text()
        text = text.replace("GSM7022367_1_features.tsv.gz", "previously-unseen-animal-assignments.tsv.gz")
        with self.assertRaises(ValueError):
            geo_files(text)

    def test_conflicting_sra_run_rejected(self):
        root = ET.fromstring((ROOT / "inventory-sources/sra-entire-project.xml").read_text())
        duplicate = copy.deepcopy(root.find("EXPERIMENT_PACKAGE"))
        duplicate.find("SAMPLE").set("alias", "unexpected_sample")
        root.append(duplicate)
        with self.assertRaises(ValueError):
            sra_inventory(ET.tostring(root, encoding="unicode"))


if __name__ == "__main__":
    unittest.main()
