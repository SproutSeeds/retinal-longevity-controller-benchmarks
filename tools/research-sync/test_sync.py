"""Safety checks for export boundaries; no network calls or real Git mutations."""
import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('research_sync', Path(__file__).with_name('sync.py'))
sync = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sync)


class Boundaries(unittest.TestCase):
    def test_private_and_escape_paths_rejected(self):
        for value in ['/etc/passwd', '../outside', 'a/../outside', 'a//b', '.git/config',
                      'a/correspondence/mail.txt', 'a/cloud/receipt.json', 'a/tmp/input', 'a\\b']:
            with self.subTest(value=value), self.assertRaises(ValueError):
                sync.safe_path(value)

    def test_dirty_worktree_stops_before_mutation(self):
        with patch.object(sync, 'run', return_value='?? unrelated.txt'), self.assertRaises(RuntimeError):
            sync.require_clean(Path('.'))

    def test_source_fingerprint_is_order_independent_and_content_sensitive(self):
        self.assertEqual(sync.content_id({'a': b'1', 'b': b'2'}), sync.content_id({'b': b'2', 'a': b'1'}))
        self.assertNotEqual(sync.content_id({'a': b'1'}), sync.content_id({'a': b'2'}))

    def test_independent_public_edit_and_removal_are_blocked(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); (root / 'owned.txt').write_bytes(b'original')
            previous = {'files': {'owned.txt': sync.digest(b'original')}}
            sync.require_owned_outputs(root, previous, '', {'owned.txt'})
            with self.assertRaises(RuntimeError):
                sync.require_owned_outputs(root, previous, '', set())
            (root / 'owned.txt').write_bytes(b'public collaborator edit')
            with self.assertRaises(RuntimeError):
                sync.require_owned_outputs(root, previous, '', {'owned.txt'})


if __name__ == '__main__':
    unittest.main()
