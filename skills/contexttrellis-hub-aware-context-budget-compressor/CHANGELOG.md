# Changelog

All notable changes to this skill are documented here (Keep a Changelog style, auto-generated).

## [0.1.0] - 2026-07-08
### Added
- Initial release.
- Graph-aware context budgeting that detects over-central hub notes and prevents them from consuming the full prompt window
- Long-tail preservation mode for execution-critical notes such as API call recipes, polling behavior, dry-run logs, incident notes, and operational checklists
- Hub compression pipeline that summarizes high-centrality notes into short orientation blocks instead of dropping them entirely
- Token-budget planner with deterministic packing, configurable reserve tokens, and transparent inclusion decisions
