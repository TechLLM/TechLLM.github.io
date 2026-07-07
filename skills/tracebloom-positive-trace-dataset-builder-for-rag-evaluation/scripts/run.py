#!/usr/bin/env python3
"""TraceBloom CLI for building positive-trace RAG evaluation datasets.

The implementation is intentionally small and dependency-free. It extracts
positive query-document traces from cited answers, aligns them with retrieval
logs, and emits deterministic JSONL records for confirmed positives and guarded
implicit negative candidates.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import parse_qs, urlparse


SAMPLE_ANSWERS = """# Example answer
Query ID: q-001
Query: How should we evaluate a RAG retriever from product traces?

Start from answer citations that survived review, such as
[retriever audit](doc://rag-handbook#chunk=intro), and compare them with
operational signals in [[support-notes#chunk=trace-signals]].
"""

SAMPLE_RETRIEVAL_LOG = """{"query_id":"q-001","query":"How should we evaluate a RAG retriever from product traces?","run_id":"run-001","rank":1,"doc_id":"rag-handbook","chunk_id":"intro","score":0.92}
{"query_id":"q-001","query":"How should we evaluate a RAG retriever from product traces?","run_id":"run-001","rank":2,"doc_id":"unused-overview","chunk_id":"overview","score":0.81}
{"query_id":"q-001","query":"How should we evaluate a RAG retriever from product traces?","run_id":"run-001","rank":3,"doc_id":"support-notes","chunk_id":"trace-signals","score":0.76}
{"query_id":"q-001","query":"How should we evaluate a RAG retriever from product traces?","run_id":"run-001","rank":4,"doc_id":"weak-match","chunk_id":"draft","score":0.41}
"""


@dataclass(frozen=True)
class Citation:
    """A positive trace extracted from an answer or citation manifest."""

    query_id: str
    query: str
    doc_id: str
    chunk_id: str | None
    citation: str
    input_ref: str
    confidence: float


@dataclass(frozen=True)
class Retrieval:
    """A retrieval result associated with a query and retrieval run."""

    query_id: str
    query: str
    run_id: str | None
    rank: int | None
    doc_id: str
    chunk_id: str | None
    score: float | None


class TraceBloomError(ValueError):
    """Raised when an input file is malformed or incomplete."""


def parse_float_env(name: str, default: float) -> float:
    """Read a float environment variable with a clear error on invalid input."""

    raw = os.environ.get(name)
    if raw is None or raw == "":
        return default
    try:
        return float(raw)
    except ValueError as exc:
        raise TraceBloomError(f"{name} must be a number, got {raw!r}") from exc


def parse_doc_reference(value: str) -> tuple[str, str | None]:
    """Parse a document reference into `(doc_id, chunk_id)`.

    Supported forms include `doc://doc-id#chunk=chunk-id`, `doc://doc-id#part`,
    `doc-id#chunk=chunk-id`, and `doc-id#part`.
    """

    text = value.strip()
    if not text:
        raise TraceBloomError("empty document reference")

    if text.startswith("doc://"):
        parsed = urlparse(text)
        doc_id = f"{parsed.netloc}{parsed.path}".strip("/")
        fragment = parsed.fragment
    else:
        doc_id, sep, fragment = text.partition("#")
        fragment = fragment if sep else ""
        doc_id = doc_id.strip("/")

    if not doc_id:
        raise TraceBloomError(f"document reference has no doc id: {value!r}")

    chunk_id = None
    if fragment:
        params = parse_qs(fragment, keep_blank_values=False)
        if "chunk" in params and params["chunk"]:
            chunk_id = params["chunk"][0]
        elif "chunk_id" in params and params["chunk_id"]:
            chunk_id = params["chunk_id"][0]
        elif "=" not in fragment:
            chunk_id = fragment
    return doc_id, chunk_id


def extract_citations_from_text(
    text: str,
    *,
    query_id: str,
    query: str,
    input_ref: str,
    default_confidence: float,
) -> list[Citation]:
    """Extract `doc://` Markdown links and `[[doc#chunk=...]]` citations."""

    citations: list[Citation] = []

    for match in re.finditer(r"\[[^\]]+\]\((doc://[^)\s]+)\)", text):
        raw = match.group(1)
        doc_id, chunk_id = parse_doc_reference(raw)
        citations.append(
            Citation(query_id, query, doc_id, chunk_id, raw, input_ref, default_confidence)
        )

    for match in re.finditer(r"\[\[([A-Za-z0-9._:/-]+(?:#(?:chunk=|chunk_id=)?[A-Za-z0-9._:/-]+)?)\]\]", text):
        raw_ref = match.group(1)
        doc_id, chunk_id = parse_doc_reference(raw_ref)
        citations.append(
            Citation(
                query_id,
                query,
                doc_id,
                chunk_id,
                f"[[{raw_ref}]]",
                input_ref,
                default_confidence,
            )
        )

    return dedupe_citations(citations)


def dedupe_citations(citations: Iterable[Citation]) -> list[Citation]:
    """Deduplicate citations while preserving first-seen order."""

    seen: set[tuple[str, str, str]] = set()
    result: list[Citation] = []
    for citation in citations:
        key = (citation.query_id, citation.doc_id, citation.chunk_id or "")
        if key in seen:
            continue
        seen.add(key)
        result.append(citation)
    return result


def parse_markdown_answers(text: str, input_ref: str, default_confidence: float) -> list[Citation]:
    """Parse one Markdown answer file into citation-backed positives."""

    query_id_match = re.search(r"(?im)^\s*Query ID:\s*(\S+)\s*$", text)
    query_match = re.search(r"(?im)^\s*Query:\s*(.+?)\s*$", text)
    if not query_id_match:
        raise TraceBloomError(f"{input_ref}: missing 'Query ID: ...' line")
    if not query_match:
        raise TraceBloomError(f"{input_ref}: missing 'Query: ...' line")

    return extract_citations_from_text(
        text,
        query_id=query_id_match.group(1),
        query=query_match.group(1).strip(),
        input_ref=input_ref,
        default_confidence=default_confidence,
    )


def parse_jsonl_answers(text: str, input_ref: str, default_confidence: float) -> list[Citation]:
    """Parse JSONL answer exports with optional citation arrays."""

    citations: list[Citation] = []
    for line_number, raw_line in enumerate(text.splitlines(), start=1):
        if not raw_line.strip():
            continue
        try:
            obj = json.loads(raw_line)
        except json.JSONDecodeError as exc:
            raise TraceBloomError(f"{input_ref}:{line_number}: invalid JSON: {exc.msg}") from exc
        if not isinstance(obj, dict):
            raise TraceBloomError(f"{input_ref}:{line_number}: expected a JSON object")

        query_id = str(obj.get("query_id") or obj.get("id") or f"line-{line_number}")
        query = str(obj.get("query") or obj.get("user_query") or "")
        if not query:
            raise TraceBloomError(f"{input_ref}:{line_number}: missing query")

        for item in obj.get("citations") or []:
            citations.append(coerce_citation(item, query_id, query, input_ref, default_confidence))

        answer = obj.get("answer")
        if isinstance(answer, str):
            citations.extend(
                extract_citations_from_text(
                    answer,
                    query_id=query_id,
                    query=query,
                    input_ref=input_ref,
                    default_confidence=default_confidence,
                )
            )
    return dedupe_citations(citations)


def coerce_citation(
    item: Any,
    query_id: str,
    query: str,
    input_ref: str,
    default_confidence: float,
) -> Citation:
    """Convert a manifest or JSONL citation value into a Citation."""

    confidence = default_confidence
    if isinstance(item, str):
        doc_id, chunk_id = parse_doc_reference(item)
        return Citation(query_id, query, doc_id, chunk_id, item, input_ref, confidence)

    if not isinstance(item, dict):
        raise TraceBloomError(f"{input_ref}: citation must be a string or object")

    raw_ref = item.get("uri") or item.get("citation") or item.get("ref")
    if raw_ref:
        doc_id, chunk_id = parse_doc_reference(str(raw_ref))
    else:
        doc_id = str(item.get("doc_id") or "").strip()
        chunk_id = item.get("chunk_id")
        if chunk_id is not None:
            chunk_id = str(chunk_id)
        if not doc_id:
            raise TraceBloomError(f"{input_ref}: citation object missing doc_id or uri")

    if "confidence" in item:
        try:
            confidence = float(item["confidence"])
        except (TypeError, ValueError) as exc:
            raise TraceBloomError(f"{input_ref}: citation confidence must be numeric") from exc
    citation_text = str(raw_ref or (f"{doc_id}#{chunk_id}" if chunk_id else doc_id))
    return Citation(query_id, query, doc_id, chunk_id, citation_text, input_ref, confidence)


def parse_citation_manifest(text: str, input_ref: str, default_confidence: float) -> list[Citation]:
    """Parse a JSON or JSONL citation manifest."""

    stripped = text.lstrip()
    if stripped.startswith("[") or stripped.startswith("{"):
        try:
            data = json.loads(text)
        except json.JSONDecodeError as exc:
            raise TraceBloomError(f"{input_ref}: invalid JSON: {exc.msg}") from exc
        if isinstance(data, dict):
            entries = data["citations"] if "citations" in data else [data]
        else:
            entries = data
        if not isinstance(entries, list):
            raise TraceBloomError(f"{input_ref}: citation manifest must be a list or object with citations")
    else:
        entries = []
        for line_number, raw_line in enumerate(text.splitlines(), start=1):
            if not raw_line.strip():
                continue
            try:
                entries.append(json.loads(raw_line))
            except json.JSONDecodeError as exc:
                raise TraceBloomError(f"{input_ref}:{line_number}: invalid JSON: {exc.msg}") from exc

    citations: list[Citation] = []
    for index, entry in enumerate(entries, start=1):
        if not isinstance(entry, dict):
            raise TraceBloomError(f"{input_ref}:{index}: manifest entry must be an object")
        query_id = str(entry.get("query_id") or "")
        query = str(entry.get("query") or "")
        if not query_id or not query:
            raise TraceBloomError(f"{input_ref}:{index}: manifest entry requires query_id and query")
        citations.append(coerce_citation(entry, query_id, query, input_ref, default_confidence))
    return dedupe_citations(citations)


def parse_retrieval_log(text: str, input_ref: str) -> list[Retrieval]:
    """Parse retrieval log JSONL into Retrieval objects."""

    retrievals: list[Retrieval] = []
    for line_number, raw_line in enumerate(text.splitlines(), start=1):
        if not raw_line.strip():
            continue
        try:
            obj = json.loads(raw_line)
        except json.JSONDecodeError as exc:
            raise TraceBloomError(f"{input_ref}:{line_number}: invalid JSON: {exc.msg}") from exc
        if not isinstance(obj, dict):
            raise TraceBloomError(f"{input_ref}:{line_number}: expected a JSON object")

        query_id = str(obj.get("query_id") or "")
        query = str(obj.get("query") or "")
        doc_id = str(obj.get("doc_id") or "").strip()
        if not query_id or not query or not doc_id:
            raise TraceBloomError(
                f"{input_ref}:{line_number}: retrieval requires query_id, query, and doc_id"
            )

        rank = obj.get("rank")
        score = obj.get("score")
        retrievals.append(
            Retrieval(
                query_id=query_id,
                query=query,
                run_id=str(obj["run_id"]) if obj.get("run_id") is not None else None,
                rank=int(rank) if rank is not None else None,
                doc_id=doc_id,
                chunk_id=str(obj["chunk_id"]) if obj.get("chunk_id") is not None else None,
                score=float(score) if score is not None else None,
            )
        )
    return retrievals


def load_answer_file(path: Path, default_confidence: float) -> list[Citation]:
    """Load Markdown or JSONL answer traces from a file."""

    text = path.read_text(encoding="utf-8")
    input_ref = path.as_posix()
    if path.suffix.lower() == ".jsonl":
        return parse_jsonl_answers(text, input_ref, default_confidence)
    return parse_markdown_answers(text, input_ref, default_confidence)


def load_citation_manifest_file(path: Path, default_confidence: float) -> list[Citation]:
    """Load JSON or JSONL citation manifest traces from a file."""

    return parse_citation_manifest(path.read_text(encoding="utf-8"), path.as_posix(), default_confidence)


def load_retrieval_log_file(path: Path) -> list[Retrieval]:
    """Load retrieval logs from a JSONL file."""

    return parse_retrieval_log(path.read_text(encoding="utf-8"), path.as_posix())


def build_dataset(
    citations: Iterable[Citation],
    retrievals: Iterable[Retrieval],
    *,
    max_negatives_per_query: int = 3,
    max_negative_rank: int = 20,
    min_negative_score: float = 0.0,
    high_impact_rank: int = 2,
) -> dict[str, Any]:
    """Build positive and implicit-negative dataset records.

    Returns a dictionary with `records`, `review_queue`, and `summary` keys.
    """

    citation_list = dedupe_citations(citations)
    retrieval_list = list(retrievals)

    retrieval_by_exact: dict[tuple[str, str, str], Retrieval] = {}
    retrieval_by_doc: dict[tuple[str, str], list[Retrieval]] = {}
    retrievals_by_query: dict[str, list[Retrieval]] = {}
    for retrieval in retrieval_list:
        exact_key = (retrieval.query_id, retrieval.doc_id, retrieval.chunk_id or "")
        retrieval_by_exact.setdefault(exact_key, retrieval)
        retrieval_by_doc.setdefault((retrieval.query_id, retrieval.doc_id), []).append(retrieval)
        retrievals_by_query.setdefault(retrieval.query_id, []).append(retrieval)

    records: list[dict[str, Any]] = []
    review_queue: list[dict[str, Any]] = []
    positive_keys: set[tuple[str, str, str]] = set()
    positive_doc_wildcards: set[tuple[str, str]] = set()

    for citation in citation_list:
        positive_keys.add((citation.query_id, citation.doc_id, citation.chunk_id or ""))
        if citation.chunk_id is None:
            positive_doc_wildcards.add((citation.query_id, citation.doc_id))

        matched = retrieval_by_exact.get((citation.query_id, citation.doc_id, citation.chunk_id or ""))
        if matched is None and citation.chunk_id is None:
            matched = (retrieval_by_doc.get((citation.query_id, citation.doc_id)) or [None])[0]

        record = {
            "query_id": citation.query_id,
            "query": citation.query,
            "doc_id": citation.doc_id,
            "chunk_id": citation.chunk_id,
            "label": "positive",
            "source": "citation+retrieval" if matched else "citation",
            "confidence": round(citation.confidence, 3),
            "run_id": matched.run_id if matched else None,
            "rank": matched.rank if matched else None,
            "score": matched.score if matched else None,
            "evidence": {
                "citation": citation.citation,
                "input": citation.input_ref,
                "matched_retrieval": bool(matched),
            },
        }
        records.append(drop_none(record))

        if citation.chunk_id is None:
            review_queue.append(
                {
                    "query_id": citation.query_id,
                    "doc_id": citation.doc_id,
                    "chunk_id": None,
                    "reason": "citation_missing_chunk_id",
                    "severity": "medium",
                    "evidence": {"citation": citation.citation, "input": citation.input_ref},
                }
            )
        if retrieval_list and not matched:
            review_queue.append(
                {
                    "query_id": citation.query_id,
                    "doc_id": citation.doc_id,
                    "chunk_id": citation.chunk_id,
                    "reason": "positive_citation_not_found_in_retrieval_log",
                    "severity": "medium",
                    "evidence": {"citation": citation.citation, "input": citation.input_ref},
                }
            )

    for query_id in sorted(retrievals_by_query):
        added = 0
        query_retrievals = sorted(
            retrievals_by_query[query_id],
            key=lambda item: (item.rank if item.rank is not None else 10**9, item.doc_id, item.chunk_id or ""),
        )
        for retrieval in query_retrievals:
            if added >= max_negatives_per_query:
                break
            if is_positive_retrieval(retrieval, positive_keys, positive_doc_wildcards):
                continue
            if retrieval.rank is not None and retrieval.rank > max_negative_rank:
                continue
            if retrieval.score is not None and retrieval.score < min_negative_score:
                continue

            records.append(
                {
                    "query_id": retrieval.query_id,
                    "query": retrieval.query,
                    "doc_id": retrieval.doc_id,
                    "chunk_id": retrieval.chunk_id,
                    "label": "implicit_negative_candidate",
                    "source": "retrieved_unused",
                    "confidence": implicit_negative_confidence(retrieval.rank),
                    "run_id": retrieval.run_id,
                    "rank": retrieval.rank,
                    "score": retrieval.score,
                    "evidence": {
                        "reason": "retrieved for the query but absent from confirmed citations",
                        "safeguard": "candidate only; require review before treating as a true negative",
                    },
                }
            )
            added += 1

            if retrieval.rank is not None and retrieval.rank <= high_impact_rank:
                review_queue.append(
                    {
                        "query_id": retrieval.query_id,
                        "doc_id": retrieval.doc_id,
                        "chunk_id": retrieval.chunk_id,
                        "reason": "high_rank_retrieved_but_unused",
                        "severity": "high",
                        "evidence": {
                            "rank": retrieval.rank,
                            "score": retrieval.score,
                            "run_id": retrieval.run_id,
                        },
                    }
                )

    query_ids = {item.query_id for item in citation_list} | {item.query_id for item in retrieval_list}
    summary = {
        "queries": len(query_ids),
        "positives": sum(1 for record in records if record["label"] == "positive"),
        "implicit_negative_candidates": sum(
            1 for record in records if record["label"] == "implicit_negative_candidate"
        ),
        "review_items": len(review_queue),
    }
    return {"records": [drop_none(record) for record in records], "review_queue": review_queue, "summary": summary}


def is_positive_retrieval(
    retrieval: Retrieval,
    positive_keys: set[tuple[str, str, str]],
    positive_doc_wildcards: set[tuple[str, str]],
) -> bool:
    """Return true if a retrieval is already covered by a positive citation."""

    exact_key = (retrieval.query_id, retrieval.doc_id, retrieval.chunk_id or "")
    return exact_key in positive_keys or (retrieval.query_id, retrieval.doc_id) in positive_doc_wildcards


def implicit_negative_confidence(rank: int | None) -> float:
    """Score confidence for an implicit negative candidate deterministically."""

    if rank is None:
        return 0.4
    return round(max(0.2, min(0.65, 0.55 - 0.03 * (rank - 1))), 3)


def drop_none(value: Any) -> Any:
    """Recursively remove keys with `None` values from dictionaries."""

    if isinstance(value, dict):
        return {key: drop_none(item) for key, item in value.items() if item is not None}
    if isinstance(value, list):
        return [drop_none(item) for item in value]
    return value


def write_jsonl(records: Iterable[dict[str, Any]], path: Path | None) -> None:
    """Write records as deterministic JSONL to a path or stdout."""

    lines = [json.dumps(record, sort_keys=True, separators=(",", ":")) for record in records]
    text = "\n".join(lines) + ("\n" if lines else "")
    if path is None:
        sys.stdout.write(text)
    else:
        path.write_text(text, encoding="utf-8")


def build_dataset_from_texts(
    answers_text: str,
    retrieval_log_text: str,
    *,
    input_ref: str = "sample",
    default_confidence: float = 0.95,
    max_negatives_per_query: int = 3,
) -> dict[str, Any]:
    """Build a dataset from in-memory Markdown answers and JSONL retrieval logs."""

    citations = parse_markdown_answers(answers_text, input_ref, default_confidence)
    retrievals = parse_retrieval_log(retrieval_log_text, f"{input_ref}.retrieval_log")
    return build_dataset(
        citations,
        retrievals,
        max_negatives_per_query=max_negatives_per_query,
        min_negative_score=0.0,
    )


def run_selftest() -> int:
    """Run a deterministic no-key self-test on built-in sample data."""

    result = build_dataset_from_texts(
        SAMPLE_ANSWERS,
        SAMPLE_RETRIEVAL_LOG,
        input_ref="selftest.md",
        default_confidence=0.95,
        max_negatives_per_query=3,
    )
    expected_summary = {
        "queries": 1,
        "positives": 2,
        "implicit_negative_candidates": 2,
        "review_items": 1,
    }
    if result["summary"] != expected_summary:
        raise TraceBloomError(f"self-test failed: expected {expected_summary}, got {result['summary']}")

    payload = {"ok": True, "summary": result["summary"], "first_record": result["records"][0]}
    print(json.dumps(payload, sort_keys=True, separators=(",", ":")))
    return 0


def build_parser() -> argparse.ArgumentParser:
    """Create the command-line parser."""

    parser = argparse.ArgumentParser(
        description="Build positive-trace JSONL datasets for RAG evaluation from citations and retrieval logs."
    )
    parser.add_argument("--answers", action="append", type=Path, help="Markdown or JSONL answer trace file; repeatable.")
    parser.add_argument("--citation-manifest", action="append", type=Path, help="JSON or JSONL citation manifest; repeatable.")
    parser.add_argument("--retrieval-log", type=Path, help="JSONL retrieval log.")
    parser.add_argument("--output", type=Path, help="Dataset JSONL output path. Defaults to stdout.")
    parser.add_argument("--review-output", type=Path, help="Optional review queue JSONL output path.")
    parser.add_argument("--max-negatives-per-query", type=int, default=3, help="Maximum implicit negative candidates per query.")
    parser.add_argument("--max-negative-rank", type=int, default=20, help="Only consider retrieved-unused candidates at or above this rank.")
    parser.add_argument("--high-impact-rank", type=int, default=2, help="Send unused retrievals at or above this rank to review.")
    parser.add_argument("--selftest", action="store_true", help="Run built-in sample data with no API key or external files.")
    return parser


def main(argv: list[str] | None = None) -> int:
    """CLI entry point."""

    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        if args.selftest or not any([args.answers, args.citation_manifest, args.retrieval_log]):
            return run_selftest()

        default_confidence = parse_float_env("TRACEBLOOM_DEFAULT_CONFIDENCE", 0.95)
        min_negative_score = parse_float_env("TRACEBLOOM_MIN_NEGATIVE_SCORE", 0.0)

        citations: list[Citation] = []
        for path in args.answers or []:
            if not path.exists():
                raise TraceBloomError(f"answer file not found: {path}")
            citations.extend(load_answer_file(path, default_confidence))

        for path in args.citation_manifest or []:
            if not path.exists():
                raise TraceBloomError(f"citation manifest not found: {path}")
            citations.extend(load_citation_manifest_file(path, default_confidence))

        retrievals: list[Retrieval] = []
        if args.retrieval_log:
            if not args.retrieval_log.exists():
                raise TraceBloomError(f"retrieval log not found: {args.retrieval_log}")
            retrievals = load_retrieval_log_file(args.retrieval_log)

        if not citations and not retrievals:
            raise TraceBloomError("no usable citations or retrieval records found")
        if args.max_negatives_per_query < 0:
            raise TraceBloomError("--max-negatives-per-query must be >= 0")

        result = build_dataset(
            citations,
            retrievals,
            max_negatives_per_query=args.max_negatives_per_query,
            max_negative_rank=args.max_negative_rank,
            min_negative_score=min_negative_score,
            high_impact_rank=args.high_impact_rank,
        )
        write_jsonl(result["records"], args.output)
        if args.review_output:
            write_jsonl(result["review_queue"], args.review_output)
        return 0
    except TraceBloomError as exc:
        parser.exit(2, f"tracebloom: error: {exc}\n")


if __name__ == "__main__":
    raise SystemExit(main())
