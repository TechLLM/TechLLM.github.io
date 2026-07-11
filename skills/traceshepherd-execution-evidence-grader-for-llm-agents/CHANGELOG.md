# Changelog

All notable changes to this skill are documented here (Keep a Changelog style, auto-generated).

## [0.1.0] - 2026-07-11
### Added
- Initial release.
- Grades agent executions using trace JSONL, filesystem state, and explicit evidence rules
- Validates expected output files with size, hash, existence, and content-pattern checks
- Detects missing evidence such as required searches, reads, edits, writes, or tool calls
- Reports unexpected, forbidden, or incorrectly modified files
