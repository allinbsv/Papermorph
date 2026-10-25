"""Language delivery choice must fail closed until the exact release is confirmed."""

import json
import tempfile
import unittest
from pathlib import Path

from delivery_language_gate import check_delivery_choice, main


def style(language=None, artifact=None, confirmed=False, source=None):
    return {"book": {"language": "zh"}, "voice": {"voice": "zh-CN-YunxiNeural"},
            "delivery": {"supported_languages": ["zh", "en"],
                         "selection": {"language": language, "for_artifact": artifact,
                                       "confirmed_by_user": confirmed, "source": source}}}


class DeliveryLanguageGateTests(unittest.TestCase):
    def test_unselected_fails_even_with_default_chinese(self):
        passed, _ = check_delivery_choice(style(), "zh", "ch01-v1")
        self.assertFalse(passed)

    def test_explicit_chinese_approved(self):
        passed, _ = check_delivery_choice(style("zh", "ch01-v1", True, "user said Chinese"), "zh", "ch01-v1")
        self.assertTrue(passed)

    def test_explicit_english_approved_despite_chinese_book_default(self):
        passed, _ = check_delivery_choice(style("en", "ch01-v1", True, "user said English"), "en", "ch01-v1")
        self.assertTrue(passed)

    def test_wrong_language_fails(self):
        passed, _ = check_delivery_choice(style("zh", "ch01-v1", True, "user said Chinese"), "en", "ch01-v1")
        self.assertFalse(passed)

    def test_prior_release_confirmation_cannot_be_reused(self):
        passed, _ = check_delivery_choice(style("zh", "ch01-v1", True, "user said Chinese"), "zh", "ch01-v2")
        self.assertFalse(passed)

    def test_missing_source_fails(self):
        passed, _ = check_delivery_choice(style("en", "ch01-v1", True), "en", "ch01-v1")
        self.assertFalse(passed)

    def test_command_exit_codes(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "style.json"
            path.write_text(json.dumps(style()), encoding="utf-8")
            self.assertEqual(main([str(path), "--language", "zh", "--artifact", "ch01-v1"]), 2)
            path.write_text(json.dumps(style("en", "ch01-v1", True, "user chose English")), encoding="utf-8")
            self.assertEqual(main([str(path), "--language", "en", "--artifact", "ch01-v1"]), 0)

    def test_language_samples_have_same_beat_and_mark_ids(self):
        templates = Path(__file__).resolve().parents[1] / "assets/templates/zh-humanist"
        zh = json.loads((templates / "narration.zh.json").read_text(encoding="utf-8"))
        en = json.loads((templates / "narration.en.json").read_text(encoding="utf-8"))
        self.assertEqual(zh["beats"].keys(), en["beats"].keys())
        import re
        for beat in zh["beats"]:
            self.assertEqual(re.findall(r"\[\[\w+\]\]", zh["beats"][beat]),
                             re.findall(r"\[\[\w+\]\]", en["beats"][beat]))
        self.assertTrue(zh["voice"].startswith("zh-"))
        self.assertTrue(en["voice"].startswith("en-"))


if __name__ == "__main__":
    unittest.main()
