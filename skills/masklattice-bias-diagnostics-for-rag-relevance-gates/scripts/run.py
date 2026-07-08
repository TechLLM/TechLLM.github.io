#!/usr/bin/env python3
"""MaskLattice: perturbation diagnostics for RAG relevance gates."""

from __future__ import annotations

import argparse
import csv
import json
import math
import os
import re
import shlex
import statistics
import subprocess
import sys
from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple


MASK = "[MASK]"
NON_EVIDENTIAL_MASKS = {"mask_title", "mask_metadata", "mask_headers"}
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
    "how",
    "in",
    "is",
    "it",
    "of",
    "on",
    "or",
    "should",
    "that",
    "the",
    "to",
    "under",
    "what",
    "when",
    "with",
}


@dataclass
class Query:
    id: str
    question: str


@dataclass
class Document:
    id: str
    title: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    headers: List[str] = field(default_factory=list)
    summary: str = ""
    paragraphs: List[str] = field(default_factory=list)
    source: str = ""


@dataclass
class Variant:
    doc: Document
    mask_name: str
    mask_target: str
    evidence_mask: bool


def tokenize(text: str) -> List[str]:
    return [
        token
        for token in re.findall(r"[a-z0-9]+", text.lower())
        if len(token) > 1 and token not in STOPWORDS
    ]


def split_paragraphs(text: str) -> List[str]:
    parts = re.split(r"\n\s*\n+", text.strip())
    return [part.strip() for part in parts if part.strip()]


def parse_frontmatter(markdown: str) -> Tuple[Dict[str, str], str]:
    lines = markdown.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}, markdown
    metadata: Dict[str, str] = {}
    end_index = None
    for idx, line in enumerate(lines[1:], start=1):
        if line.strip() == "---":
            end_index = idx
            break
        if ":" in line:
            key, value = line.split(":", 1)
            metadata[key.strip()] = value.strip().strip('"')
    if end_index is None:
        return {}, markdown
    return metadata, "\n".join(lines[end_index + 1 :]).strip()


def markdown_to_doc(path: Path) -> Document:
    raw = path.read_text(encoding="utf-8")
    metadata, body = parse_frontmatter(raw)
    title = metadata.get("title", "")
    headers: List[str] = []
    non_heading_lines: List[str] = []

    for line in body.splitlines():
        heading = re.match(r"^(#{1,6})\s+(.+?)\s*$", line)
        if heading:
            text = heading.group(2).strip()
            headers.append(text)
            if not title and heading.group(1) == "#":
                title = text
            continue
        non_heading_lines.append(line)

    paragraphs = split_paragraphs("\n".join(non_heading_lines))
    summary = metadata.get("summary", "")
    if not summary and paragraphs:
        first = paragraphs[0]
        if first.lower().startswith("summary:"):
            summary = first.split(":", 1)[1].strip()
            paragraphs = paragraphs[1:]
        else:
            summary = first[:300]

    return Document(
        id=metadata.get("id", path.stem),
        title=title or path.stem.replace("_", " ").title(),
        metadata={key: value for key, value in metadata.items() if key not in {"id", "title", "summary"}},
        headers=headers,
        summary=summary,
        paragraphs=paragraphs,
        source=str(path.as_posix()),
    )


def ensure_list(value: Any) -> List[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item) for item in value if str(item).strip()]
    return split_paragraphs(str(value))


def json_object_to_doc(obj: Mapping[str, Any], fallback_id: str, source: str) -> Document:
    headers = [str(item) for item in obj.get("headers", [])] if isinstance(obj.get("headers"), list) else []
    paragraphs: List[str] = []

    for key in ("body", "content", "text"):
        if key in obj:
            paragraphs.extend(ensure_list(obj.get(key)))

    sections = obj.get("sections")
    if isinstance(sections, list):
        for section in sections:
            if not isinstance(section, Mapping):
                paragraphs.append(str(section))
                continue
            heading = section.get("heading") or section.get("title")
            if heading:
                headers.append(str(heading))
            for key in ("body", "content", "text"):
                if key in section:
                    paragraphs.extend(ensure_list(section.get(key)))

    metadata = obj.get("metadata", {})
    if not isinstance(metadata, Mapping):
        metadata = {"metadata": str(metadata)}

    doc_id = str(obj.get("id") or obj.get("doc_id") or fallback_id)
    return Document(
        id=doc_id,
        title=str(obj.get("title") or obj.get("name") or doc_id),
        metadata=dict(metadata),
        headers=headers,
        summary=str(obj.get("summary") or obj.get("abstract") or ""),
        paragraphs=paragraphs,
        source=source,
    )


def json_to_docs(path: Path) -> List[Document]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, list):
        return [
            json_object_to_doc(item, f"{path.stem}_{idx + 1}", path.as_posix())
            for idx, item in enumerate(data)
            if isinstance(item, Mapping)
        ]
    if isinstance(data, Mapping):
        return [json_object_to_doc(data, path.stem, path.as_posix())]
    raise ValueError(f"Unsupported JSON document shape in {path}")


def load_queries(path: Optional[Path]) -> List[Query]:
    if path is None:
        default = Path("examples/questions.jsonl")
        path = default if default.exists() else None
    if path is None:
        return [
            Query("q1", "How should a RAG relevance gate avoid metadata bias?"),
            Query("q2", "Which retrieval diagnostics measure ranking instability?"),
        ]

    queries: List[Query] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            line = line.strip()
            if not line:
                continue
            obj = json.loads(line)
            question = obj.get("question") or obj.get("query")
            if not question:
                raise ValueError(f"Missing question on line {line_number} in {path}")
            queries.append(Query(str(obj.get("id") or f"q{line_number}"), str(question)))
    return queries


def built_in_docs() -> List[Document]:
    return [
        Document(
            id="rag_gate_eval",
            title="RAG Gate Evaluation",
            metadata={"topic": "retrieval", "label": "relevance"},
            headers=["Evidence grounding", "Masking checks"],
            summary="Relevance gates should score retrieved passages by answer evidence rather than metadata labels.",
            paragraphs=[
                "A robust RAG relevance gate compares the user question with concrete claims in the candidate passage.",
                "Masking titles, labels, and headers can reveal whether a scorer depends on non-evidential cues.",
                "Ranking shifts and score variance are useful regression metrics for retrieval audits.",
            ],
            source="built-in",
        ),
        Document(
            id="dashboard_notes",
            title="Dashboard Design Notes",
            metadata={"topic": "interface", "label": "product"},
            headers=["Tables", "Controls"],
            summary="Operational dashboards should make repeated workflows easy to scan.",
            paragraphs=[
                "Dense tables, filters, and predictable controls help users compare records quickly.",
                "This note is about interface design, not retrieval evaluation or relevance gates.",
            ],
            source="built-in",
        ),
        Document(
            id="reranker_monitoring",
            title="Reranker Monitoring",
            metadata={"topic": "retrieval", "label": "monitoring"},
            headers=["Ranking stability", "CI checks"],
            summary="Reranker audits can track ranking instability after controlled document perturbations.",
            paragraphs=[
                "Score variance across masked variants can identify brittle relevance decisions.",
                "Continuous integration can fail a regression when irrelevant masks create large ranking changes.",
            ],
            source="built-in",
        ),
    ]


def load_documents(path: Optional[Path]) -> List[Document]:
    if path is None:
        default = Path("examples/docs")
        path = default if default.exists() else None
    if path is None:
        return built_in_docs()

    files: List[Path]
    if path.is_dir():
        files = sorted(
            item
            for item in path.rglob("*")
            if item.is_file() and item.suffix.lower() in {".md", ".markdown", ".json"}
        )
    else:
        files = [path]

    docs: List[Document] = []
    for file_path in files:
        suffix = file_path.suffix.lower()
        if suffix in {".md", ".markdown"}:
            docs.append(markdown_to_doc(file_path))
        elif suffix == ".json":
            docs.extend(json_to_docs(file_path))

    if not docs:
        raise ValueError(f"No Markdown or JSON documents found at {path}")
    return docs


def render_document(doc: Document) -> str:
    lines: List[str] = []
    if doc.title:
        lines.append(f"# {doc.title}")
    if doc.metadata:
        lines.append("Metadata:")
        for key in sorted(doc.metadata):
            lines.append(f"- {key}: {doc.metadata[key]}")
    if doc.summary:
        lines.append(f"Summary: {doc.summary}")
    for header in doc.headers:
        lines.append(f"## {header}")
    lines.extend(doc.paragraphs)
    return "\n\n".join(lines).strip()


def masked_copy(doc: Document, mask_name: str) -> Variant:
    copied = replace(
        doc,
        metadata=dict(doc.metadata),
        headers=list(doc.headers),
        paragraphs=list(doc.paragraphs),
    )

    if mask_name == "original":
        return Variant(copied, "original", "none", False)
    if mask_name == "mask_title":
        copied.title = MASK
        return Variant(copied, mask_name, "title", False)
    if mask_name == "mask_metadata":
        copied.metadata = {key: MASK for key in copied.metadata} if copied.metadata else {"metadata": MASK}
        return Variant(copied, mask_name, "metadata", False)
    if mask_name == "mask_headers":
        copied.headers = [MASK for _ in copied.headers] if copied.headers else [MASK]
        return Variant(copied, mask_name, "headers", False)
    if mask_name == "mask_summary":
        copied.summary = MASK if copied.summary else MASK
        return Variant(copied, mask_name, "summary", True)

    if not copied.paragraphs:
        copied.paragraphs = [MASK]
        return Variant(copied, mask_name, "body", True)

    if mask_name == "mask_leading_window":
        copied.paragraphs[0] = MASK
        return Variant(copied, mask_name, "leading paragraph", True)
    if mask_name == "mask_trailing_window":
        copied.paragraphs[-1] = MASK
        return Variant(copied, mask_name, "trailing paragraph", True)
    if mask_name == "mask_neighbor_window":
        midpoint = len(copied.paragraphs) // 2
        start = max(0, midpoint - 1)
        end = min(len(copied.paragraphs), midpoint + 2)
        copied.paragraphs[start:end] = [MASK]
        return Variant(copied, mask_name, "middle neighboring paragraphs", True)

    raise ValueError(f"Unknown mask name: {mask_name}")


def build_variants(doc: Document) -> List[Variant]:
    return [
        masked_copy(doc, "original"),
        masked_copy(doc, "mask_title"),
        masked_copy(doc, "mask_metadata"),
        masked_copy(doc, "mask_headers"),
        masked_copy(doc, "mask_summary"),
        masked_copy(doc, "mask_leading_window"),
        masked_copy(doc, "mask_trailing_window"),
        masked_copy(doc, "mask_neighbor_window"),
    ]


def lexical_score(question: str, document: str) -> float:
    q_tokens = tokenize(question)
    d_tokens = tokenize(document)
    if not q_tokens or not d_tokens:
        return 0.0

    q_counts: Dict[str, int] = {}
    d_counts: Dict[str, int] = {}
    for token in q_tokens:
        q_counts[token] = q_counts.get(token, 0) + 1
    for token in d_tokens:
        d_counts[token] = d_counts.get(token, 0) + 1

    overlap = sum(min(q_counts[token], d_counts.get(token, 0)) for token in q_counts)
    cosine = overlap / math.sqrt(sum(q_counts.values()) * sum(d_counts.values()))
    phrase_bonus = 0.0
    lower_doc = document.lower()
    for phrase in ("rag relevance", "relevance gate", "ranking instability", "retrieval audit"):
        if phrase in question.lower() and phrase in lower_doc:
            phrase_bonus += 0.08
    return round(min(1.0, cosine + phrase_bonus), 6)


def score_with_adapter(command: str, cases: Sequence[Mapping[str, Any]]) -> Dict[str, float]:
    completed = subprocess.run(
        shlex.split(command),
        input=json.dumps(list(cases)),
        text=True,
        capture_output=True,
        check=False,
    )
    if completed.returncode != 0:
        raise RuntimeError(
            f"Adapter failed with exit code {completed.returncode}: {completed.stderr.strip()}"
        )
    output = completed.stdout.strip()
    if not output:
        raise RuntimeError("Adapter returned no output")

    try:
        parsed = json.loads(output)
        if isinstance(parsed, list):
            if all(isinstance(item, (int, float)) for item in parsed):
                if len(parsed) != len(cases):
                    raise RuntimeError("Adapter score count does not match case count")
                return {
                    str(case["case_id"]): float(score)
                    for case, score in zip(cases, parsed)
                }
            scores: Dict[str, float] = {}
            for item in parsed:
                if not isinstance(item, Mapping):
                    raise RuntimeError("Adapter JSON array must contain numbers or objects")
                scores[str(item["case_id"])] = float(item["score"])
            return scores
    except json.JSONDecodeError:
        pass

    scores = {}
    for line in output.splitlines():
        item = json.loads(line)
        scores[str(item["case_id"])] = float(item["score"])
    return scores


def load_score_file(path: Path) -> Dict[str, float]:
    scores: Dict[str, float] = {}
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            line = line.strip()
            if not line:
                continue
            item = json.loads(line)
            case_id = item.get("case_id") or item.get("id")
            if case_id is None or "score" not in item:
                raise ValueError(f"Score file line {line_number} needs case_id and score")
            scores[str(case_id)] = float(item["score"])
    return scores


def rank_scores(items: Iterable[Tuple[str, float]]) -> Dict[str, int]:
    ranked = sorted(items, key=lambda item: (-item[1], item[0]))
    return {doc_id: rank + 1 for rank, (doc_id, _) in enumerate(ranked)}


def build_cases(queries: Sequence[Query], docs: Sequence[Document]) -> Tuple[List[Dict[str, Any]], Dict[Tuple[str, str, str], Variant]]:
    cases: List[Dict[str, Any]] = []
    variant_lookup: Dict[Tuple[str, str, str], Variant] = {}
    for query in queries:
        for doc in docs:
            for variant in build_variants(doc):
                case_id = f"{query.id}|{doc.id}|{variant.mask_name}"
                variant_lookup[(query.id, doc.id, variant.mask_name)] = variant
                cases.append(
                    {
                        "case_id": case_id,
                        "query_id": query.id,
                        "doc_id": doc.id,
                        "mask_name": variant.mask_name,
                        "mask_target": variant.mask_target,
                        "question": query.question,
                        "document": render_document(variant.doc),
                    }
                )
    return cases, variant_lookup


def compute_rows(
    queries: Sequence[Query],
    docs: Sequence[Document],
    cases: Sequence[Mapping[str, Any]],
    scores: Mapping[str, float],
    variant_lookup: Mapping[Tuple[str, str, str], Variant],
    scorer_name: str,
) -> List[Dict[str, Any]]:
    query_ids = [query.id for query in queries]
    doc_ids = [doc.id for doc in docs]
    mask_names = sorted({str(case["mask_name"]) for case in cases})

    score_by_key: Dict[Tuple[str, str, str], float] = {}
    for case in cases:
        case_id = str(case["case_id"])
        if case_id not in scores:
            raise ValueError(f"Missing score for case {case_id}")
        score_by_key[(str(case["query_id"]), str(case["doc_id"]), str(case["mask_name"]))] = float(scores[case_id])

    original_ranks: Dict[str, Dict[str, int]] = {}
    variant_ranks: Dict[Tuple[str, str], Dict[str, int]] = {}
    for query_id in query_ids:
        original_ranks[query_id] = rank_scores(
            (doc_id, score_by_key[(query_id, doc_id, "original")]) for doc_id in doc_ids
        )
        for mask_name in mask_names:
            variant_ranks[(query_id, mask_name)] = rank_scores(
                (doc_id, score_by_key[(query_id, doc_id, mask_name)]) for doc_id in doc_ids
            )

    rows: List[Dict[str, Any]] = []
    question_by_id = {query.id: query.question for query in queries}
    doc_by_id = {doc.id: doc for doc in docs}

    for query_id in query_ids:
        for doc_id in doc_ids:
            original_score = score_by_key[(query_id, doc_id, "original")]
            for mask_name in mask_names:
                variant = variant_lookup[(query_id, doc_id, mask_name)]
                score = score_by_key[(query_id, doc_id, mask_name)]
                original_rank = original_ranks[query_id][doc_id]
                variant_rank = variant_ranks[(query_id, mask_name)][doc_id]
                rows.append(
                    {
                        "query_id": query_id,
                        "question": question_by_id[query_id],
                        "doc_id": doc_id,
                        "doc_source": doc_by_id[doc_id].source,
                        "mask_name": mask_name,
                        "mask_target": variant.mask_target,
                        "evidence_mask": str(variant.evidence_mask).lower(),
                        "score": round(score, 6),
                        "original_score": round(original_score, 6),
                        "score_delta": round(score - original_score, 6),
                        "abs_score_delta": round(abs(score - original_score), 6),
                        "original_rank": original_rank,
                        "variant_rank": variant_rank,
                        "rank_shift": variant_rank - original_rank,
                        "abs_rank_shift": abs(variant_rank - original_rank),
                        "scorer": scorer_name,
                    }
                )
    return rows


def mean(values: Sequence[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def write_csv(rows: Sequence[Mapping[str, Any]], path: Path) -> None:
    fieldnames = [
        "query_id",
        "question",
        "doc_id",
        "doc_source",
        "mask_name",
        "mask_target",
        "evidence_mask",
        "score",
        "original_score",
        "score_delta",
        "abs_score_delta",
        "original_rank",
        "variant_rank",
        "rank_shift",
        "abs_rank_shift",
        "scorer",
    ]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def report_markdown(rows: Sequence[Mapping[str, Any]], threshold: float) -> str:
    non_original = [row for row in rows if row["mask_name"] != "original"]
    masks = sorted({str(row["mask_name"]) for row in non_original})

    lines = [
        "# MaskLattice Report",
        "",
        "This report summarizes score movement and ranking shifts under controlled document masks.",
        "",
        "## Aggregate Mask Diagnostics",
        "",
        "| Mask | Mean absolute score delta | Max absolute score delta | Mean absolute rank shift |",
        "| --- | ---: | ---: | ---: |",
    ]

    for mask_name in masks:
        mask_rows = [row for row in non_original if row["mask_name"] == mask_name]
        mean_delta = mean([float(row["abs_score_delta"]) for row in mask_rows])
        max_delta = max([float(row["abs_score_delta"]) for row in mask_rows], default=0.0)
        mean_rank = mean([float(row["abs_rank_shift"]) for row in mask_rows])
        lines.append(f"| {mask_name} | {mean_delta:.4f} | {max_delta:.4f} | {mean_rank:.2f} |")

    grouped: Dict[Tuple[str, str], List[Mapping[str, Any]]] = {}
    for row in rows:
        grouped.setdefault((str(row["query_id"]), str(row["doc_id"])), []).append(row)

    warnings: List[Tuple[str, str, float, float]] = []
    stable: List[Tuple[str, str, float]] = []
    for (query_id, doc_id), group_rows in grouped.items():
        non_evidential = [
            row
            for row in group_rows
            if str(row["mask_name"]) in NON_EVIDENTIAL_MASKS or str(row["mask_name"]) == "original"
        ]
        scores = [float(row["score"]) for row in non_evidential]
        if not scores:
            continue
        variance = statistics.pvariance(scores) if len(scores) > 1 else 0.0
        max_delta = max(float(row["abs_score_delta"]) for row in non_evidential)
        if max_delta >= threshold:
            warnings.append((query_id, doc_id, variance, max_delta))
        elif max_delta <= threshold / 2:
            stable.append((query_id, doc_id, max_delta))

    lines.extend(
        [
            "",
            "## Potential Inductive-Bias Warnings",
            "",
            f"Warning threshold: max absolute score delta >= {threshold:.3f} for non-evidential masks.",
            "",
        ]
    )

    if warnings:
        lines.extend(
            [
                "| Query | Document | Non-evidential score variance | Max absolute score delta |",
                "| --- | --- | ---: | ---: |",
            ]
        )
        for query_id, doc_id, variance, max_delta in sorted(warnings, key=lambda item: (-item[3], item[0], item[1])):
            lines.append(f"| {query_id} | {doc_id} | {variance:.6f} | {max_delta:.4f} |")
    else:
        lines.append("No query-document pairs crossed the warning threshold.")

    lines.extend(["", "## Stable Under Irrelevant Masks", ""])
    if stable:
        lines.extend(["| Query | Document | Max absolute score delta |", "| --- | --- | ---: |"])
        for query_id, doc_id, max_delta in sorted(stable, key=lambda item: (item[0], item[1])):
            lines.append(f"| {query_id} | {doc_id} | {max_delta:.4f} |")
    else:
        lines.append("No query-document pairs met the stable threshold.")

    evidence_rows = [row for row in non_original if str(row["evidence_mask"]) == "true"]
    lines.extend(
        [
            "",
            "## Evidence-Mask Movement",
            "",
            f"Mean absolute score delta for evidence-bearing masks: {mean([float(row['abs_score_delta']) for row in evidence_rows]):.4f}",
            f"Mean absolute rank shift for evidence-bearing masks: {mean([float(row['abs_rank_shift']) for row in evidence_rows]):.2f}",
            "",
            "## Interpretation Notes",
            "",
            "- Large movement after title, metadata, or header masks can indicate dependence on weak relevance cues.",
            "- Movement after summary or body-window masks is expected when those fields contain answer evidence.",
            "- Treat warnings as audit leads, not final judgments.",
        ]
    )
    return "\n".join(lines) + "\n"


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run MaskLattice perturbation diagnostics.")
    parser.add_argument("--queries", type=Path, help="JSONL questions file.")
    parser.add_argument("--docs", type=Path, help="Directory or file containing Markdown or JSON documents.")
    parser.add_argument("--out", type=Path, default=Path("masklattice_output"), help="Output directory.")
    parser.add_argument(
        "--adapter-cmd",
        default=os.environ.get("MASKLATTICE_SCORER_CMD", ""),
        help="Optional stdin/stdout scorer adapter command.",
    )
    parser.add_argument(
        "--score-file",
        type=Path,
        default=Path(os.environ["MASKLATTICE_SCORE_FILE"]) if os.environ.get("MASKLATTICE_SCORE_FILE") else None,
        help="Optional JSONL file with precomputed case_id and score values.",
    )
    parser.add_argument(
        "--warning-threshold",
        type=float,
        default=0.12,
        help="Max absolute score delta threshold for non-evidential mask warnings.",
    )
    return parser.parse_args(argv)


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = parse_args(argv)
    queries = load_queries(args.queries)
    docs = load_documents(args.docs)
    cases, variant_lookup = build_cases(queries, docs)

    if args.score_file:
        scores = load_score_file(args.score_file)
        scorer_name = f"score_file:{args.score_file.as_posix()}"
    elif args.adapter_cmd:
        scores = score_with_adapter(args.adapter_cmd, cases)
        scorer_name = f"adapter:{args.adapter_cmd}"
    else:
        scores = {
            str(case["case_id"]): lexical_score(str(case["question"]), str(case["document"]))
            for case in cases
        }
        scorer_name = "lexical-baseline"

    rows = compute_rows(queries, docs, cases, scores, variant_lookup, scorer_name)
    args.out.mkdir(parents=True, exist_ok=True)
    csv_path = args.out / "diagnostics.csv"
    report_path = args.out / "report.md"
    write_csv(rows, csv_path)
    report_path.write_text(report_markdown(rows, args.warning_threshold), encoding="utf-8")

    print(f"queries: {len(queries)}")
    print(f"documents: {len(docs)}")
    print(f"cases: {len(cases)}")
    print(f"scorer: {scorer_name}")
    print(f"csv: {csv_path.as_posix()}")
    print(f"report: {report_path.as_posix()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
