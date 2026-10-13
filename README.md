# Tea CLI

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.9+-blue.svg)](https://python.org)
[![Version](https://img.shields.io/badge/version-0.1.1-blue.svg)](pyproject.toml)

Control the [Tea](https://goodtea.world) multi-livestream intelligence platform from your terminal.
A thin client (Click + httpx + Rich) for the hosted Tea API.

## Install

```bash
curl -fsSL https://downloads.goodtea.world/cli/install.sh | bash
```

The installer downloads the standalone binary for your platform and verifies it against the
release `SHA256SUMS`. From source (a clone of this repo):

```bash
make install          # creates .venv and installs `tea` in editable mode
source .venv/bin/activate
tea --help
```

## Authenticate

Create an API key in the product app (**Account › Developer › New key**), then:

```bash
tea login --key tea_xxxxxxxx           # or run `tea login` for the wizard
```

The key is stored in `~/.tea/config.yaml` and sent as the `X-API-Key` header on every
request.

### Configuration

| Setting   | Config key (`~/.tea/config.yaml`) | Env var         | Default                 |
|-----------|-----------------------------------|-----------------|-------------------------|
| API key   | `api_key`                         | `TEA_API_KEY`   | —                       |
| API URL   | `api_url`                         | `TEA_API_URL`   | `https://api.goodtea.world` |
| Timeout   | `timeout`                         | `TEA_TIMEOUT`   | `60` (seconds)          |
| Retries   | —                                 | `TEA_MAX_RETRIES` | `3`                   |

Environment variables take precedence over the config file.

## Commands

```bash
tea status                       # account + platform snapshot
tea doctor                       # diagnose config, connectivity, auth

tea bookmarks list [--platform twitch] [--limit 50]
tea bookmarks search "keyword"
tea bookmarks add <url> [--title ...] [--platform ...]
tea bookmarks delete <id>

tea livestreams list [--platform youtube]
tea livestreams live
tea livestreams trending

tea keys list
tea keys create <name> [--scope read:bookmarks] [--expires-in-days 90]
tea keys delete <id>

tea completion zsh               # shell completion setup
```

Global flags: `-o/--output {table,json,yaml}`, `--no-color`, `-v/--verbose`, `--debug`, `--ci`.

```bash
tea -o json bookmarks list | jq '.[].url'
```

## Exit codes

`0` ok · `1` general · `2` auth · `3` not found · `4` validation · `5` network · `6` server ·
`130` SIGINT · `143` SIGTERM.

## Develop

```bash
make test     # pytest
make lint     # byte-compile check
make smoke    # `tea --help`
```

## Documentation & resources

- [CHANGELOG](CHANGELOG.md) — release history
- Hosted product: [goodtea.world](https://goodtea.world) · binaries: `https://downloads.goodtea.world`

## License

This project is licensed under the MIT License.
