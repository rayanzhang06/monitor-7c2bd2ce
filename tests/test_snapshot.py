import copy
import importlib.util
import json
import unittest
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('validator', ROOT / 'validate.py')
validator = importlib.util.module_from_spec(spec)
spec.loader.exec_module(validator)


class PublicationTests(unittest.TestCase):
    def setUp(self):
        self.snapshot = json.loads((ROOT / 'site/snapshot.json').read_text())
        self.calendar = json.loads((ROOT / 'site/calendar.json').read_text())
        self.now = datetime.fromisoformat(self.snapshot['publication']['published_at'])

    def test_actual_publication_is_valid(self):
        validator.validate(self.snapshot, self.calendar, self.now)

    def test_authority_failure_is_rejected(self):
        self.snapshot['authority']['status'] = 'failed'
        with self.assertRaisesRegex(ValueError, 'authority'):
            validator.validate(self.snapshot, self.calendar, self.now)

    def test_old_data_cannot_be_relabelled_daily(self):
        self.snapshot['publication']['mode'] = 'daily'
        with self.assertRaises(ValueError):
            validator.validate(self.snapshot, self.calendar, datetime.fromisoformat('2099-01-01T00:00:00+00:00'))

    def test_account_inconsistency_is_rejected(self):
        self.snapshot['account']['total_value'] += 100
        with self.assertRaisesRegex(ValueError, 'inconsistent holdings'):
            validator.validate(self.snapshot, self.calendar, self.now)

    def test_plan_is_rejected(self):
        self.snapshot['account']['plan_id'] = 'must-not-publish'
        with self.assertRaisesRegex(ValueError, 'account plan'):
            validator.validate(self.snapshot, self.calendar, self.now)

    def test_private_metadata_is_rejected(self):
        self.snapshot['source'] = '/Users/example/private-file'
        with self.assertRaisesRegex(ValueError, 'private metadata'):
            validator.validate(self.snapshot, self.calendar, self.now)

    def test_overlay_misalignment_is_rejected(self):
        self.snapshot['performance']['assets']['gold']['horizons']['1Y']['points'][0]['date'] = '1900-01-01'
        with self.assertRaisesRegex(ValueError, 'overlay dates'):
            validator.validate(self.snapshot, self.calendar, self.now)

    def test_current_model_accepts_explicit_stale_holdings_without_comparison(self):
        self.snapshot['publication']['mode'] = 'daily'
        self.snapshot['account']['status'] = 'stale'
        self.snapshot['account']['max_abs_deviation_pct'] = None
        for row in self.snapshot['account']['rows']:
            row.update(model_amount=None, model_weight_pct=None, deviation_pp=None)
        self.snapshot['account']['valuation_date'] = '2026-09-01'
        self.now = datetime.fromisoformat(self.snapshot['freshness']['data_end']+'T08:00:00+00:00')
        validator.validate(self.snapshot, self.calendar, self.now)

    def test_model_only_publication_is_valid(self):
        self.snapshot['publication']['mode'] = 'daily'
        self.snapshot['account'] = None
        self.snapshot['visibility'] = 'model_only'
        self.now = datetime.fromisoformat(self.snapshot['freshness']['data_end']+'T08:00:00+00:00')
        validator.validate(self.snapshot, self.calendar, self.now)


if __name__ == '__main__':
    unittest.main()
