import io
import unittest
import zipfile

from audit import evidence_state,require_xlsx


class SourceAdmissionChecks(unittest.TestCase):
    def test_HTTP_success_empty_body_rejects(self):
        with self.assertRaises(ValueError):require_xlsx(b'')

    def test_HTML_download_page_rejects(self):
        with self.assertRaises(ValueError):require_xlsx(b'<html>Preparing to download</html>')

    def test_generic_ZIP_is_not_a_workbook(self):
        b=io.BytesIO()
        with zipfile.ZipFile(b,'w') as archive:archive.writestr('README.txt','not an Excel workbook')
        with self.assertRaises(ValueError):require_xlsx(b.getvalue())

    def test_retained_mapping_cannot_establish_current_admission(self):
        self.assertEqual(evidence_state(False,100),'INCONCLUSIVE_current_workbook; no_mapping_admission')

    def test_ages_without_keys_cannot_admit(self):
        self.assertEqual(evidence_state(True,0),'no_usable_assignment_keys; no_mapping_admission')

    def test_keys_alone_still_need_context_and_QC(self):
        self.assertEqual(evidence_state(True,10),'candidate_requires_explicit_context_and_QC_join_verification')


if __name__=='__main__':unittest.main()
