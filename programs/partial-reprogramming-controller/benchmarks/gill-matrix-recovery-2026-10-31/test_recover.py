import gzip
import hashlib
import io
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import recover


ANNOTATIONS = ['Probe', 'Chromosome', 'Start', 'End', 'Probe Strand', 'Feature', 'ID',
               'Description', 'Feature Strand', 'Type', 'Feature Orientation', 'Distance']
CONTRACT = {'annotation_columns': ANNOTATIONS,
            'locus_key_fields': ['Chromosome', 'Start', 'End', 'Probe Strand', 'ID'],
            'sources': [{'source_id': 'left'}, {'source_id': 'right'}],
            'provisional_title_aliases': {'a b': 'a_b'}}


def feature(probe, start, gene, values):
    return [probe, '1', str(start), str(start + 1), '+', probe, gene, '', '+', 'gene', 'Name match', '0', *values]


def matrix(labels, rows):
    text = '\t'.join([*ANNOTATIONS, *labels]) + '\n'
    text += ''.join('\t'.join(row) + '\n' for row in rows)
    return recover.read_matrix(io.StringIO(text), CONTRACT)


def source(data):
    return {'filename': 'fixture.tsv.gz', 'bytes': len(data),
            'sha256': hashlib.sha256(data).hexdigest(), 'url': 'https://example.org/fixture.tsv.gz'}


class RecoveryTests(unittest.TestCase):
    def test_reordered_rows_preserve_the_values_of_each_locus(self):
        left = matrix(['L'], [feature('A', 1, 'ENSA', ['-3.500']), feature('B', 2, 'ENSB', ['2.0'])])
        right = matrix(['R'], [feature('B', 2, 'ENSB', ['200.00']), feature('A', 1, 'ENSA', ['-5.50'])])
        actual = [(key[-1], values) for key, _, values in recover.aligned_rows([left, right])]
        self.assertEqual(actual, [('ENSA', ['-3.500', '-5.50']), ('ENSB', ['2.0', '200.00'])])

    def test_repeated_gene_ids_at_distinct_loci_remain_distinct(self):
        left = matrix(['L'], [feature('A', 1, 'SAME', ['1']), feature('A', 2, 'SAME', ['2'])])
        right = matrix(['R'], [feature('A', 2, 'SAME', ['20']), feature('A', 1, 'SAME', ['10'])])
        rows = list(recover.aligned_rows([left, right]))
        self.assertEqual(len(rows), 2)
        self.assertEqual([row[2] for row in rows], [['1', '10'], ['2', '20']])

    def test_blank_gene_ids_keep_their_locus_identity(self):
        actual = matrix(['L'], [feature('A', 1, '', ['1']), feature('B', 2, '', ['2'])])
        self.assertEqual(len(actual['rows']), 2)

    def test_duplicate_compound_key_fails(self):
        with self.assertRaisesRegex(ValueError, 'Duplicate compound locus'):
            matrix(['L'], [feature('A', 1, 'ENSA', ['1']), feature('A', 1, 'ENSA', ['9'])])

    def test_equal_row_counts_do_not_hide_different_loci(self):
        left = matrix(['L'], [feature('A', 1, 'ENSA', ['1'])])
        right = matrix(['R'], [feature('B', 2, 'ENSB', ['2'])])
        with self.assertRaisesRegex(ValueError, 'locus sets differ'):
            list(recover.aligned_rows([left, right]))

    def test_matching_coordinates_do_not_hide_annotation_conflicts(self):
        left = matrix(['L'], [feature('A', 1, 'ENSA', ['1'])])
        right = matrix(['R'], [feature('RENAMED', 1, 'ENSA', ['2'])])
        with self.assertRaisesRegex(ValueError, 'annotations disagree'):
            list(recover.aligned_rows([left, right]))

    def test_malformed_or_nonfinite_cells_fail(self):
        for value in ['nan', 'inf', '-inf', 'missing']:
            with self.subTest(value=value), self.assertRaises(ValueError):
                matrix(['L'], [feature('A', 1, 'ENSA', [value])])
        with self.assertRaisesRegex(ValueError, 'Ragged'):
            matrix(['L', 'R'], [feature('A', 1, 'ENSA', ['1'])])

    def test_duplicate_sample_columns_fail(self):
        with self.assertRaisesRegex(ValueError, 'duplicate'):
            matrix(['L', 'L'], [feature('A', 1, 'ENSA', ['1', '2'])])

    def test_title_normalization_cannot_reuse_a_sample(self):
        data = matrix(['a_b', 'a b'], [feature('A', 1, 'ENSA', ['1', '2'])])
        metadata = [{'title': 'a_b', 'sample_id': 'GSM1'}]
        with self.assertRaisesRegex(ValueError, 'Reused sample'):
            recover.match_columns([data], metadata, CONTRACT)

    def test_provisional_title_match_cannot_supply_a_frozen_arm(self):
        data = matrix(['a b', 'exact'], [feature('A', 1, 'ENSA', ['1', '2'])])
        metadata = [{'title': 'a_b', 'sample_id': 'GSM1'}, {'title': 'exact', 'sample_id': 'GSM2'}]
        matches = recover.match_columns([data], metadata, CONTRACT)
        pair = {'pair_id': 'P', 'control_rna_id': 'GSM1', 'treated_rna_id': 'GSM2'}
        with self.assertRaisesRegex(ValueError, 'two exact RNA'):
            recover.contrast_coverage(matches, [pair])

    def test_unknown_titles_fail_without_a_guess(self):
        data = matrix(['unmatched'], [feature('A', 1, 'ENSA', ['1'])])
        with self.assertRaisesRegex(ValueError, 'Unrecognized'):
            recover.match_columns([data], [{'title': 'other', 'sample_id': 'GSM1'}], CONTRACT)

    def test_source_validation_rejects_empty_truncated_and_wrong_format(self):
        valid = gzip.compress(b'original source', mtime=0)
        for payload in [b'', valid[:-3]]:
            with self.subTest(length=len(payload)), self.assertRaisesRegex(ValueError, 'byte length'):
                recover.validate_payload(payload, source(valid))
        wrong = b'<html>error</html>'
        with self.assertRaises(gzip.BadGzipFile):
            recover.validate_payload(wrong, source(wrong))
        changed = bytearray(valid)
        changed[-8] ^= 1
        with self.assertRaisesRegex(ValueError, 'hash differs'):
            recover.validate_payload(bytes(changed), source(valid))

    def test_failed_transfer_never_creates_an_accepted_file(self):
        valid = gzip.compress(b'original source', mtime=0)
        response = unittest.mock.MagicMock()
        response.__enter__.return_value.status = 200
        response.__enter__.return_value.read.return_value = b''
        with tempfile.TemporaryDirectory() as folder:
            cache = Path(folder)
            with patch('recover.urllib.request.urlopen', return_value=response):
                with self.assertRaisesRegex(ValueError, 'byte length'):
                    recover.download(source(valid), cache)
            self.assertEqual(list(cache.iterdir()), [])

    def test_changed_existing_source_is_preserved_without_a_network_retry(self):
        valid = gzip.compress(b'original source', mtime=0)
        with tempfile.TemporaryDirectory() as folder:
            cache = Path(folder)
            path = cache / 'fixture.tsv.gz'
            path.write_bytes(b'existing evidence')
            with patch('recover.urllib.request.urlopen') as request:
                with self.assertRaises(ValueError):
                    recover.download(source(valid), cache)
                request.assert_not_called()
            self.assertEqual(path.read_bytes(), b'existing evidence')


if __name__ == '__main__':
    unittest.main(verbosity=2)
