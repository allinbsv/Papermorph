"""No-network regression checks for Chinese narration helpers."""

import importlib.util
import unittest
from pathlib import Path


HERE = Path(__file__).parent


def load_script(name):
    spec = importlib.util.spec_from_file_location(name, HERE / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


review = load_script("zh_review")
tts = load_script("tts")


class ChineseReviewTests(unittest.TestCase):
    def test_valid_mandarin_narration(self):
        spec = {"voice": "zh-CN-YunxiNeural", "beats": {"open": "[[lamp]]夜里，一盏灯忽然灭了。"}}
        errors, warnings = review.analyze(spec, {"book": {"language": "zh-CN"}})
        self.assertEqual(errors, [])
        self.assertEqual(warnings, [])

    def test_wrong_book_language_and_voice(self):
        spec = {"voice": "en-GB-RyanNeural", "beats": {"open": "The light is off."}}
        errors, _ = review.analyze(spec, {"book": {"language": "en"}})
        self.assertTrue(any("Chinese book" in e for e in errors))
        self.assertTrue(any("not Chinese" in e for e in errors))

    def test_cliche_is_a_review_not_a_failure(self):
        spec = {"voice": "zh-CN-YunxiNeural", "beats": {"open": "众所周知，灯可能会熄灭。"}}
        errors, warnings = review.analyze(spec)
        self.assertEqual(errors, [])
        self.assertTrue(any("众所周知" in w for w in warnings))

    def test_foreign_dialogue_requires_chinese_subtitle(self):
        spec = {"voices": {"en": {"voice": "en-US-AriaNeural"}}, "beats": {
            "a": {"speaker": "en", "text": "Hello!", "sub": "你好！"}}}
        self.assertEqual(review.analyze(spec)[0], [])

    def test_reject_broken_mark_and_unknown_speaker(self):
        spec = {"voice": "zh-CN-YunxiNeural", "beats": {
            "a": "[[broken]你好。", "b": {"speaker": "missing", "text": "你好。"}}}
        errors, _ = review.analyze(spec)
        self.assertEqual(len(errors), 2)

    def test_regional_voices_do_not_force_subtitles(self):
        self.assertFalse(tts.is_foreign_voice("zh-CN-YunxiNeural", "narration.zh.json"))
        self.assertFalse(tts.is_foreign_voice("zh-TW-HsiaoChenNeural", "narration.zh-CN.json"))
        self.assertTrue(tts.is_foreign_voice("en-US-AriaNeural", "narration.zh-CN.json"))


if __name__ == "__main__":
    unittest.main()
