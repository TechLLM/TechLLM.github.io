# Changelog

All notable changes to this skill are documented here (Keep a Changelog style, auto-generated).

## [0.1.0] - 2026-08-03
### Added
- Initial release.
- Hybrid fatal-boundary detector that fuses LLM judgment, regex tool-error vocabularies, and structural heuristics
- Schema-stable output: fatal_step_index, pre_failure_subgraph, masked_tail, confidence, suggested_label
- Pluggable judge backends — OpenAI, Anthropic, local Ollama, or fully offline regex-only mode
- Token-level masking hints compatible with GRPO, PPO, and rejection-sampling fine-tuning loops
