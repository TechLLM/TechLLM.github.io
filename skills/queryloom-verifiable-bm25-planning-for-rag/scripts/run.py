#!/usr/bin/env python3
"""QueryLoom: build deterministic BM25 retrieval plans for local RAG corpora.

The script is intentionally small and self-contained. It analyzes Markdown or
plain-text corpora with TF-IDF, proposes rare terms, creates synonym slots, and
emits a JSON retrieval plan that can be reviewed before running BM25 search.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import re
import sys
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Sequence


TOKEN_RE = re.compile(r"[a-z0-9]+(?:[-'][a-z0-9]+)?")
SUPPORTED_SUFFIXES = {".md", ".txt", ".text"}

STOPWORDS = frozenset(
    {
        "a",
        "an",
        "and",
        "are",
        "as",
        "at",
        "be",
        "before",
        "by",
        "can",
        "for",
        "from",
        "how",
        "in",
        "into",
        "is",
        "it",
        "its",
        "of",
        "on",
        "or",
        "that",
        "the",
        "their",
        "then",
        "to",
        "use",
        "uses",
        "when",
        "with",
    }
)

DOMAIN_BOOST_TERMS = frozenset(
    {
        "bm25",
        "corpus",
        "evidence",
        "exclusion",
        "failure",
        "failures",
        "planning",
        "query",
        "queryloom",
        "rag",
        "rare",
        "retrieval",
        "retrieval_plan",
        "search",
        "synonym",
        "synonyms",
        "tf-idf",
    }
)

SYNONYM_SLOTS = (
    {
        "slot": "rag",
        "triggers": {"rag", "generation"},
        "terms": ["rag", "retrieval augmented generation", "grounded generation"],
    },
    {
        "slot": "retrieval",
        "triggers": {"retrieval", "retriever", "search"},
        "terms": ["retrieval", "search", "lookup"],
    },
    {
        "slot": "bm25",
        "triggers": {"bm25", "lexical", "sparse"},
        "terms": ["bm25", "lexical search", "sparse retrieval"],
    },
    {
        "slot": "planning",
        "triggers": {"plan", "planning", "strategy"},
        "terms": ["planning", "strategy", "control plane"],
    },
    {
        "slot": "failure",
        "triggers": {"failure", "failures", "miss", "misses"},
        "terms": ["failure", "miss", "retrieval error"],
    },
    {
        "slot": "evidence",
        "triggers": {"evidence", "citation", "support"},
        "terms": ["evidence", "citation", "supporting passage"],
    },
)

SAMPLE_QUESTION = "How can QueryLoom reduce RAG retrieval failures with BM25 planning?"


@dataclass(frozen=True)
class Document:
    """A corpus document with a stable identifier, source label, and text."""

    id: str
    source: str
    text: str


@dataclass(frozen=True)
class VocabularyStats:
    """TF-IDF statistics used to build the retrieval plan."""

    tokens_by_doc: dict[str, list[str]]
    document_frequency: Counter[str]
    max_tfidf: dict[str, float]
    token_count: int
    vocabulary_size: int


SAMPLE_DOCUMENTS = (
    Document(
        id="sample-1",
        source="sample/queryloom.md",
        text=(
            "QueryLoom creates retrieval_plan.json files before retrieval. "
            "The plan decomposes user questions, names evidence requirements, "
            "and turns RAG intent into BM25 query strings."
        ),
    ),
    Document(
        id="sample-2",
        source="sample/bm25.md",
        text=(
            "BM25 retrieval rewards rare exact terms in a corpus. TF-IDF can "
            "surface identifiers, product names, and unusual phrases that "
            "ordinary semantic search might skip."
        ),
    ),
    Document(
        id="sample-3",
        source="sample/failures.md",
        text=(
            "Retrieval failures often happen when a search system omits "
            "required evidence, overuses broad synonyms, or includes unrelated "
            "vector-only concepts."
        ),
    ),
)


def tokenize(text: str) -> list[str]:
    """Return normalized lexical tokens, excluding common stopwords."""

    tokens = []
    for match in TOKEN_RE.finditer(text.lower()):
        token = match.group(0).strip("'")
        if len(token) > 1 and token not in STOPWORDS:
            tokens.append(token)
    return tokens


def read_optional_api_key(env: dict[str, str] | None = None) -> bool:
    """Return whether an optional planner API key exists without exposing it."""

    values = os.environ if env is None else env
    return bool(values.get("QUERYLOOM_API_KEY") or values.get("OPENAI_API_KEY"))


def load_corpus(path_text: str) -> list[Document]:
    """Load Markdown or text documents from a file or directory."""

    corpus_path = Path(path_text)
    if not corpus_path.exists():
        raise ValueError(f"corpus path does not exist: {path_text}")

    if corpus_path.is_file():
        if corpus_path.suffix.lower() not in SUPPORTED_SUFFIXES:
            supported = ", ".join(sorted(SUPPORTED_SUFFIXES))
            raise ValueError(f"unsupported corpus file type: {corpus_path.suffix}; use {supported}")
        text = corpus_path.read_text(encoding="utf-8").strip()
        if not text:
            raise ValueError(f"corpus file is empty: {path_text}")
        return [Document(id="doc-1", source=corpus_path.name, text=text)]

    files = sorted(
        p
        for p in corpus_path.rglob("*")
        if p.is_file() and p.suffix.lower() in SUPPORTED_SUFFIXES
    )
    documents = []
    for index, file_path in enumerate(files, start=1):
        text = file_path.read_text(encoding="utf-8").strip()
        if not text:
            continue
        source = file_path.relative_to(corpus_path).as_posix()
        documents.append(Document(id=f"doc-{index}", source=source, text=text))

    if not documents:
        supported = ", ".join(sorted(SUPPORTED_SUFFIXES))
        raise ValueError(f"corpus directory contains no non-empty supported files: {supported}")
    return documents


def compute_vocabulary_stats(documents: Sequence[Document]) -> VocabularyStats:
    """Compute document frequency and max per-document TF-IDF for each term."""

    if not documents:
        raise ValueError("corpus must contain at least one document")

    tokens_by_doc = {doc.id: tokenize(doc.text) for doc in documents}
    document_frequency: Counter[str] = Counter()
    for tokens in tokens_by_doc.values():
        document_frequency.update(set(tokens))

    doc_count = len(documents)
    max_tfidf: dict[str, float] = {}
    token_count = 0

    for tokens in tokens_by_doc.values():
        counts = Counter(tokens)
        token_count += sum(counts.values())
        length = max(sum(counts.values()), 1)
        for term, count in counts.items():
            tf = count / length
            idf = math.log((doc_count + 1) / (document_frequency[term] + 1)) + 1.0
            score = tf * idf
            if score > max_tfidf.get(term, 0.0):
                max_tfidf[term] = score

    return VocabularyStats(
        tokens_by_doc=tokens_by_doc,
        document_frequency=document_frequency,
        max_tfidf=max_tfidf,
        token_count=token_count,
        vocabulary_size=len(document_frequency),
    )


def select_rare_terms(
    question: str, stats: VocabularyStats, max_terms: int = 8
) -> list[dict[str, object]]:
    """Select rare corpus terms, boosting terms that occur in the question."""

    question_terms = set(tokenize(question))
    ranked = []
    for term, tf_idf in stats.max_tfidf.items():
        if not term or term in STOPWORDS:
            continue
        rank_score = tf_idf
        if term in question_terms:
            rank_score *= 2.0
        if term in DOMAIN_BOOST_TERMS:
            rank_score *= 1.25
        ranked.append((rank_score, term))

    selected = sorted(ranked, key=lambda item: (-item[0], item[1]))[:max_terms]
    return [
        {
            "term": term,
            "tf_idf": round(stats.max_tfidf[term], 4),
            "document_frequency": int(stats.document_frequency[term]),
        }
        for _, term in selected
    ]


def decompose_question(question: str) -> list[str]:
    """Split a question into deterministic subquery intents."""

    stripped = question.strip().rstrip("?!.")
    if not stripped:
        raise ValueError("question must not be empty")

    fragments = re.split(r"\s+(?:and|then|also)\s+|[;]", stripped, flags=re.IGNORECASE)
    intents = [fragment.strip() for fragment in fragments if fragment.strip()]
    return intents[:3] or [stripped]


def build_synonym_slots(question: str, rare_terms: Sequence[dict[str, object]]) -> list[dict[str, object]]:
    """Create synonym slots when the question or rare terms trigger them."""

    visible_terms = set(tokenize(question))
    visible_terms.update(str(item["term"]) for item in rare_terms)

    slots = []
    for slot in SYNONYM_SLOTS:
        if visible_terms.intersection(slot["triggers"]):
            slots.append({"slot": slot["slot"], "terms": list(slot["terms"])})
    return slots


def extract_explicit_exclusions(question: str) -> list[str]:
    """Extract simple user-stated exclusions from negation phrases."""

    exclusions: list[str] = []
    pattern = re.compile(
        r"\b(?:avoid|exclude|excluding|except|not|without)\s+([a-z0-9][a-z0-9 -]{0,60})",
        flags=re.IGNORECASE,
    )
    for match in pattern.finditer(question):
        for token in tokenize(match.group(1)):
            if token not in exclusions:
                exclusions.append(token)
    return exclusions[:4]


def suggest_exclusions(question: str) -> list[str]:
    """Suggest conservative exclusions to reduce common false positives."""

    question_terms = set(tokenize(question))
    exclusions = extract_explicit_exclusions(question)

    if "bm25" in question_terms:
        exclusions.append("embedding-only")
    if "rag" in question_terms and "bm25" in question_terms:
        exclusions.append("answer-generation-only")

    deduped: list[str] = []
    for term in exclusions:
        if term not in deduped:
            deduped.append(term)
    return deduped[:5]


def quote_bm25_term(term: str) -> str:
    """Format a term or phrase for a generic BM25 query string."""

    if re.search(r"\s", term):
        return f'"{term}"'
    return term


def make_bm25_query(
    required_terms: Sequence[str],
    optional_terms: Sequence[str],
    synonym_slots: Sequence[dict[str, object]],
    exclusion_terms: Sequence[str],
) -> str:
    """Build a generic BM25 query string with required, optional, and excluded terms."""

    parts: list[str] = [f"+{quote_bm25_term(term)}" for term in required_terms]

    for slot in synonym_slots[:3]:
        terms = [quote_bm25_term(str(term)) for term in slot["terms"]]
        parts.append("(" + " OR ".join(terms) + ")")

    for term in optional_terms:
        parts.append(quote_bm25_term(term))

    for term in exclusion_terms:
        parts.append(f"-{quote_bm25_term(term)}")

    return " ".join(parts)


def choose_required_terms(
    intent: str, rare_terms: Sequence[dict[str, object]], stats: VocabularyStats
) -> list[str]:
    """Choose required terms that are both question-relevant and present in the corpus."""

    candidate_order = [str(item["term"]) for item in rare_terms]
    intent_terms = tokenize(intent)
    required = [
        term for term in intent_terms if term in stats.document_frequency and term in candidate_order
    ]

    for term in candidate_order:
        if len(required) >= 4:
            break
        if term not in required:
            required.append(term)

    return required[:4]


def build_subqueries(
    question: str,
    rare_terms: Sequence[dict[str, object]],
    synonym_slots: Sequence[dict[str, object]],
    stats: VocabularyStats,
) -> list[dict[str, object]]:
    """Build subqueries with BM25-ready strings and evidence requirements."""

    exclusions = suggest_exclusions(question)
    rare_term_order = [str(item["term"]) for item in rare_terms]
    subqueries = []

    for index, intent in enumerate(decompose_question(question), start=1):
        required_terms = choose_required_terms(intent, rare_terms, stats)
        optional_terms = [term for term in rare_term_order if term not in required_terms][:5]
        bm25_query = make_bm25_query(required_terms, optional_terms, synonym_slots, exclusions)
        evidence_terms = ", ".join(required_terms[:3]) if required_terms else "the query intent"
        subqueries.append(
            {
                "id": f"q{index}",
                "intent": intent,
                "bm25_query": bm25_query,
                "required_terms": required_terms,
                "optional_terms": optional_terms,
                "exclusion_terms": exclusions,
                "evidence_requirements": [
                    f"Passage must explicitly support: {intent}",
                    f"Passage should mention at least one required term: {evidence_terms}",
                    "Passage should describe retrieval planning behavior, not only final answer synthesis.",
                ],
            }
        )

    return subqueries


def build_retrieval_plan(
    question: str,
    documents: Sequence[Document],
    max_terms: int = 8,
    top_k: int = 5,
) -> dict[str, object]:
    """Return a deterministic QueryLoom retrieval plan."""

    if max_terms < 1:
        raise ValueError("max_terms must be at least 1")
    if top_k < 1:
        raise ValueError("top_k must be at least 1")

    normalized_question = question.strip()
    if not normalized_question:
        raise ValueError("question must not be empty")

    stats = compute_vocabulary_stats(documents)
    rare_terms = select_rare_terms(normalized_question, stats, max_terms=max_terms)
    synonym_slots = build_synonym_slots(normalized_question, rare_terms)

    return {
        "schema_version": "1.0",
        "planner": {
            "name": "queryloom-local-heuristic",
            "mode": "local",
            "external_llm_used": False,
        },
        "question": normalized_question,
        "corpus": {
            "document_count": len(documents),
            "token_count": stats.token_count,
            "vocabulary_size": stats.vocabulary_size,
            "top_k": top_k,
        },
        "rare_term_candidates": rare_terms,
        "synonym_slots": synonym_slots,
        "subqueries": build_subqueries(normalized_question, rare_terms, synonym_slots, stats),
    }


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    """Parse command-line arguments."""

    parser = argparse.ArgumentParser(
        description="Build a deterministic QueryLoom BM25 retrieval plan for a local corpus."
    )
    parser.add_argument("--question", help="Question to plan retrieval for.")
    parser.add_argument("--question-file", help="Path to a UTF-8 file containing the question.")
    parser.add_argument("--corpus", help="Path to a Markdown/text file or directory.")
    parser.add_argument("--output", help="Write JSON plan to this file instead of stdout.")
    parser.add_argument("--max-terms", type=int, default=8, help="Maximum rare-term candidates.")
    parser.add_argument("--top-k", type=int, default=5, help="Intended retrieval depth recorded in output.")
    parser.add_argument("--selftest", action="store_true", help="Run with built-in sample data.")
    return parser.parse_args(argv)


def read_question_from_args(args: argparse.Namespace) -> str:
    """Read a question from inline text or a file."""

    if args.question and args.question_file:
        raise ValueError("use either --question or --question-file, not both")
    if args.question:
        return args.question
    if args.question_file:
        question_path = Path(args.question_file)
        if not question_path.exists():
            raise ValueError(f"question file does not exist: {args.question_file}")
        question = question_path.read_text(encoding="utf-8").strip()
        if not question:
            raise ValueError(f"question file is empty: {args.question_file}")
        return question
    raise ValueError("provide --question, --question-file, or --selftest")


def emit_plan(plan: dict[str, object], output: str | None = None) -> None:
    """Write the plan as stable, pretty JSON to stdout or a file."""

    text = json.dumps(plan, indent=2, ensure_ascii=True) + "\n"
    if output:
        output_path = Path(output)
        if output_path.parent != Path("."):
            output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(text, encoding="utf-8")
    else:
        sys.stdout.write(text)


def run_selftest(output: str | None = None) -> int:
    """Run the planner on built-in sample data and emit the resulting plan."""

    plan = build_retrieval_plan(SAMPLE_QUESTION, SAMPLE_DOCUMENTS)
    emit_plan(plan, output)
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    """CLI entry point."""

    args_list = list(sys.argv[1:] if argv is None else argv)
    if not args_list:
        return run_selftest()

    args = parse_args(args_list)
    read_optional_api_key()

    try:
        if args.selftest:
            return run_selftest(args.output)

        question = read_question_from_args(args)
        if not args.corpus:
            raise ValueError("provide --corpus unless using --selftest")
        documents = load_corpus(args.corpus)
        plan = build_retrieval_plan(
            question,
            documents,
            max_terms=args.max_terms,
            top_k=args.top_k,
        )
        emit_plan(plan, args.output)
        return 0
    except (OSError, ValueError) as exc:
        sys.stderr.write(f"error: {exc}\n")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
