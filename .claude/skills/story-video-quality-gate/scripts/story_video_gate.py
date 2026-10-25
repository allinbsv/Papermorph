#!/usr/bin/env python3
"""Offline QA for narrated story video; signal detection is NOT word recognition."""

import argparse
import array
import hashlib
import json
import math
import re
import shutil
import subprocess
from pathlib import Path

SRT_TIME = re.compile(r"^(\d\d):(\d\d):(\d\d)[,.](\d\d\d)\s*-->\s*(\d\d):(\d\d):(\d\d)[,.](\d\d\d)")
SILENCE = re.compile(r"silence_start:\s*([\d.]+)")


def command(args, *, check=True):
    return subprocess.run(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=check)


def ffprobe(path):
    data = command(["ffprobe", "-v", "error", "-show_streams", "-show_format",
                    "-of", "json", str(path)])
    return json.loads(data.stdout)


def sha256_file(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def audio_bitstream_sha256(path):
    data = command(["ffmpeg", "-nostdin", "-hide_banner", "-loglevel", "error",
                    "-i", str(path), "-map", "0:a:0", "-c:a", "copy",
                    "-f", "hash", "-hash", "SHA256", "-"])
    match = re.search(rb"SHA256=([0-9a-fA-F]{64})", data.stdout)
    if not match:
        raise ValueError("Audio stream hash is unavailable")
    return match.group(1).decode("ascii").lower()


def parse_srt(path):
    content = Path(path).read_text(encoding="utf-8-sig").strip()
    cues = []
    for block in re.split(r"\r?\n\s*\r?\n", content):
        lines = block.splitlines()
        if not lines:
            continue
        index = lines[0].strip()
        if len(lines) < 3 or not index.isdecimal():
            raise ValueError(f"Malformed SRT block starting {index[:30]!r}")
        match = SRT_TIME.match(lines[1])
        if not match:
            raise ValueError(f"Bad SRT timestamp at cue {index}")
        v = [int(n) for n in match.groups()]
        start = v[0]*3600 + v[1]*60 + v[2] + v[3]/1000
        end = v[4]*3600 + v[5]*60 + v[6] + v[7]/1000
        caption = "\n".join(lines[2:]).strip()
        if not caption:
            raise ValueError(f"Empty text at cue {index}")
        cues.append({"index": int(index), "start": start, "end": end, "text": caption})
    if not cues:
        raise ValueError("No SRT cues")
    for i, cue in enumerate(cues):
        if cue["index"] != i+1 or cue["end"] <= cue["start"] or cue["start"] < 0:
            raise ValueError(f"Non-sequential or invalid cue {cue['index']}")
        if i and cue["start"] < cues[i-1]["end"]-0.001:
            raise ValueError(f"Overlapping cue {cue['index']}")
    return cues


def source_split_check(groups, basedir):
    if not groups:
        return {"status": "NOT_TESTED", "reason": "No source split groups supplied"}
    checked = []
    unproven = []
    for group in groups:
        file = (basedir / group["source"]).resolve()
        if not file.is_file():
            return {"status": "UNKNOWN", "reason": f"Source file not accessible: {group['source']}"}
        total = float(ffprobe(file)["format"]["duration"])
        segments = group["segments"]
        if not segments:
            return {"status": "FAIL", "reason": "Empty source segments", "source": group["source"]}
        previous = 0.0
        for i, segment in enumerate(segments):
            start = float(segment["start_s"])
            end = total if segment["end_s"] is None else float(segment["end_s"])
            if start < 0 or end <= start or end > total + 0.04:
                return {"status": "FAIL", "reason": f"Invalid interval {i}", "source": group["source"]}
            if abs(start - previous) > 0.005:
                return {"status": "FAIL", "reason": f"Input gap/overlap of {start-previous:.3f}s at segment {i}", "source": group["source"]}
            tempo = float(segment.get("tempo", 1.0))
            if not 0.5 <= tempo <= 2.0:
                return {"status": "FAIL", "reason": f"Invalid atempo {tempo}", "source": group["source"]}
            rendered = segment.get("transformed_clip")
            if not rendered:
                unproven.append(f"{group['source']} segment {i}: no transformed_clip evidence")
            else:
                proof = (basedir / rendered).resolve()
                if not proof.is_file():
                    return {"status":"UNKNOWN", "reason": f"Transformed clip not accessible: {rendered}"}
                rendered_duration = float(ffprobe(proof)["format"]["duration"])
                expected = (end-start)/tempo
                if abs(rendered_duration-expected) > max(0.18, expected*0.02):
                    return {"status":"FAIL",
                            "reason": f"Post-tempo clip {rendered}: {rendered_duration:.3f}s != source/tempo {expected:.3f}s",
                            "source":group["source"]}
            previous = end
        if abs(previous-total) > 0.04:
            return {"status": "FAIL", "reason": f"Input tail missing: {total-previous:.3f}s", "source": group["source"]}
        checked.append({"source": group["source"], "source_duration_s": round(total, 3),
                        "segments": len(segments), "coverage": "full-source-contiguous"})
    return {"status": "REVIEW" if unproven else "PASS",
            "source_interval_coverage": "PASS", "groups":checked,
            "unproven_rendered_clips": unproven,
            "limitation": "Declared source splits are not proof of rendered tails; transformed_clip must match source/tempo duration."}


def signal_windows(path, cues, threshold_dbfs=-40):
    pcm = command(["ffmpeg", "-nostdin", "-v", "error", "-i", str(path),
                   "-map", "0:a:0", "-vn", "-ac", "1", "-ar", "16000",
                   "-f", "s16le", "-acodec", "pcm_s16le", "-"])
    samples = array.array("h")
    samples.frombytes(pcm.stdout)
    frame = 320  # 20 ms at 16 kHz
    threshold = 32768 * 10**(threshold_dbfs/20)
    active = []
    for start in range(0, len(samples)-frame+1, frame):
        x = samples[start:start+frame]
        rms = math.sqrt(sum(v*v for v in x)/frame)
        active.append(rms >= threshold)
    result = []
    for cue in cues:
        first = max(0, int(cue["start"]/0.02))
        last = min(len(active), math.ceil(cue["end"]/0.02))
        frames = active[first:last]
        count = sum(frames)
        result.append({"cue": cue["index"], "active_20ms_frames": count,
                       "total_20ms_frames": len(frames),
                       "signal_present": count > 0})
    return result


def long_silences(path, threshold="-40dB", min_duration=1.5):
    process = command(["ffmpeg", "-hide_banner", "-nostdin", "-i", str(path),
                       "-map", "0:a:0", "-af",
                       f"silencedetect=noise={threshold}:d={min_duration}",
                       "-f", "null", "-"], check=False)
    if process.returncode:
        raise RuntimeError(process.stderr.decode(errors="replace")[-500:])
    return [float(m) for m in SILENCE.findall(process.stderr.decode(errors="replace"))]


def media_check(path, expected_width, expected_height, duration_range):
    info = ffprobe(path)
    streams = info.get("streams", [])
    video = next((s for s in streams if s["codec_type"] == "video"), None)
    audio = next((s for s in streams if s["codec_type"] == "audio"), None)
    duration = float(info["format"]["duration"])
    good = bool(video and audio and video["width"] == expected_width
                and video["height"] == expected_height
                and duration_range[0] <= duration <= duration_range[1])
    return {"status": "PASS" if good else "FAIL", "duration_s": duration,
            "width": video.get("width") if video else None,
            "height": video.get("height") if video else None,
            "video_codec": video.get("codec_name") if video else None,
            "audio_codec": audio.get("codec_name") if audio else None,
            "audio_sample_rate": audio.get("sample_rate") if audio else None,
            "sha256": sha256_file(path)}


def evaluate_human(evidence, file_checks):
    result = {}
    for name in ("line_by_line_content", "voice_and_visual_style", "mobile_720p", "master_1080p"):
        item = evidence.get(name, {})
        has_claim = item.get("status") == "PASS" and bool(item.get("evidence_ref"))
        if name in ("mobile_720p", "master_1080p"):
            measured = file_checks.get(name, {}).get("sha256")
            has_claim = has_claim and bool(measured) and item.get("sha256") == measured
        result[name] = {"status": "RECORDED" if has_claim else "PENDING",
                        "provenance": "human-attestation-not-independently-authenticated",
                        "evidence_ref": item.get("evidence_ref") if has_claim else None}
    return result


def audit(config_path):
    config_file = Path(config_path).resolve()
    cfg = json.loads(config_file.read_text(encoding="utf-8"))
    root = config_file.parent
    target = cfg.get("duration_range_s", [120, 180])
    checks = {}
    media = {}
    for key, dims in (("mobile_720p", (1280,720)), ("master_1080p", (1920,1080))):
        value = cfg.get("files", {}).get(key)
        path = root / value if value else None
        if not path or not path.is_file():
            media[key] = {"status": "UNKNOWN", "reason": "File missing/not set"}
            continue
        try:
            media[key] = media_check(path, *dims, target)
        except (OSError, ValueError, subprocess.CalledProcessError) as error:
            media[key] = {"status": "FAIL", "reason": str(error)}
    checks["media"] = media
    checks["source_audio_coverage"] = source_split_check(cfg.get("source_split_groups", []), root)
    sub_path = cfg.get("files", {}).get("subtitles_srt")
    cues = None
    if sub_path and (root/sub_path).is_file():
        try:
            cues = parse_srt(root/sub_path)
            expected = cfg.get("expected_caption_count")
            end_time = min((m["duration_s"] for m in media.values() if m["status"] == "PASS"), default=None)
            ok = (expected is None or len(cues) == expected) and (end_time is None or cues[-1]["end"] <= end_time+0.15)
            checks["subtitles"] = {"status": "PASS" if ok else "FAIL",
                                   "cue_count": len(cues),
                                   "last_cue_end_s": cues[-1]["end"]}
        except (ValueError, OSError) as error:
            checks["subtitles"] = {"status": "FAIL", "reason": str(error)}
    else:
        checks["subtitles"] = {"status": "UNKNOWN", "reason": "SRT missing"}
    if cues and cfg.get("files", {}).get("mobile_720p") and media["mobile_720p"]["status"] == "PASS":
        try:
            path = root / cfg["files"]["mobile_720p"]
            windows = signal_windows(path, cues)
            checks["caption_audio_activity"] = {
                "status": "PASS" if all(w["signal_present"] for w in windows) else "REVIEW",
                "cue_count_with_signal": sum(w["signal_present"] for w in windows),
                "cue_count_total": len(windows), "windows": windows,
                "limitation": "Signal activity is not word/phoneme identification; music may produce false positives."}
            spots = long_silences(path)
            checks["long_silences"] = {"status": "PASS" if not spots else "REVIEW",
                                       "starts_s": spots, "threshold": "-40dB / 1.5s",
                                       "limitation": "No silence does not guarantee no omitted words."}
        except (OSError, ValueError, subprocess.CalledProcessError, RuntimeError) as error:
            checks["caption_audio_activity"] = {"status": "UNKNOWN", "reason": str(error)}
            checks["long_silences"] = {"status": "UNKNOWN", "reason": str(error)}
    else:
        checks["caption_audio_activity"] = {"status": "NOT_TESTED"}
        checks["long_silences"] = {"status": "NOT_TESTED"}
    if all(media[x]["status"] == "PASS" for x in media):
        try:
            p1 = root / cfg["files"]["mobile_720p"]
            p2 = root / cfg["files"]["master_1080p"]
            h1, h2 = audio_bitstream_sha256(p1), audio_bitstream_sha256(p2)
            checks["cross_resolution_audio"] = {
                "status": "PASS" if h1 == h2 else "REVIEW",
                "same_encoded_audio_bitstream": h1 == h2,
                "mobile_audio_sha256": h1, "master_audio_sha256": h2,
                "note": "Different stream hashes require listening; matching hashes do not verify pictures/subtitles."}
        except (OSError, ValueError, subprocess.CalledProcessError) as error:
            checks["cross_resolution_audio"] = {"status": "UNKNOWN", "reason": str(error)}
    else:
        checks["cross_resolution_audio"] = {"status": "NOT_TESTED"}
    language_ok = cfg.get("selected_language") in ("zh-CN","en") and bool(cfg.get("language_selection_evidence_ref"))
    checks["language_choice"] = {"status": "PASS" if language_ok else "UNKNOWN",
                                  "selected_language": cfg.get("selected_language")}
    humans = evaluate_human(cfg.get("human_evidence", {}), media)
    checks["human_approvals"] = humans
    required = [
        media["mobile_720p"]["status"], media["master_1080p"]["status"],
        checks["source_audio_coverage"]["status"], checks["subtitles"]["status"],
        checks["caption_audio_activity"]["status"], checks["cross_resolution_audio"]["status"],
        checks["language_choice"]["status"]]
    tech = "FAIL" if "FAIL" in required else ("PASS" if all(x == "PASS" for x in required) else "HOLD")
    release = cfg.get("public_release", {})
    human_ready = all(v["status"] == "RECORDED" for v in humans.values())
    public_request = release.get("authorized") is True and bool(release.get("evidence_ref"))
    state = "READY_FOR_MANUAL_RELEASE" if tech == "PASS" and human_ready and public_request else "HOLD"
    return {"schema_version": "1.0", "project_id": cfg.get("project_id"),
            "version": cfg.get("version"), "checks": checks, "technical_gate": tech,
            "human_gate": "RECORDED" if human_ready else "PENDING",
            "public_release_gate": state,
            "publication_performed": False,
            "trust_note": "Human and release evidence refs inside JSON are user-supplied claims; independently authenticate before publishing.",
            "token_usage": cfg.get("model_token_usage", {"Tin":"UNKNOWN","Tout":"UNKNOWN","Ttotal":"UNKNOWN"})}


def trim_audio(args):
    src = Path(args.source)
    dest = Path(args.output)
    if not src.is_file():
        raise FileNotFoundError(src)
    if dest.exists():
        raise FileExistsError(f"Refusing to overwrite existing file: {dest}")
    if not 0.5 <= args.tempo <= 2.0 or args.start < 0 or args.duration <= 0:
        raise ValueError("Require 0.5<=tempo<=2, start>=0, duration>0")
    total = float(ffprobe(src)["format"]["duration"])
    if args.start + args.duration > total + 0.03:
        raise ValueError("Source trim exceeds source duration")
    dest.parent.mkdir(parents=True, exist_ok=True)
    # -ss/-t are input options BEFORE -i; -t after -i caused omitted tail words in v1.0.
    cmd = ["ffmpeg", "-hide_banner", "-nostdin", "-loglevel", "error",
           "-n", "-ss", f"{args.start:.6f}", "-t", f"{args.duration:.6f}",
           "-i", str(src), "-vn", "-af", f"atempo={args.tempo:.6f},aresample=48000",
           "-ac", "1", "-ar", "48000", "-c:a", "pcm_s16le", str(dest)]
    command(cmd)
    actual = float(ffprobe(dest)["format"]["duration"])
    expected = args.duration / args.tempo
    if abs(actual-expected) > max(0.18, expected*0.02):
        raise RuntimeError(f"Output duration {actual:.3f}s != expected {expected:.3f}s")
    print(json.dumps({"source_trim_s":args.duration, "tempo":args.tempo,
                      "output_s":actual, "expected_s":expected,
                      "status":"PASS", "source_side_trim":True}, indent=2))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    actions = parser.add_subparsers(dest="action", required=True)
    qa = actions.add_parser("audit", help="Audit two renders, SRT and source MP3 continuity")
    qa.add_argument("--config", required=True)
    qa.add_argument("--out", required=True)
    clip = actions.add_parser("trim-audio", help="Trim source interval BEFORE tempo, emit 48k PCM WAV")
    clip.add_argument("--source", required=True)
    clip.add_argument("--start", type=float, default=0.0)
    clip.add_argument("--duration", type=float, required=True)
    clip.add_argument("--tempo", type=float, default=1.0)
    clip.add_argument("--output", required=True)
    args = parser.parse_args()
    if not shutil.which("ffmpeg") or not shutil.which("ffprobe"):
        parser.error("Requires ffmpeg and ffprobe binaries on PATH")
    if args.action == "trim-audio":
        trim_audio(args)
    else:
        report = audit(args.config)
        output = Path(args.out)
        if output.exists():
            parser.error(f"Refusing to overwrite existing report: {output}")
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(report, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
        print(json.dumps({"technical_gate":report["technical_gate"],
                          "human_gate":report["human_gate"],
                          "public_release_gate":report["public_release_gate"],
                          "report":str(output)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
