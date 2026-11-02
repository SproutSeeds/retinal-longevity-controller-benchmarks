import io
import unittest
import zipfile

from recover import validate_payload


def workbook_zip():
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, 'w', compression=zipfile.ZIP_STORED) as archive:
        archive.writestr('[Content_Types].xml', '<Types/>')
        archive.writestr('xl/workbook.xml', '<workbook>fixture</workbook>')
        archive.writestr('xl/_rels/workbook.xml.rels', '<Relationships/>')
    return buffer.getvalue()


class RecoveryChecks(unittest.TestCase):
    def test_complete_response_structure_and_CRC(self):
        self.assertEqual(validate_payload(200, workbook_zip(), 'xlsx')['full_CRC'], 'PASS')

    def test_HTTP_failure_cannot_admit_even_complete_workbook(self):
        for status in [403, 404, 206]:
            with self.subTest(status=status), self.assertRaises(ValueError):
                validate_payload(status, workbook_zip(), 'xlsx')

    def test_empty_HTTP_success_rejects(self):
        with self.assertRaises(ValueError):
            validate_payload(200, b'', 'xlsx')

    def test_HTML_HTTP_success_rejects(self):
        with self.assertRaises(ValueError):
            validate_payload(200, b'<html>Checking your browser</html>', 'xlsx')

    def test_generic_ZIP_rejects(self):
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, 'w') as archive:
            archive.writestr('README.txt', 'not a workbook')
        with self.assertRaises(ValueError):
            validate_payload(200, buffer.getvalue(), 'xlsx')

    def test_corrupted_member_rejects(self):
        body = bytearray(workbook_zip())
        body[body.index(b'fixture')] ^= 1
        with self.assertRaises(ValueError):
            validate_payload(200, bytes(body), 'xlsx')

    def test_expanded_budget_rejects(self):
        with self.assertRaises(ValueError):
            validate_payload(200, workbook_zip(), 'xlsx', expanded_limit=1)


if __name__ == '__main__':
    unittest.main()
