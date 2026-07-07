#!/usr/bin/env python3
"""Example external scorer for the Maskwright stdin/stdout contract."""

from __future__ import annotations

import json
import re
import sys


def tokens(text: str) -> set[str]:
    """Return lowercase token set."""

    return set(re.findall(r"[a-z0-9]+", text.lower()))


def main() -> int:
    """Read a scoring request from stdin and write JSON scores to stdout."""

    payload = json.loads(sys.stdin.read())
    query_tokens = tokens(payload["query"])
    scores = []
    for index, candidate in enumerate(payload["candidates"]):
        candidate_tokens = tokens(candidate.get("text", ""))
        overlap = len(query_tokens & candidate_tokens) / max(len(query_tokens), 1)
        score = overlap + (0.01 * (len(payload["candidates"]) - index))
        scores.append({"id": candidate["id"], "score": round(score, 6)})
    print(json.dumps({"scores": scores}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
