# Changelog

All notable changes to this skill are documented here (Keep a Changelog style, auto-generated).

## [0.1.0] - 2026-07-09
### Added
- Initial release.
- Domain-sliced Recall, Precision, F1, and pass-rate metrics for retrieval and relevance gates
- False-pass and false-block analysis for gate decisions before context reaches the generator
- Missing-evidence reports that identify queries where required supporting documents were not retrieved
- OOD-like query detection using configurable tags such as rare terms, unfamiliar domains, and long-tail intents
