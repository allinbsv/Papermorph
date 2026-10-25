"""Fail-closed check that the user chose Chinese/English for the exact release.

This checks the recorded user language choice ONLY, not final technical QA.
Example: python3 delivery_language_gate.py books/my-book/style.json --language en --artifact ch01-v2
"""

import argparse
import json
from pathlib import Path


LANGUAGES = {"zh", "en"}


def check_delivery_choice(style, language, artifact):
    """Return (passed, reason). Never infer a choice from a default voice or book language."""
    delivery = style.get("delivery")
    if not isinstance(delivery, dict):
        return False, "no delivery choice recorded; ask Chinese or English first"
    supported = delivery.get("supported_languages")
    if not isinstance(supported, list) or any(not isinstance(v, str) for v in supported) or not LANGUAGES.issubset(set(supported)):
        return False, "the bilingual language options are not configured"
    selection = delivery.get("selection")
    if not isinstance(selection, dict):
        return False, "no selection for this deliverable"
    if selection.get("confirmed_by_user") is not True:
        return False, "the user has not explicitly confirmed a delivery language"
    if selection.get("language") != language:
        return False, "requested language differs from the confirmed choice"
    if selection.get("for_artifact") != artifact:
        return False, "language confirmation belongs to a different artifact/revision"
    if not isinstance(selection.get("source"), str) or not selection["source"].strip():
        return False, "confirmation source is missing"
    return True, "user language choice matches this artifact; technical QA is still separate"


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("style", type=Path, help="book's style.json with recorded user choice")
    parser.add_argument("--language", choices=sorted(LANGUAGES), required=True)
    parser.add_argument("--artifact", required=True, help="specific deliverable/revision identifier")
    args = parser.parse_args(argv)
    if not args.artifact.strip():
        parser.error("--artifact must be nonempty")
    try:
        style = json.loads(args.style.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"BLOCKED: could not load style: {exc}")
        return 2
    if not isinstance(style, dict):
        print("BLOCKED: style.json root must be an object")
        return 2
    passed, reason = check_delivery_choice(style, args.language, args.artifact)
    print(f"{'CHOICE_CONFIRMED' if passed else 'BLOCKED'}: {reason}")
    return 0 if passed else 2


if __name__ == "__main__":
    raise SystemExit(main())
