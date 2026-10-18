"""Meaningful extraction and identity-failure regression tests (synthetic data)."""
import copy
import tempfile
import unittest
import zipfile
from pathlib import Path
from extract_reference import exact_unique_lookup, join_reference, rows_from_sheet
from xlsx_cells import read_workbook


class ReferenceJoinTests(unittest.TestCase):
    def setUp(self):
        self.source = {'values': {'SampleID': 'S1', 'Line': 'DonorA', 'Line_age': 55,
                                 'Passage': 9, 'Gene': 'NTg', 'Dox': 0}}
        self.meta = {'library': 'S1', 'donor_or_line': 'DonorA', 'age_years': 55,
                     'passage': 9, 'genotype': 'NTg', 'treatment': 'NT',
                     'matrix_column': 'S1', 'matrix_column_present': True}

    def check(self, expected, meta=None, source=None):
        lookup = exact_unique_lookup([self.meta if meta is None else meta], 'library')
        self.assertEqual(join_reference(self.source if source is None else source, lookup)['status'], expected)

    def test_literal_ntg_must_not_be_overwritten_by_alias(self):
        self.check('verified_exact_library_and_metadata')

    def test_wt_control_alias(self):
        self.meta['genotype'] = 'WT'
        self.check('verified_exact_library_and_metadata')

    def test_bfp_alias_and_explicit_dose(self):
        self.source['values'].update(Gene='BFP', Dox=2000)
        self.meta.update(genotype='mTagBFP2', treatment='Dox_2000ng/mL, 3d-ON')
        self.check('verified_exact_library_and_metadata')

    def test_duplicate_key_rejected(self):
        lookup = exact_unique_lookup([self.meta, copy.deepcopy(self.meta)], 'library')
        self.assertEqual(join_reference(self.source, lookup)['status'], 'duplicate_library_identifier')

    def test_near_match_id_rejected(self):
        self.meta['library'] = 'S01'
        self.check('missing_library_identifier')

    def test_missing_id_is_not_group_join(self):
        del self.source['values']['SampleID']
        self.check('no_library_identifier')

    def test_recycled_id_with_wrong_donor_rejected(self):
        self.meta['donor_or_line'] = 'OtherDonor'
        self.check('identifier_only_or_metadata_conflict')

    def test_wrong_age_rejected(self):
        self.meta['age_years'] = 56
        self.check('identifier_only_or_metadata_conflict')

    def test_wrong_passage_rejected(self):
        self.meta['passage'] = 10
        self.check('identifier_only_or_metadata_conflict')

    def test_unknown_dose_not_zero(self):
        self.meta['treatment'] = ''
        self.check('identifier_only_or_metadata_conflict')

    def test_wrong_construct_rejected(self):
        self.meta['genotype'] = 'SRSF1'
        self.check('identifier_only_or_metadata_conflict')

    def test_missing_matrix_column_rejected(self):
        self.meta['matrix_column_present'] = False
        self.check('identifier_only_or_metadata_conflict')


class WorkbookTests(unittest.TestCase):
    def fixture(self, sheet):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        path = Path(temp.name) / 'source.xlsx'
        with zipfile.ZipFile(path, 'w') as archive:
            archive.writestr('xl/workbook.xml', '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><sheets><sheet name="refs" r:id="r1"/></sheets></workbook>')
            archive.writestr('xl/_rels/workbook.xml.rels', '<Relationships><Relationship Id="r1" Target="worksheets/sheet1.xml"/></Relationships>')
            archive.writestr('xl/sharedStrings.xml', '<sst><si><t>SampleID</t></si><si><r><t>Predicted</t></r><r><t>_age</t></r></si></sst>')
            archive.writestr('xl/worksheets/sheet1.xml', '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><dimension ref="A1:C2"/><sheetData>' + sheet + '</sheetData></worksheet>')
        return path

    def test_shared_rich_and_inline_strings_and_coordinates(self):
        path = self.fixture('<row r="1"><c r="A1" t="s"><v>0</v></c><c r="B1" t="s"><v>1</v></c></row><row r="2"><c r="A2" t="inlineStr"><is><t>S1</t></is></c><c r="B2"><v>42.5</v></c></row>')
        sheet = read_workbook(path)[0]
        row = rows_from_sheet(sheet, 1)[0]
        self.assertEqual(row['values'], {'SampleID': 'S1', 'Predicted_age': 42.5})
        self.assertEqual(row['coordinates']['Predicted_age'], 'B2')

    def test_zero_and_blank_remain_distinct(self):
        path = self.fixture('<row r="2"><c r="A2"><v>0</v></c><c r="B2"/></row>')
        cells = read_workbook(path)[0]['cells']
        self.assertEqual(cells[0]['value'], 0)
        self.assertIsNone(cells[1]['value'])

    def test_formula_is_not_executed_and_cache_is_separate(self):
        path = self.fixture('<row r="2"><c r="A2"><f>1+1</f><v>99</v></c><c r="B2"><f>1/0</f></c></row>')
        cells = read_workbook(path)[0]['cells']
        self.assertEqual(cells[0]['formula'], '1+1')
        self.assertEqual(cells[0]['value'], 99)
        self.assertIsNone(cells[1]['value'])

    def test_duplicate_header_is_rejected(self):
        sheet = {'sheet': 'refs', 'cells': [{'cell': 'A1', 'value': 'SampleID'}, {'cell': 'B1', 'value': 'SampleID'}]}
        with self.assertRaises(ValueError):
            rows_from_sheet(sheet, 1)


if __name__ == '__main__':
    unittest.main()
