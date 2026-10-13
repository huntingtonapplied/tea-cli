# Changelog

All notable changes to the Tea CLI will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

> **Pre-1.0 policy:** Minor versions (0.x) may include breaking changes.

## [0.1.1] - 2026-10-13

### Changed
- README rewritten for the public repository (curl installer, hosted API, no monorepo paths).
- License holder: Huntington Applied LLC.

## [0.1.0] - Unreleased

### Added
- Initial release with `login`, `status`, `livestreams`, `bookmarks`, `keys`, `doctor`, and `completion` commands
- `--output/-o` flag for `table`, `json`, or `yaml` output formats
- `--verbose/-v` flag for INFO-level logging to stderr
- `--debug` flag for DEBUG-level logging (HTTP requests)
- `--no-color` flag to disable colored output
- `--ci` flag for CI/CD pipeline usage (no color, no interactive prompts); auto-detected from `CI`, `GITHUB_ACTIONS`, `GITLAB_CI` env vars
- `tea doctor` command — checks configuration, connectivity, and authentication
- `tea keys` — list, create, and revoke developer API keys
- Developer API-key auth via the `X-API-Key` header
- Distinct exit codes: 2 (auth), 3 (not found), 4 (validation), 5 (network), 6 (server), 7 (duplicate), 130 (SIGINT), 143 (SIGTERM)
- Automatic retry with exponential backoff on 429/500/502/503/504 and connection/timeout errors (`TEA_MAX_RETRIES`, default 3)
- Configurable request timeout via `TEA_TIMEOUT` env var or `timeout` config key (default 60s)
- Rich terminal output with table, JSON, and YAML formats
- Shell completion for bash, zsh, and fish

### Notes
- Configuration via `~/.tea/config.yaml` or `TEA_API_KEY` / `TEA_API_URL` env vars
- Default API URL is `https://api.goodtea.world` (override with `TEA_API_URL=http://localhost:8007` for local dev)
