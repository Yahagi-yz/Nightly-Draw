import copy
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from validate import validate_card, validate_project
import bootstrap_github


class ContractTests(unittest.TestCase):
    def setUp(self):
        self.card = json.loads((ROOT / 'content/cards/story-lion-and-mouse.json').read_text(encoding='utf-8'))

    def test_all_samples_validate(self):
        self.assertEqual(validate_project(ROOT), 3)

    def test_three_categories_present(self):
        cards = [json.loads(p.read_text(encoding='utf-8')) for p in (ROOT / 'content/cards').glob('*.json')]
        self.assertEqual({c['category'] for c in cards}, {'world_story', 'person_story', 'historic_city'})
        self.assertTrue(all(c['release_status'] == 'sample_only' for c in cards))

    def test_no_sources_rejected(self):
        self.card['sources'] = []
        with self.assertRaises(ValueError):
            validate_card(self.card)

    def test_unknown_field_rejected(self):
        self.card['invented_status'] = 'ready'
        with self.assertRaises(ValueError):
            validate_card(self.card)

    def test_fake_image_card_rejected(self):
        self.card['format'] = 'image'
        with self.assertRaises(ValueError):
            validate_card(self.card)

    def test_unreviewed_publication_rejected(self):
        self.card['release_status'] = 'published'
        with self.assertRaises(ValueError):
            validate_card(self.card)

    def test_credentials_in_source_rejected(self):
        self.card['sources'][0]['url'] = 'https://secret@example.com/story'
        with self.assertRaises(ValueError):
            validate_card(self.card)

    def test_duplicate_tags_rejected(self):
        self.card['related_tags'] = ['世界', '世界']
        with self.assertRaises(ValueError):
            validate_card(self.card)

    def test_invalid_access_date_rejected(self):
        self.card['sources'][0]['accessed_on'] = '2026-02-30'
        with self.assertRaises(ValueError):
            validate_card(self.card)

    def test_schedule_not_falsely_enabled(self):
        schedule = json.loads((ROOT / 'config/schedule.json').read_text(encoding='utf-8'))
        self.assertFalse(schedule['enabled'])
        self.assertIsNone(schedule['task_id'])
        self.assertEqual(schedule['timezone'], 'Asia/Shanghai')
        self.assertEqual(schedule['local_time'], '22:00')

    def test_bootstrap_dry_run_no_external_commands(self):
        with patch.object(bootstrap_github, 'run', side_effect=AssertionError('must not run')):
            self.assertEqual(bootstrap_github.main([]), 0)

    def test_dry_run_does_not_create_git(self):
        # Run in an isolated extraction, not the real checkout (which has .git).
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / 'scripts').mkdir()
            script = root / 'scripts/bootstrap_github.py'
            script.write_bytes((ROOT / 'scripts/bootstrap_github.py').read_bytes())
            result = subprocess.run([sys.executable, str(script)],
                                    capture_output=True, text=True)
            self.assertEqual(result.returncode, 0)
            self.assertFalse((root / '.git').exists())

    def test_dry_run_preserves_existing_checkout(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / 'scripts').mkdir()
            (root / '.git').mkdir()
            marker = root / '.git/HEAD'
            marker.write_text('ref: refs/heads/main\n', encoding='utf-8')
            script = root / 'scripts/bootstrap_github.py'
            script.write_bytes((ROOT / 'scripts/bootstrap_github.py').read_bytes())
            before = {str(p.relative_to(root)): p.read_bytes()
                      for p in root.rglob('*') if p.is_file()}
            result = subprocess.run([sys.executable, str(script)],
                                    capture_output=True, text=True)
            after = {str(p.relative_to(root)): p.read_bytes()
                     for p in root.rglob('*') if p.is_file()}
            self.assertEqual(result.returncode, 0)
            self.assertEqual(before, after)


if __name__ == '__main__':
    unittest.main()
