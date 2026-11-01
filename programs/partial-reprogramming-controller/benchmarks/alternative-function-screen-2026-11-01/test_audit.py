"""Synthetic rejection tests; these fixtures are not biological observations."""
import gzip
from pathlib import Path
import tempfile
import unittest

from audit import conflicts, geo_samples, inspect_matrix, target_scope, unique


def fixture():
    g = {"cell_line": "HC1", "unique_variable_name": "HC1_sp2_Normal_Control_ox21_p6",
         "inhouse_cell_line_name": "hFB12", "study_part": "2", "rnaseq_sampleid": "21",
         "percent_oxygen": "21", "passage": "6", "treatments": "Control", "Sex": "male",
         "donor_age": "18", "replicate_line": "1", "date_of_passage": "2018-08-29",
         "time_of_passage": "9:00", "days_grown_udays": "21.20833333"}
    a = {"Cell_line": "HC1", "Unique_variable_name": g["unique_variable_name"],
         "Cell_line_inhouse": "hFB12", "Study_part": "2", "RNAseq_sampleID": "21",
         "Percent_oxygen": "21", "Passage": "6", "Treatments": "Control", "Sex": "male",
         "Donor_age": "18", "Replicate_line": "1", "Date_of_Passage": "8/29/18",
         "Time_of_Passage": "09:00:00", "Days_grown_Udays": "21.21"}
    return {"gsm": "SYNTHETIC_GSM", "organism": "Homo sapiens",
            "description": "Sample_21", "attributes": g}, a


class AuditTests(unittest.TestCase):
    def test_exact_ids_and_documented_time_precision_pass(self):
        g, a = fixture()
        self.assertEqual(conflicts(g, a), [])
        self.assertTrue(target_scope(g, a))

    def test_donor_and_rna_identity_cannot_be_replaced_by_row_position(self):
        g, a = fixture()
        a["Cell_line"] = "HC2"
        a["RNAseq_sampleID"] = "22"
        self.assertIn("cell_line:different", conflicts(g, a))
        self.assertIn("rnaseq_sampleid:different", conflicts(g, a))

    def test_adjacent_date_and_clock_time_do_not_form_a_match(self):
        g, a = fixture()
        a["Date_of_Passage"] = "8/30/18"
        a["Time_of_Passage"] = "09:01:00"
        self.assertIn("collection_date:different", conflicts(g, a))
        self.assertIn("collection_time:different", conflicts(g, a))

    def test_growth_time_outside_source_rounding_is_rejected(self):
        g, a = fixture()
        a["Days_grown_Udays"] = "21.22"
        self.assertIn("days_grown:incompatible_source_precision", conflicts(g, a))

    def test_replicate_codes_are_not_silently_reconciled(self):
        g, a = fixture()
        a["Replicate_line"] = "0"
        self.assertIn("replicate_line:different", conflicts(g, a))

    def test_species_age_treatment_phase_and_oxygen_stay_scoped(self):
        for key, replacement in [("donor_age", "0"), ("study_part", "3"),
                                 ("treatments", "Oligo"), ("percent_oxygen", "3")]:
            g, a = fixture()
            g["attributes"][key] = replacement
            self.assertFalse(target_scope(g, a))
        g, a = fixture()
        g["organism"] = "Mus musculus"
        self.assertIn("species:outside_scope", conflicts(g, a))

    def test_missing_technical_reference_context_is_explicit(self):
        g, a = fixture()
        del g["attributes"]["cell_line"]
        del g["attributes"]["date_of_passage"]
        self.assertIn("cell_line:missing", conflicts(g, a))
        self.assertIn("collection_date_or_time:missing", conflicts(g, a))
        self.assertFalse(target_scope(g, a))

    def test_duplicate_study_ids_are_rejected(self):
        with self.assertRaises(ValueError):
            unique([{"Sample": "21"}, {"Sample": "21"}], "Sample")

    def test_matrix_column_order_is_not_an_identity_rule(self):
        with tempfile.TemporaryDirectory() as temp:
            p = Path(temp) / "matrix.csv.gz"
            with gzip.open(p, "wt") as h:
                h.write(',Sample_2,Sample_1\nGENE_A,-2,3.25\nGENE_B,0,1\n')
            q = inspect_matrix(p, ["Sample_1", "Sample_2"])
            self.assertEqual(q["finite_expression_values"], 4)

    def test_duplicate_columns_genes_and_nonfinite_values_fail(self):
        invalid = [',Sample_1,Sample_1\nA,1,2\n',
                   ',Sample_1,Sample_2\nA,1,2\nA,3,4\n',
                   ',Sample_1,Sample_2\nA,NaN,2\n',
                   ',Sample_1,Sample_2\n,1,2\n']
        with tempfile.TemporaryDirectory() as temp:
            p = Path(temp) / "matrix.csv.gz"
            for content in invalid:
                with gzip.open(p, "wt") as h:
                    h.write(content)
                with self.assertRaises(ValueError):
                    inspect_matrix(p, ["Sample_1", "Sample_2"])

    def test_geo_duplicate_rna_ids_fail_before_joining(self):
        with tempfile.TemporaryDirectory() as temp:
            p = Path(temp) / "family.txt"
            p.write_text('^SAMPLE = SYNTH_A\n!Sample_characteristics_ch1 = rnaseq_sampleid: 1\n'
                         '^SAMPLE = SYNTH_B\n!Sample_characteristics_ch1 = rnaseq_sampleid: 1\n')
            with self.assertRaises(ValueError):
                geo_samples(p)


if __name__ == "__main__":
    unittest.main()
