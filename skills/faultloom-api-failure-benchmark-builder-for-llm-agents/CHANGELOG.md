# Changelog

All notable changes to this skill are documented here (Keep a Changelog style, auto-generated).

## [0.1.0] - 2026-07-08
### Added
- Initial release.
- Ingests raw text logs, JSON API responses, exception traces, and status payloads from social publishing pipelines
- Normalizes provider-specific failures into a portable taxonomy such as authentication, rate limit, permission, media validation, transient outage, policy block, and unknown failure
- Assigns retryability, expected recovery action, user-action requirement, severity, and confidence metadata to every classified case
- Generates benchmark-ready YAML test cases for evaluating LLM tool-use failure handling
