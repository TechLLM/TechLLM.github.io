# Lexical Retrieval Notes
aliases:
  - BM25 planning
  - sparse retrieval

BM25 is useful when exact wording, RFC 9110 references, wiki links like
[[SPLADE]], and identifiers such as arXiv:2305.10403 need to survive search.

## Query planning

An LLM can propose rare terms, exclusions, and title candidates before lexical
search. This is planner mode, not answer mode.
