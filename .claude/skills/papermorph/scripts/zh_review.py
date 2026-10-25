"""Static checks for Chinese narration. These checks do not certify human sincerity.

Usage:
    python3 scripts/zh_review.py content/book/ch01/narration.zh.json --style books/book/style.json

Exit code 0 means the file is structurally usable, not that a person has
approved the script, voice, factual claims or finished film.
"""

import argparse
import json
import re
from pathlib import Path


MARK = re.compile(r"\[\[([A-Za-z0-9_]+)\]\]")
HAN = re.compile(r"[\u3400-\u9fff]")
CLICHES = (
    "在当今社会", "综上所述", "让我们一起", "不言而喻", "深刻揭示", "赋能",
    "众所周知", "毋庸置疑", "值得注意的是", "首先.*其次.*最后",
)


def primary_language(value):
    return str(value).split("-")[0].lower()


def analyze(spec, style=None):
    """Return (errors, warnings) with beat references; never infer editorial approval."""
    errors, warnings = [], []
    if not isinstance(spec, dict):
        return ["Narration root must be an object"], []
    if spec.get("engine", "edge") not in ("edge", "kokoro"):
        errors.append("Unsupported TTS engine; choose edge or kokoro")
    beats = spec.get("beats")
    if not isinstance(beats, dict) or not beats:
        return errors + ["beats must be a non-empty object"], warnings
    voices = spec.get("voices", {})
    if not isinstance(voices, dict):
        errors.append("voices must be an object")
        voices = {}
    lang = ((style or {}).get("book", {}).get("language", "zh")
            if isinstance(style, dict) else "zh")
    if primary_language(lang) != "zh":
        errors.append(f"Expected a Chinese book language, got {lang!r}")

    for beat, raw in beats.items():
        if not re.fullmatch(r"[A-Za-z0-9_-]+", beat):
            errors.append(f"{beat}: beat id must use ASCII letters, digits, _ or -")
        who = spec
        sub = None
        if isinstance(raw, dict):
            speaker, sub = raw.get("speaker"), raw.get("sub")
            if not speaker or speaker not in voices:
                errors.append(f"{beat}: speaker is missing from voices")
                continue
            who = voices[speaker]
            raw = raw.get("text")
        if not isinstance(raw, str) or not raw.strip():
            errors.append(f"{beat}: text must be a non-empty string")
            continue
        if not isinstance(who, dict) or not isinstance(who.get("voice"), str):
            errors.append(f"{beat}: selected TTS voice is missing")
            continue

        clean = MARK.sub("", raw)
        if "[[" in clean or "]]" in clean:
            errors.append(f"{beat}: malformed [[mark]] tag")
        mark_names = MARK.findall(raw)
        if len(mark_names) != len(set(mark_names)):
            errors.append(f"{beat}: duplicated mark in a beat")
        voice_lang = primary_language(who["voice"])
        is_foreign = voice_lang != "zh" and bool(sub)
        if voice_lang != "zh" and not is_foreign:
            errors.append(f"{beat}: {who['voice']} is not Chinese; foreign speech needs a Chinese sub")
        if not is_foreign and not HAN.search(clean):
            warnings.append(f"{beat}: no Chinese characters detected")
        if len(HAN.findall(clean)) > 100:
            warnings.append(f"{beat}: long voice beat; review pauses and subtitle breaks")
        if clean and clean[-1] not in "。！？!?…\"'”’":
            warnings.append(f"{beat}: no sentence-ending punctuation")
        for phrase in CLICHES:
            if re.search(phrase, clean):
                warnings.append(f"{beat}: editorial cliché candidate: {phrase}")
    return errors, warnings


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("narration", type=Path)
    parser.add_argument("--style", type=Path)
    args = parser.parse_args()
    try:
        spec = json.loads(args.narration.read_text(encoding="utf-8-sig"))
        style = json.loads(args.style.read_text(encoding="utf-8-sig")) if args.style else None
    except (OSError, json.JSONDecodeError) as exc:
        parser.exit(2, f"INPUT_ERROR: {exc}\n")
    errors, warnings = analyze(spec, style)
    for problem in errors:
        print(f"ERROR: {problem}")
    for problem in warnings:
        print(f"REVIEW: {problem}")
    print(f"STRUCTURE: {'FAIL' if errors else 'PASS'}; HUMAN_REVIEW: PENDING; errors={len(errors)}; reviews={len(warnings)}")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
