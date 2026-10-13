.PHONY: venv install test lint smoke build build-binary clean

VENV ?= .venv
PY := $(VENV)/bin/python
PIP := $(VENV)/bin/pip

# Standalone binary naming must match install.sh's `tea-${os}-${arch}` asset.
BIN_OS := $(shell uname -s | tr '[:upper:]' '[:lower:]')
BIN_ARCH := $(shell uname -m | sed 's/amd64/x86_64/; s/aarch64/arm64/')
BIN := tea-$(BIN_OS)-$(BIN_ARCH)
# macOS only: stable per-build onefile unpack dir (mirrors sega _onefile_cache_args).
# The default {TEMP}/onefile_{PID}_{TIME} re-extracts on every run and XProtect rescans
# every new file, so each command took 4-12 s on macOS (LAUNCH-CLI-SWEEP). Linux keeps
# the default (already fast; /tmp is shared between users).
TEA_VERSION := $(shell sed -n 's/^version *= *"\(.*\)"/\1/p' pyproject.toml | head -1)
ifeq ($(BIN_OS),darwin)
ONEFILE_SPEC := --onefile-tempdir-spec='{TEMP}/huntingtonapplied/tea-$(TEA_VERSION)-$(shell date -u +%Y%m%d%H%M%S)'
endif

venv:
	python3 -m venv $(VENV)
	$(PIP) install -U pip

install: venv
	$(PIP) install -e ".[test]"

test:
	$(VENV)/bin/pytest -q

lint:
	$(PY) -m py_compile tea_cli/*.py tea_cli/commands/*.py

smoke:
	$(VENV)/bin/tea --help >/dev/null && echo "smoke ok"

build:
	$(PY) -m build

# Single-file binary for the downloads CDN. install.sh fetches
# /cli/releases/<version>/tea-<os>-<arch> and verifies it against SHA256SUMS.
#
# Built with Nuitka onefile (compiled to native machine code), NOT PyInstaller.
# PyInstaller bundles raw .pyc bytecode that pyinstxtractor can unpack and
# uncompyle back into readable source (R-tea-23). Nuitka compiles each module to
# C -> a native binary with no .pyc archive, mirroring the rest of the fleet CLIs
# (see sega `binaries publish-cli` / lab/client_testing/CLI_REBUILD_PLAYBOOK.md).
# --disable-plugin=anti-bloat is required: anti-bloat rewrites the
# certifi->importlib.resources chain into a bare `raise ImportError()` that
# crashes the first network call (fleet class C8-1).
# NOTE: Nuitka --standalone needs a real CPython (python.org or Homebrew), NOT
# Apple's /usr/bin/python3 (Nuitka FATALs: "Apple Python is not supported").
# --static-libpython=no lets it build against a stock dylib python.
build-binary: install
	$(PIP) install -U setuptools "Nuitka[onefile]==2.5.9"
	$(PY) -m nuitka --standalone --onefile --follow-imports --assume-yes-for-downloads \
		--disable-plugin=anti-bloat --include-package=rich._unicode_data \
		--static-libpython=no \
		$(ONEFILE_SPEC) \
		--output-dir=dist --output-filename=$(BIN) tea_cli/main.py
	cd dist && { sha256sum $(BIN) 2>/dev/null || shasum -a 256 $(BIN); } > SHA256SUMS
	@./dist/$(BIN) --help >/dev/null && echo "Built + smoke-tested: dist/$(BIN) (+ dist/SHA256SUMS)"

clean:
	rm -rf build dist *.egg-info $(VENV) .pytest_cache
	find . -name __pycache__ -type d -exec rm -rf {} +
