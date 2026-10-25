"""Check PaperMorph subscription-vs-metered access policy before an AI operation.

This is a configuration preflight, not an actual provider-side spend limiter.
"""

import argparse
import json
from pathlib import Path


def check_token_policy(style, mode, scope=None):
    policy = style.get("token_policy")
    if not isinstance(policy, dict):
        return False, "missing token_policy; no implied metered authorization"
    if mode == "subscription":
        if policy.get("access_mode") == "existing_subscriptions_only":
            return True, "existing subscription is permitted; provider quota remains unknown"
        return False, "subscription access mode must be explicitly configured"
    metered = policy.get("metered_api")
    if not isinstance(metered, dict) or metered.get("authorized") is not True:
        return False, "paid API has not been authorized by the user"
    if not scope or metered.get("approved_scope") != scope:
        return False, "paid API scope does not match user approval"
    if not isinstance(metered.get("approved_by_user_source"), str) or not metered["approved_by_user_source"].strip():
        return False, "paid API user approval source is missing"
    cap = metered.get("budget_usd")
    if isinstance(cap, bool) or not isinstance(cap, (int, float)) or not (0 < cap < float("inf")):
        return False, "paid API budget cap must be an explicit positive finite number"
    return True, "configuration authorized for this scope; verify a real provider-side spend stop before use"


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("style", type=Path)
    parser.add_argument("--mode", choices=("subscription", "metered-api"), required=True)
    parser.add_argument("--scope", help="exact operation/release identifier for a metered API step")
    opts = parser.parse_args(argv)
    try:
        style = json.loads(opts.style.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"HOLD: could not read policy: {exc}")
        return 2
    if not isinstance(style, dict):
        print("HOLD: policy root must be an object")
        return 2
    passed, reason = check_token_policy(style, opts.mode, opts.scope)
    print(f"{'AUTHORIZED_FOR_SCOPE' if passed else 'HOLD'}: {reason}")
    return 0 if passed else 2


if __name__ == "__main__":
    raise SystemExit(main())
