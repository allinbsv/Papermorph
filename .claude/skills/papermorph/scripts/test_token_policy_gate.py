"""Preflight must not treat a configured API key or previous budget example as consent."""

import json
import tempfile
import unittest
from pathlib import Path

from token_policy_gate import check_token_policy, main


def style(authorized=False, scope=None, source=None, cap=None):
    return {"token_policy": {
        "access_mode": "existing_subscriptions_only",
        "metered_api": {"authorized": authorized, "approved_scope": scope,
                        "approved_by_user_source": source, "budget_usd": cap},
        "monthly_token_ceiling": None,
    }}


class TokenPolicyGateTests(unittest.TestCase):
    def test_subscription_allowed_with_unknown_quota(self):
        passed, _ = check_token_policy(style(), "subscription")
        self.assertTrue(passed)

    def test_missing_policy_fails_closed(self):
        passed, _ = check_token_policy({}, "metered-api", "ch01-images-v1")
        self.assertFalse(passed)

    def test_default_paid_api_blocked(self):
        passed, _ = check_token_policy(style(), "metered-api", "ch01-images-v1")
        self.assertFalse(passed)

    def test_user_approved_scope_and_cap_allowed_by_configuration(self):
        approved = style(True, "ch01-images-v1", "user explicitly approved ch01 images", 8.0)
        passed, _ = check_token_policy(approved, "metered-api", "ch01-images-v1")
        self.assertTrue(passed)

    def test_not_other_scope(self):
        approved = style(True, "ch01-images-v1", "user approved images", 8.0)
        passed, _ = check_token_policy(approved, "metered-api", "ch01-video-v1")
        self.assertFalse(passed)

    def test_unknown_or_invalid_cap_rejected(self):
        for cap in (None, 0, -10, "80", float("inf"), True):
            with self.subTest(cap=cap):
                approved = style(True, "ch01-images-v1", "user approved", cap)
                self.assertFalse(check_token_policy(approved, "metered-api", "ch01-images-v1")[0])

    def test_no_documented_user_approval_rejected(self):
        approved = style(True, "ch01-images-v1", None, 8.0)
        self.assertFalse(check_token_policy(approved, "metered-api", "ch01-images-v1")[0])

    def test_cli_blocks_unapproved_paid_request(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "style.json"
            p.write_text(json.dumps(style()), encoding="utf-8")
            self.assertEqual(main([str(p), "--mode", "metered-api", "--scope", "ch01-images-v1"]), 2)
            self.assertEqual(main([str(p), "--mode", "subscription"]), 0)


if __name__ == "__main__":
    unittest.main()
