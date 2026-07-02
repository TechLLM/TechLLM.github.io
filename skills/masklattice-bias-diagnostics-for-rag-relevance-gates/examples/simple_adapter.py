#!/usr/bin/env python3
"""Tiny stdin/stdout scorer adapter example for MaskLattice."""

import json
import re
import sys


def tokens(text):
    return set(re.findall(r"[a-z0-9]+", text.lower()))


def score(question, document):
    q = tokens(question)
    d = tokens(document)
    if not q or not d:
        return 0.0
    return round(len(q & d) / len(q), 6)


cases = json.loads(sys.stdin.read() or "[]")
print(
    json.dumps(
        [
            {"case_id": case["case_id"], "score": score(case["question"], case["document"])}
            for case in cases
        ]
    )
)
