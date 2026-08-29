# Contributing to Create Agents AI

Thank you for your interest in contributing to **Create Agents AI**!

This document provides a quick entrypoint for contributors. For the complete, in-depth guide covering architecture, provider adapters, CLI handlers, and quality gate policies, please read our [Detailed Contribution Guide](docs/en/dev-guide/contribute.md).

## Prerequisites

- **Python**: `>=3.12,<4.0`
- **Package and environment manager**: [uv](https://docs.astral.sh/uv/)
- **Git**

## Workflow

1. **Fork** the repository on GitHub.
2. **Clone** your fork locally:
   ```bash
   git clone https://github.com/your-username/Create-Agents-AI.git
   cd Create-Agents-AI
   ```
3. **Create a branch** off `develop`:
   ```bash
   git checkout -b feature/your-feature-name
   ```
   *(All pull requests must target the `develop` branch).*
4. **Install dependencies and hooks** from the locked environment:
   ```bash
   uv sync --locked
   uv run --locked --no-sync pre-commit install --install-hooks
   ```
   *(To include optional file-reading dependencies during development, use `uv sync --locked --extra file-tools`).*
5. **Implement changes** adhering to Clean Architecture and SOLID principles.
6. **Add or update tests** to verify your changes and prevent regressions.
7. **Run local validation**:
   ```bash
   # Run all pre-commit quality hooks (38 hooks)
   uv run --locked --no-sync pre-commit run --all-files

   # Run pre-push quality hooks (4 hooks: two mypy scopes, pytest-unit, pip-audit)
   uv run --locked --no-sync pre-commit run --all-files --hook-stage pre-push

   # Run safe local tests (excludes integration and slow tests)
   uv run --locked --no-sync pytest -m 'not integration and not slow' -ra --cov

   # Strict documentation build
   uv run --locked --no-sync mkdocs build --strict
   ```
8. **Commit your changes** using Conventional Commits in English:
   ```bash
   git commit -m "feat: add support for provider XYZ"
   ```
   The repository enforces Conventional Commits via a `commit-msg` hook.
9. **Open a Pull Request** against `develop`.

## Quality Gates and Hook Breakdown

The repository enforces **44 hooks** via `.pre-commit-config.yaml`:

- **38 pre-commit hooks**: Code formatting (Ruff, mdformat), linting (Ruff, yamllint, actionlint, codespell), syntax/file integrity, secret scanning (Gitleaks), static security (Bandit), import direction (`import-linter`), cycle detection, and docstrings (Ruff D rules).
- **4 pre-push hooks**: Primary and supporting static type checks (`mypy`), the safe unit test suite with the 85% `pytest.ini` coverage floor (`pytest-unit`), and dependency audit (`pip-audit`).
- **1 commit-msg hook**: Conventional Commits format validation.
- **1 manual hook**: Optional `check-harness-sync` for the central harness mirror.

> **Provider Integration Tests**: Tests connecting to live external APIs are marked with `@pytest.mark.integration` and must not be run during default local validation without explicit authorization. Safe local checks do not call OpenAI or Ollama and do not consume provider quota. Network-dependent checks such as `pip-audit` may still require network access.

`.agents/` is tracked so portable validators travel with the repository. The
generated `.codex/`, `.claude/`, `.opencode/`, and `.github/prompts/` mirrors
are ignored and remain outside the Git index. Normal hooks do not require
`central-skills`; run the optional mirror check only when deliberately
requested:

```bash
uv run --locked --no-sync harness-sync --check
```

If `central-skills` is unavailable, the manual check is `skipped`, not a
failure of the normal hook stages. Gitleaks intentionally scans every tracked
file, including `.agents/`, and redacts findings. Review output from mutating
hooks before staging, then stage only explicit paths. In a dirty working tree,
avoid `git add .` and `git add -A`; they can include unrelated files.

## Code of Conduct & Security

- Please review and adhere to our [Code of Conduct](CODE_OF_CONDUCT.md).
- To report security vulnerabilities, please follow our [Security Policy](SECURITY.md).
