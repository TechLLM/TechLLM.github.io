#!/usr/bin/env python3
"""ModuLens: modality-aware evidence features for lightweight RAG pipelines."""

from __future__ import annotations

import argparse
import bisect
import json
import os
import re
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable


MODALITIES = ("table", "code", "formula", "citation", "date", "benchmark")

DEFAULT_WEIGHTS = {
    "table": 1.15,
    "code": 1.10,
    "formula": 1.10,
    "citation": 1.00,
    "date": 0.95,
    "benchmark": 1.35,
}

PROFILE_MULTIPLIERS = {
    "general": {},
    "scientific": {"formula": 1.20, "citation": 1.25, "benchmark": 1.20, "table": 1.10},
    "software": {"code": 1.50, "benchmark": 1.10, "table": 1.05},
    "temporal": {"date": 1.60, "citation": 1.10},
}

STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "by",
    "for",
    "from",
    "has",
    "have",
    "how",
    "in",
    "is",
    "it",
    "of",
    "on",
    "or",
    "that",
    "the",
    "this",
    "to",
    "was",
    "were",
    "what",
    "which",
    "with",
}

MONTHS = (
    "Jan(?:uary)?",
    "Feb(?:ruary)?",
    "Mar(?:ch)?",
    "Apr(?:il)?",
    "May",
    "Jun(?:e)?",
    "Jul(?:y)?",
    "Aug(?:ust)?",
    "Sep(?:tember)?",
    "Oct(?:ober)?",
    "Nov(?:ember)?",
    "Dec(?:ember)?",
)


@dataclass
class Document:
    id: str
    text: str
    source_type: str = "text"


@dataclass
class Span:
    modality: str
    text: str
    start_line: int
    end_line: int
    confidence: float
    signals: list[str]
    metadata: dict[str, Any]

    def compact(self, score: float | None = None) -> dict[str, Any]:
        value: dict[str, Any] = {
            "modality": self.modality,
            "start_line": self.start_line,
            "end_line": self.end_line,
            "confidence": round(self.confidence, 3),
            "signals": self.signals,
            "text": snippet(self.text),
        }
        if self.metadata:
            value["metadata"] = self.metadata
        if score is not None:
            value["score"] = round(score, 4)
        return value


SAMPLE_DOCS = [
    Document(
        id="mock-paper-a.md",
        source_type="markdown",
        text="""# Sparse Adapter Benchmark

In 2024, ModuLens-A was evaluated on a retrieval benchmark [1].

| System | F1 | Latency ms | Notes |
| --- | ---: | ---: | --- |
| DenseBase | 78.4 | 42 | baseline |
| ModuLens-A | 84.9 | 37 | table-aware router |

The objective uses $score = lexical(q,d) + 0.4 * evidence(q,d)$.

```python
def route(query, spans):
    return sorted(spans, key=lambda span: span["score"], reverse=True)
```

The authors report a 6.5 point F1 improvement over the baseline on March 3, 2024.
Reference: [1] Doe et al. (2024), doi:10.1000/example.
""",
    ),
    Document(
        id="mock-note-b.txt",
        source_type="text",
        text="""Release notes from 2022 describe a plain keyword retriever.
It includes no benchmark table and no code sample.
The only metric mentioned is recall, but no numeric result is provided.
""",
    ),
]


QUESTION_RULES = [
    (
        "numeric_comparison",
        (
            "compare",
            "comparison",
            "better",
            "worse",
            "higher",
            "lower",
            "faster",
            "slower",
            "versus",
            " vs ",
            "metric",
            "score",
            "accuracy",
            "f1",
            "latency",
            "throughput",
        ),
        {"table": 1.40, "benchmark": 1.65, "formula": 1.15},
    ),
    (
        "implementation_detail",
        (
            "implement",
            "implementation",
            "code",
            "api",
            "function",
            "class",
            "algorithm",
            "configure",
            "configuration",
            "debug",
        ),
        {"code": 1.75, "formula": 1.15, "table": 1.05},
    ),
    (
        "experimental_result",
        (
            "experiment",
            "experimental",
            "evaluation",
            "benchmark",
            "baseline",
            "ablation",
            "result",
            "performance",
            "sota",
        ),
        {"benchmark": 1.70, "table": 1.30, "citation": 1.15},
    ),
    (
        "citation_support",
        (
            "cite",
            "citation",
            "reference",
            "source",
            "evidence",
            "paper",
            "doi",
            "arxiv",
        ),
        {"citation": 1.80, "date": 1.15},
    ),
    (
        "temporal_claim",
        (
            "latest",
            "recent",
            "current",
            "before",
            "after",
            "since",
            "during",
            "when",
            "date",
            "year",
            "month",
            "202",
        ),
        {"date": 1.85, "citation": 1.15, "benchmark": 1.05},
    ),
    (
        "mathematical_reasoning",
        (
            "formula",
            "equation",
            "derive",
            "derivation",
            "proof",
            "loss",
            "objective",
            "gradient",
        ),
        {"formula": 1.85, "code": 1.10},
    ),
]


def snippet(text: str, limit: int = 220) -> str:
    compact = re.sub(r"\s+", " ", text).strip()
    if len(compact) <= limit:
        return compact
    return compact[: limit - 3].rstrip() + "..."


def tokenize(text: str) -> list[str]:
    tokens = re.findall(r"[a-z0-9][a-z0-9_./+-]*", text.lower())
    return [token for token in tokens if token not in STOPWORDS and len(token) > 1]


def line_starts(text: str) -> list[int]:
    starts = [0]
    for match in re.finditer(r"\n", text):
        starts.append(match.end())
    return starts


def line_number(starts: list[int], offset: int) -> int:
    return bisect.bisect_right(starts, offset)


def text_for_line_range(lines: list[str], start: int, end: int) -> str:
    return "\n".join(lines[start - 1 : end])


def is_table_line(line: str) -> bool:
    stripped = line.strip()
    if not stripped or stripped.startswith("```") or stripped.startswith("~~~"):
        return False
    return stripped.count("|") >= 2


def detect_code_spans(lines: list[str]) -> tuple[list[Span], set[int]]:
    spans: list[Span] = []
    code_lines: set[int] = set()
    i = 0
    while i < len(lines):
        match = re.match(r"\s*(```|~~~)\s*([A-Za-z0-9_+.-]+)?", lines[i])
        if not match:
            i += 1
            continue
        fence = match.group(1)
        language = match.group(2) or "unknown"
        start = i + 1
        i += 1
        while i < len(lines) and not lines[i].strip().startswith(fence):
            i += 1
        end = min(i + 1, len(lines))
        for line_no in range(start, end + 1):
            code_lines.add(line_no)
        spans.append(
            Span(
                modality="code",
                text=text_for_line_range(lines, start, end),
                start_line=start,
                end_line=end,
                confidence=0.97,
                signals=["fenced_code_block"],
                metadata={"language": language},
            )
        )
        i += 1
    return spans, code_lines


def detect_table_spans(lines: list[str], excluded_lines: set[int]) -> list[Span]:
    spans: list[Span] = []
    i = 0
    while i < len(lines):
        line_no = i + 1
        if line_no in excluded_lines or not is_table_line(lines[i]):
            i += 1
            continue
        start = line_no
        block: list[str] = []
        while i < len(lines) and i + 1 not in excluded_lines and is_table_line(lines[i]):
            block.append(lines[i])
            i += 1
        end = start + len(block) - 1
        if len(block) >= 2:
            separator = any(re.search(r"\|\s*:?-{3,}:?\s*(?:\||$)", row) for row in block)
            confidence = 0.93 if separator else 0.78
            spans.append(
                Span(
                    modality="table",
                    text="\n".join(block),
                    start_line=start,
                    end_line=end,
                    confidence=confidence,
                    signals=["markdown_pipe_table"] + (["alignment_row"] if separator else []),
                    metadata={"rows": len(block)},
                )
            )
        else:
            i += 1
    return spans


def add_regex_spans(
    spans: list[Span],
    text: str,
    starts: list[int],
    lines: list[str],
    modality: str,
    patterns: Iterable[tuple[str, str, float]],
    flags: int = 0,
) -> None:
    seen: set[tuple[str, int, int]] = set()
    for pattern, signal, confidence in patterns:
        for match in re.finditer(pattern, text, flags):
            start_line = line_number(starts, match.start())
            end_line = line_number(starts, match.end())
            key = (modality, start_line, end_line)
            if key in seen:
                continue
            seen.add(key)
            matched_text = match.group(0)
            line_text = text_for_line_range(lines, start_line, end_line).strip()
            spans.append(
                Span(
                    modality=modality,
                    text=line_text or matched_text,
                    start_line=start_line,
                    end_line=end_line,
                    confidence=confidence,
                    signals=[signal],
                    metadata={},
                )
            )


def detect_regex_spans(text: str, lines: list[str]) -> list[Span]:
    starts = line_starts(text)
    spans: list[Span] = []
    month_pattern = "|".join(MONTHS)
    metric_terms = (
        r"accuracy|f1(?:-score)?|precision|recall|auc|bleu|rouge|map|ndcg|"
        r"latency|throughput|speedup|tokens/s|pass@k|benchmark|baseline|sota|"
        r"state-of-the-art|win rate"
    )

    add_regex_spans(
        spans,
        text,
        starts,
        lines,
        "formula",
        (
            (r"\$\$[\s\S]{1,600}?\$\$", "latex_block_formula", 0.90),
            (r"(?<!\\)\$[^$\n]{1,180}?(?<!\\)\$", "latex_inline_formula", 0.82),
            (r"\\\[[\s\S]{1,600}?\\\]", "latex_display_formula", 0.88),
            (r"\b(?:loss|objective|gradient|equation)\b[^\n]{0,180}(?:=|\\sum|\\frac|\^|_)[^\n]{0,180}", "formula_language", 0.72),
            (r"^[^\n]{0,140}(?:<=|>=|~=|=)[^\n]{1,140}$", "equation_like_line", 0.55),
        ),
        re.IGNORECASE | re.MULTILINE,
    )

    add_regex_spans(
        spans,
        text,
        starts,
        lines,
        "citation",
        (
            (r"\b10\.\d{4,9}/[-._;()/:A-Za-z0-9]+", "doi", 0.95),
            (r"\barXiv:\d{4}\.\d{4,5}(?:v\d+)?\b", "arxiv", 0.95),
            (r"\[[0-9]{1,3}\]", "numeric_citation", 0.75),
            (r"\([A-Z][A-Za-z-]+(?:\s+et al\.)?,\s*(?:19|20)\d{2}[a-z]?\)", "author_year_citation", 0.83),
            (r"\b[A-Z][A-Za-z-]+ et al\. \((?:19|20)\d{2}[a-z]?\)", "author_year_citation", 0.83),
        ),
        re.IGNORECASE,
    )

    add_regex_spans(
        spans,
        text,
        starts,
        lines,
        "date",
        (
            (r"\b(?:19|20)\d{2}-\d{2}-\d{2}\b", "iso_date", 0.92),
            (rf"\b(?:{month_pattern})\s+\d{{1,2}},\s+(?:19|20)\d{{2}}\b", "month_day_year", 0.90),
            (r"\bQ[1-4]\s+(?:19|20)\d{2}\b", "quarter_year", 0.85),
            (r"\b(?:19|20)\d{2}\b", "year", 0.62),
        ),
        re.IGNORECASE,
    )

    add_regex_spans(
        spans,
        text,
        starts,
        lines,
        "benchmark",
        (
            (
                rf"\b(?:{metric_terms})\b[^\n.]*?(?:\d+(?:\.\d+)?\s*%?|\b(?:higher|lower|faster|slower|best|improved|improvement)\b)[^\n.]*",
                "metric_result",
                0.86,
            ),
            (r"\b\d+(?:\.\d+)?\s*(?:%|ms|seconds?|tokens/s|x)\b[^\n.]{0,80}\b(?:benchmark|baseline|latency|throughput|accuracy|f1|recall|precision)\b", "numeric_metric_context", 0.76),
            (r"\b(?:benchmark|baseline|sota|state-of-the-art|ablation)\b[^\n.]{0,120}", "benchmark_language", 0.65),
        ),
        re.IGNORECASE,
    )

    return spans


def detect_spans(text: str) -> list[Span]:
    lines = text.splitlines()
    code_spans, code_lines = detect_code_spans(lines)
    table_spans = detect_table_spans(lines, code_lines)
    regex_spans = detect_regex_spans(text, lines)
    spans = code_spans + table_spans + regex_spans
    spans.sort(key=lambda item: (item.start_line, item.end_line, item.modality))
    return spans


def classify_question(question: str) -> dict[str, Any]:
    normalized = " " + question.lower() + " "
    needs: list[str] = []
    preferences = {modality: 1.0 for modality in MODALITIES}

    for need, keywords, boosts in QUESTION_RULES:
        if any(keyword in normalized for keyword in keywords):
            needs.append(need)
            for modality, multiplier in boosts.items():
                preferences[modality] *= multiplier

    if not needs:
        needs.append("semantic_text")

    return {
        "needs": needs,
        "query_tokens": tokenize(question),
        "modality_preferences": {key: round(value, 3) for key, value in preferences.items()},
    }


def load_custom_weights(path: str | None) -> dict[str, float]:
    if not path:
        return {}
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if "weights" in data and isinstance(data["weights"], dict):
        data = data["weights"]
    weights: dict[str, float] = {}
    for modality in MODALITIES:
        if modality in data:
            weights[modality] = float(data[modality])
    return weights


def build_weights(profile: str, custom_weights: dict[str, float] | None = None) -> dict[str, float]:
    if profile not in PROFILE_MULTIPLIERS:
        raise ValueError(f"Unknown profile: {profile}")
    weights = dict(DEFAULT_WEIGHTS)
    for modality, multiplier in PROFILE_MULTIPLIERS[profile].items():
        weights[modality] *= multiplier
    for modality, value in (custom_weights or {}).items():
        if modality in weights:
            weights[modality] = float(value)
    return {key: round(value, 4) for key, value in weights.items()}


def lexical_overlap(query_tokens: set[str], text: str) -> float:
    if not query_tokens:
        return 0.0
    text_tokens = set(tokenize(text))
    return len(query_tokens & text_tokens) / len(query_tokens)


def score_span(span: Span, query_tokens: set[str], weights: dict[str, float], preferences: dict[str, float]) -> float:
    span_tokens = set(tokenize(span.text))
    overlap = len(query_tokens & span_tokens) / max(len(query_tokens), 1)
    token_density = min(1.0, len(span_tokens) / 60.0)
    signal_bonus = min(0.12, 0.03 * len(span.signals))
    modality_weight = weights.get(span.modality, 1.0) * preferences.get(span.modality, 1.0)
    raw = modality_weight * (0.64 * overlap + 0.18 * token_density + 0.18 * span.confidence + signal_bonus)
    return max(0.0, raw)


def score_document(
    document: Document,
    question: str,
    question_profile: dict[str, Any],
    weights: dict[str, float],
    max_spans: int,
) -> dict[str, Any]:
    query_tokens = set(question_profile["query_tokens"])
    spans = detect_spans(document.text)
    modality_counts = Counter(span.modality for span in spans)
    preferences = question_profile["modality_preferences"]
    scored_spans = [(span, score_span(span, query_tokens, weights, preferences)) for span in spans]
    scored_spans.sort(key=lambda item: item[1], reverse=True)

    lexical = lexical_overlap(query_tokens, document.text)
    top_scores = [score for _, score in scored_spans[:8]]
    span_signal = min(1.0, sum(top_scores) / 3.5) if top_scores else 0.0
    useful_modalities = {
        span.modality
        for span, score in scored_spans
        if score >= 0.18 and span.modality in MODALITIES
    }
    preferred_modalities = {
        modality
        for modality, preference in preferences.items()
        if preference > 1.05
    }
    if preferred_modalities:
        coverage = len(useful_modalities & preferred_modalities) / len(preferred_modalities)
    else:
        coverage = len(useful_modalities) / len(MODALITIES)
    coverage = min(1.0, coverage)

    final_score = min(1.0, 0.46 * lexical + 0.44 * span_signal + 0.10 * coverage)
    modality_scores: dict[str, float] = defaultdict(float)
    for span, score in scored_spans:
        modality_scores[span.modality] += score

    return {
        "id": document.id,
        "source_type": document.source_type,
        "score": round(final_score, 4),
        "features": {
            "lexical_overlap": round(lexical, 4),
            "span_signal": round(span_signal, 4),
            "preferred_modality_coverage": round(coverage, 4),
            "modality_counts": {modality: modality_counts.get(modality, 0) for modality in MODALITIES},
            "modality_scores": {
                modality: round(modality_scores.get(modality, 0.0), 4)
                for modality in MODALITIES
            },
            "matched_modalities": sorted(useful_modalities),
        },
        "top_spans": [
            span.compact(score=score)
            for span, score in scored_spans[:max_spans]
        ],
    }


def normalize_documents(items: Iterable[Any]) -> list[Document]:
    documents: list[Document] = []
    for index, item in enumerate(items, start=1):
        if isinstance(item, Document):
            documents.append(item)
        elif isinstance(item, dict):
            text = str(item.get("text") or item.get("content") or "")
            doc_id = str(item.get("id") or item.get("name") or f"doc-{index}")
            source_type = str(item.get("source_type") or item.get("type") or "json")
            documents.append(Document(id=doc_id, text=text, source_type=source_type))
        else:
            documents.append(Document(id=f"doc-{index}", text=str(item), source_type="text"))
    return documents


def route_evidence(
    question: str,
    documents: Iterable[Any],
    *,
    profile: str = "general",
    custom_weights: dict[str, float] | None = None,
    max_spans: int = 5,
) -> dict[str, Any]:
    docs = normalize_documents(documents)
    weights = build_weights(profile, custom_weights)
    question_profile = classify_question(question)
    scored = [
        score_document(document, question, question_profile, weights, max_spans)
        for document in docs
    ]
    scored.sort(key=lambda item: item["score"], reverse=True)
    return {
        "query": question,
        "question_profile": {
            "needs": question_profile["needs"],
            "modality_preferences": question_profile["modality_preferences"],
        },
        "config": {
            "profile": profile,
            "weights": weights,
            "max_spans_per_document": max_spans,
        },
        "documents": scored,
    }


def load_json_documents(path: Path) -> list[Document]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, dict) and "documents" in data:
        data = data["documents"]
    if isinstance(data, dict):
        data = [data]
    if not isinstance(data, list):
        raise ValueError("JSON input must be a document object, a list of documents, or an object with a documents list.")
    return normalize_documents(data)


def load_documents(input_path: str | None) -> tuple[list[Document], str]:
    if not input_path:
        return list(SAMPLE_DOCS), "built_in_sample"

    path = Path(input_path)
    if not path.exists():
        raise FileNotFoundError(f"Input path does not exist: {input_path}")

    if path.is_dir():
        files = sorted(
            item
            for item in path.rglob("*")
            if item.is_file() and item.suffix.lower() in {".md", ".markdown", ".txt", ".text"}
        )
        documents = [
            Document(
                id=item.relative_to(path).as_posix(),
                text=item.read_text(encoding="utf-8"),
                source_type=item.suffix.lower().lstrip(".") or "text",
            )
            for item in files
        ]
        return documents, "directory"

    if path.suffix.lower() == ".json":
        return load_json_documents(path), "json"

    return [
        Document(
            id=path.name,
            text=path.read_text(encoding="utf-8"),
            source_type=path.suffix.lower().lstrip(".") or "text",
        )
    ], "file"


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Detect modality-specific evidence spans and emit relevance feature JSON for RAG pipelines."
    )
    parser.add_argument(
        "--question",
        default="Which document provides benchmark evidence with implementation details?",
        help="Question or retrieval query to score against.",
    )
    parser.add_argument(
        "--input",
        help="Markdown/text file, JSON document list, or directory of .md/.txt files. Uses built-in mock data when omitted.",
    )
    parser.add_argument(
        "--output",
        help="Optional output JSON file. Prints to stdout when omitted.",
    )
    parser.add_argument(
        "--weights",
        help="Optional JSON file with modality weights, for example {'benchmark': 2.0, 'code': 1.4}.",
    )
    parser.add_argument(
        "--profile",
        choices=sorted(PROFILE_MULTIPLIERS),
        default="general",
        help="Preset multiplier profile for common retrieval tasks.",
    )
    parser.add_argument(
        "--max-spans",
        type=int,
        default=5,
        help="Maximum top evidence spans to include per document.",
    )
    parser.add_argument(
        "--pretty",
        action="store_true",
        help="Pretty-print JSON output.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    api_key_present = bool(os.getenv("MODULENS_API_KEY") or os.getenv("OPENAI_API_KEY"))
    documents, input_mode = load_documents(args.input)
    custom_weights = load_custom_weights(args.weights)
    result = route_evidence(
        args.question,
        documents,
        profile=args.profile,
        custom_weights=custom_weights,
        max_spans=max(1, args.max_spans),
    )
    result["runtime"] = {
        "input_mode": input_mode,
        "document_count": len(documents),
        "api_key_present": api_key_present,
        "external_services_used": False,
    }

    output = json.dumps(result, indent=2 if args.pretty else None, sort_keys=args.pretty)
    if args.output:
        Path(args.output).write_text(output + "\n", encoding="utf-8")
    else:
        print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
