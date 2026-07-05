# QueryLoom sample corpus

QueryLoom creates retrieval_plan.json files before retrieval. The plan decomposes user questions, names evidence requirements, and turns RAG intent into BM25 query strings.

BM25 retrieval rewards rare exact terms in a corpus. TF-IDF can surface identifiers, product names, and unusual phrases that ordinary semantic search might skip.

Retrieval failures often happen when a search system omits required evidence, overuses broad synonyms, or includes unrelated vector-only concepts.
