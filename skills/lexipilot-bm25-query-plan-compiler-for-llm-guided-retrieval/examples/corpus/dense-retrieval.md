# Dense Retrieval Caveats
aliases:
  - embedding retrieval

Dense vectors help with semantic matching, but they may smooth away sparse
signals like CVE-2024-3094, function names, or the original title of a paper.
HyDE can improve recall, but it should be compared with BM25 baselines.
