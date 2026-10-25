"""Offline/synthetic smoke tests: no voice model, network or paid API."""
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "scripts" / "story_video_gate.py"
spec = importlib.util.spec_from_file_location("story_video_gate", MODULE)
gate = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = gate
spec.loader.exec_module(gate)


def ffmpeg(*args):
    subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-y", *map(str,args)], check=True)


class StoryVideoGateTests(unittest.TestCase):
    def setUp(self):
        self.scratch = tempfile.TemporaryDirectory()
        self.root = Path(self.scratch.name)
        self.audio = self.root / "synthetic.wav"
        ffmpeg("-f", "lavfi", "-i", "sine=frequency=440:sample_rate=48000:duration=3",
               "-ac", "1", "-c:a", "pcm_s16le", self.audio)

    def tearDown(self):
        self.scratch.cleanup()

    def test_split_full_source(self):
        group = [{"source":"synthetic.wav","segments":[
            {"start_s":0,"end_s":1.5,"tempo":0.9},
            {"start_s":1.5,"end_s":None,"tempo":1.1}]}]
        result = gate.source_split_check(group,self.root)
        self.assertEqual(result["source_interval_coverage"],"PASS")
        self.assertEqual(result["status"],"REVIEW")  # metadata alone cannot prove the render

    def test_rendered_trim_duration_catches_output_side_t(self):
        wrong = self.root/"cut_wrong.wav"
        ffmpeg("-i",self.audio,"-filter:a","atempo=0.8",
               "-t","1.0","-c:a","pcm_s16le",wrong)
        group = [{"source":"synthetic.wav","segments":[
            {"start_s":0,"end_s":1.0,"tempo":0.8,"transformed_clip":"cut_wrong.wav"},
            {"start_s":1.0,"end_s":None,"tempo":1.0}]}]
        result = gate.source_split_check(group,self.root)
        self.assertEqual(result["status"],"FAIL")
        self.assertIn("Post-tempo clip",result["reason"])

    def test_split_gap_is_failure(self):
        group = [{"source":"synthetic.wav","segments":[
            {"start_s":0,"end_s":1.5},
            {"start_s":1.6,"end_s":None}]}]
        checked = gate.source_split_check(group,self.root)
        self.assertEqual(checked["status"],"FAIL")
        self.assertIn("gap/overlap",checked["reason"])

    def test_split_tail_is_failure(self):
        group = [{"source":"synthetic.wav","segments":[{"start_s":0,"end_s":2.8}]}]
        self.assertEqual(gate.source_split_check(group,self.root)["status"],"FAIL")

    def test_source_trim_precedes_tempo(self):
        output = self.root/"slow.wav"
        namespace = type("Args",(),{"source":str(self.audio), "start":0.0,
                   "duration":2.0,"tempo":0.8,"output":str(output)})
        gate.trim_audio(namespace)
        duration = float(gate.ffprobe(output)["format"]["duration"])
        self.assertGreater(duration,2.4)  # a wrong output-side -t gives only 2.0
        self.assertLess(duration,2.65)
        with self.assertRaises(FileExistsError):
            gate.trim_audio(namespace)

    def test_srt_out_of_order_rejected(self):
        file = self.root/"bad.srt"
        file.write_text("1\n00:00:01,000 --> 00:00:02,000\nHello\n\n"
                        "2\n00:00:01,500 --> 00:00:02,500\nOverlap\n")
        with self.assertRaisesRegex(ValueError,"Overlapping"):
            gate.parse_srt(file)

    def test_integrated_audit_and_independent_approval(self):
        mobile = self.root/"mobile.mp4"
        master = self.root/"master.mp4"
        ffmpeg("-f","lavfi","-i","color=c=blue:s=1280x720:r=12:d=3",
               "-i",self.audio,"-c:v","libx264","-preset","ultrafast",
               "-pix_fmt","yuv420p","-c:a","aac","-b:a","128k",
               "-shortest",mobile)
        ffmpeg("-i",mobile,"-vf","scale=1920:1080","-c:v","libx264",
               "-preset","ultrafast","-c:a","copy",master)
        srt = self.root/"cues.srt"
        srt.write_text("1\n00:00:00,100 --> 00:00:01,200\nOnce upon a time\n\n"
                       "2\n00:00:01,300 --> 00:00:02,900\nThe end\n")
        first = self.root/"first.wav"
        second = self.root/"second.wav"
        gate.trim_audio(type("Args",(),{"source":str(self.audio),"start":0.0,
                       "duration":1.0,"tempo":1.0,"output":str(first)}))
        gate.trim_audio(type("Args",(),{"source":str(self.audio),"start":1.0,
                       "duration":2.0,"tempo":1.0,"output":str(second)}))
        cfg = {
            "project_id":"synthetic","version":"v0","selected_language":"en",
            "language_selection_evidence_ref":"test-only",
            "duration_range_s":[2.5,3.5],"expected_caption_count":2,
            "files":{"mobile_720p":"mobile.mp4","master_1080p":"master.mp4",
                     "subtitles_srt":"cues.srt"},
            "source_split_groups":[{"source":"synthetic.wav","segments":[
                {"start_s":0.0,"end_s":1.0,"transformed_clip":"first.wav"},
                {"start_s":1.0,"end_s":None,"transformed_clip":"second.wav"}]}],
            "human_evidence":{},"public_release":{"authorized":False}}
        conf = self.root/"project.json"
        conf.write_text(json.dumps(cfg))
        report = gate.audit(conf)
        self.assertEqual(report["technical_gate"],"PASS",report)
        self.assertEqual(report["human_gate"],"PENDING")
        self.assertEqual(report["public_release_gate"],"HOLD")
        self.assertTrue(report["checks"]["cross_resolution_audio"]["same_encoded_audio_bitstream"])
        self.assertEqual(report["checks"]["caption_audio_activity"]["cue_count_with_signal"],2)
        # A 720p acceptance must not carry across resolutions automatically.
        cfg["human_evidence"] = {"mobile_720p":{"status":"PASS","evidence_ref":"user-test",
                                   "sha256":gate.sha256_file(mobile)}}
        conf.write_text(json.dumps(cfg))
        self.assertEqual(gate.audit(conf)["human_gate"],"PENDING")
        # Wrong SHA never binds the approval even when the evidence text says PASS.
        cfg["human_evidence"]["master_1080p"] = {"status":"PASS",
                                                    "evidence_ref":"user-test",
                                                    "sha256":"incorrect"}
        conf.write_text(json.dumps(cfg))
        self.assertEqual(gate.audit(conf)["checks"]["human_approvals"]["master_1080p"]["status"],"PENDING")


if __name__ == "__main__":
    unittest.main()
