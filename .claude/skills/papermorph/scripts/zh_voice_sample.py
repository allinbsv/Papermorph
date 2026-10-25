"""Optional Qwen3-TTS Mandarin audition. NOT the timed Papermorph narration pipeline.

Example:
    python3 zh_voice_sample.py --text-file narration.zh.json --speaker Uncle_Fu --output sample.wav --dry-run

Uses the official qwen-tts Python package on a user-provided local accelerator.
The selected weights may be downloaded by the package; this requires bandwidth,
storage and compute and must be checked against the exact weights' license.
"""

import argparse
import json
from pathlib import Path


MODEL = "Qwen/Qwen3-TTS-12Hz-1.7B-CustomVoice"
SPEAKERS = ("Uncle_Fu", "Serena", "Vivian", "Dylan", "Eric")


def audition_text(path):
    """Read a Chinese script as JSON beats or an ordinary UTF-8 text file."""
    p = Path(path)
    source = p.read_text(encoding="utf-8-sig")
    if p.suffix.lower() != ".json":
        result = source.strip()
    else:
        spec = json.loads(source)
        beats = spec.get("beats")
        if not isinstance(beats, dict) or not beats:
            raise ValueError("narration JSON must contain nonempty 'beats' object")
        lines = []
        for beat in beats.values():
            raw = beat.get("text") if isinstance(beat, dict) else beat
            if not isinstance(raw, str):
                raise ValueError("each beat must be text or an object with 'text'")
            import re
            lines.append(re.sub(r"\[\[\w+\]\]", "", raw).strip())
        result = "\n".join(lines)
    if not result:
        raise ValueError("audition text cannot be empty")
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--text-file", required=True, type=Path, help="UTF-8 text or narration JSON")
    parser.add_argument("--speaker", choices=SPEAKERS, default="Uncle_Fu")
    parser.add_argument("--instruct", default="像一位沉稳而亲切的长者，平实自然地讲给一个好奇的朋友听；不要播音腔或刻意煽情。")
    parser.add_argument("--output", required=True, type=Path, help="local .wav output")
    parser.add_argument("--device", default="cuda:0", help="explicit torch device, default cuda:0")
    parser.add_argument("--dry-run", action="store_true", help="validate input without loading any model")
    opts = parser.parse_args(argv)
    if opts.output.suffix.lower() != ".wav":
        parser.error("--output must end with .wav")
    try:
        spoken_text = audition_text(opts.text_file)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        parser.error(str(exc))
    if opts.dry_run:
        print(json.dumps({"status": "DRY_RUN_ONLY", "model": MODEL, "speaker": opts.speaker,
                          "device": opts.device, "characters": len(spoken_text),
                          "output": str(opts.output), "timings": "NOT_GENERATED"}, ensure_ascii=False, indent=2))
        return 0

    import torch
    import soundfile as sf
    from qwen_tts import Qwen3TTSModel

    model = Qwen3TTSModel.from_pretrained(MODEL, device_map=opts.device, dtype=torch.bfloat16)
    wavs, sample_rate = model.generate_custom_voice(
        text=spoken_text, language="Chinese", speaker=opts.speaker, instruct=opts.instruct
    )
    opts.output.parent.mkdir(parents=True, exist_ok=True)
    sf.write(str(opts.output), wavs[0], sample_rate)
    print(f"AUDIO_CREATED: {opts.output} ({sample_rate} Hz); HUMAN_LISTENING_PENDING; TIMING_ALIGNMENT_PENDING")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
