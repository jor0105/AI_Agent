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
   # Run all pre-commit quality hooks (36 hooks)
   uv run --locked --no-sync pre-commit run --all-files

   # Run pre-push quality hooks (3 hooks: mypy, pytest-unit, pip-audit)
   uv run --locked --no-sync pre-commit run --all-files --hook-stage pre-push

   # Run safe local tests (excludes integration and slow tests)
   uv run --locked --no-sync pytest -m 'not integration and not slow' -ra --cov=src --cov-fail-under=85

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

The repository enforces **40 automated hooks** via `.pre-commit-config.yaml`:

- **36 pre-commit hooks**: Code formatting (Ruff, mdformat), linting (Ruff, yamllint, actionlint, codespell), syntax/file integrity, secret scanning (gitleaks), static security (Bandit), import direction (`import-linter`), cycle detection, and docstrings (`pydocstyle`).
- **3 pre-push hooks**: Full static type checking (`mypy`), safe unit test suite with 85% coverage floor (`pytest-unit`), and dependency audit (`pip-audit`).
- **1 commit-msg hook**: Conventional Commits format validation.

> **Provider Integration Tests**: Tests connecting to live external APIs are marked with `@pytest.mark.integration` and must not be run during default local validation without explicit authorization. Safe local checks do not call OpenAI or Ollama and do not consume provider quota. Network-dependent checks such as `pip-audit` may still require network access.

## Code of Conduct & Security

- Please review and adhere to our [Code of Conduct](CODE_OF_CONDUCT.md).
- To report security vulnerabilities, please follow our [Security Policy](SECURITY.md).
