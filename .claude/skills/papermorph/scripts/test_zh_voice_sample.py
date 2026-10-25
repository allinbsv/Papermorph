"""Cheap, offline tests: never load weights or produce synthetic speech."""

import json
import tempfile
import unittest
from pathlib import Path

from zh_voice_sample import audition_text, main


class ChineseVoiceSampleTests(unittest.TestCase):
    def test_json_beats_strip_marks_and_keep_chinese(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "narration.zh.json"
            path.write_text(json.dumps({"beats": {"b1": "[[one]]真诚地说。",
                                                      "b2": {"text": "[[two]]慢一点。"}}}), encoding="utf-8")
            self.assertEqual(audition_text(path), "真诚地说。\n慢一点。")

    def test_plain_text(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "sample.txt"
            path.write_text("  说得明白。  ", encoding="utf-8")
            self.assertEqual(audition_text(path), "说得明白。")

    def test_empty_beats_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "narration.zh.json"
            path.write_text('{"beats":{}}', encoding="utf-8")
            with self.assertRaises(ValueError):
                audition_text(path)

    def test_dry_run_never_creates_audio(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "sample.txt"
            path.write_text("生活里的一件小事。", encoding="utf-8")
            output = Path(tmp) / "preview.wav"
            self.assertEqual(main(["--text-file", str(path), "--output", str(output), "--dry-run"]), 0)
            self.assertFalse(output.exists())


if __name__ == "__main__":
    unittest.main()
