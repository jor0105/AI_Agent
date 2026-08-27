# How to Contribute

Contribute to the development of **Create Agents AI** by following the guidelines below. All contributions are welcome!

______________________________________________________________________

## 🚦 Requirements for Contribution

- Python `>=3.12,<4.0` and `uv` installed
- Basic understanding of Clean Architecture and SOLID principles
- Familiarity with Git and GitHub workflows
- Adherence to project code standards, typing, and test coverage

______________________________________________________________________

## 🛠️ Step-by-Step Contribution

01. **Fork** the repository on GitHub

02. **Clone** your fork locally:

    ```bash
    git clone https://github.com/jordanestralioto/Create-Agents-AI.git
    cd Create-Agents-AI
    ```

03. **Create a descriptive branch**:

    ```bash
    git checkout -b feature/add-provider
    ```

04. **Implement** your improvement or fix following existing project architecture

05. **Add or update automated tests** proving behavior, edge cases, and regressions

06. **Install and run local checks**:

    ```bash
    uv sync --locked
    uv run --locked --no-sync pre-commit install --install-hooks
    uv run --locked --no-sync pre-commit run --all-files
    uv run --locked --no-sync pre-commit run --all-files --hook-stage pre-push
    uv run --locked --no-sync pytest -m 'not integration and not slow' -ra \
        --cov=src --cov-fail-under=85
    uv run --locked --no-sync mkdocs build --strict
    ```

07. **Update documentation** if APIs, configuration, or parameters changed

08. **Commit in English** using Conventional Commits format (`feat:`, `fix:`, `docs:`)

09. **Submit a Pull Request (PR)** against the `develop` branch with a clear description

10. Await review and address feedback from maintainers

______________________________________________________________________

## 🧪 Tests and Quality Gates

The safe local test command selects unit tests and components that do not rely on live external services:

```bash
uv run --locked --no-sync pytest -m 'not integration and not slow' -ra \
    --cov=src --cov-fail-under=85
```

Tests hitting external APIs must be marked with `@pytest.mark.integration` and are excluded from default local runs to avoid consuming provider quotas. Tests marked as `slow` are also excluded from safe local runs.

Run targeted gates when applicable:

```bash
uv run --locked --no-sync mypy src --ignore-missing-imports --pretty
uv run --locked --no-sync pydocstyle src --convention=google --add-ignore=D100,D104,D107
uv run --locked --no-sync bandit -c pyproject.toml -r src -ll
uv run --locked --no-sync pip-audit
```

The full CI workflow, including lockfile checks, security, quality, typing, docstrings, and test coverage, is defined in `.github/workflows/pipeline.yml`. The local pre-commit configuration defines 41 hooks across `pre-commit` (37), `pre-push` (3), and `commit-msg` (1).

### Local Quality Gate Policy

Pre-commit hooks are deterministic and inspect the Git index to determine whether a commit can proceed. They do not run `uv sync`, `uv lock`, dependency resolvers, or auto-updaters. Environment synchronization is an explicit bootstrap step (`uv sync --locked`); dependency changes are deliberate, reviewed, and update the lockfile outside hooks:

```bash
# Only when intentionally changing dependency resolution
uv lock
uv sync --locked
```

The `quality-gate-policy` runs only when hook configuration or policy code changes. It enforces immutable pins for remote hooks, forbids dependency sync within hooks, and preserves essential gates. Tool configurations for Ruff, pytest, and Bandit remain canonical in their respective configuration files without duplication. Modifications to `.gitleaksignore` require security review. Generated harness projections do not receive auto-formatting; the projection gate validates the staged hash.

Line length checks can be run as an on-demand structural audit for large refactors:

```bash
uv run --locked --no-sync python .agents/scripts/check-max-lines.py
```

Pre-push runs `mypy` across `src/`, safe tests with coverage, and `pip-audit`. Any external dependency audit failure (such as network unavailability) must be reported as `external_failure`, never summarized as a pass.

______________________________________________________________________

## ✅ PR Quality Checklist

- [ ] Code strictly follows Clean Architecture and SOLID principles
- [ ] Automated tests cover new features and bug fixes
- [ ] Documentation updated (code docstrings and Markdown docs)
- [ ] No lint warnings (Ruff, yamllint, mdformat)
- [ ] Targeted gates (mypy, pydocstyle, Bandit, pip-audit) executed when applicable
- [ ] Strict docs build (`uv run --locked --no-sync mkdocs build --strict`) passes
- [ ] Atomic, clear Conventional Commits in English
- [ ] Pull request description clearly explains rationale

______________________________________________________________________

## 📝 Commit Conventions

Use Conventional Commits in English:

- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation only changes
- `test:` Adding or improving tests
- `refactor:` Code changes without altering behavior
- `chore:` Maintenance tasks

Example:

```bash
git commit -m "feat: add support for provider XYZ"
```

______________________________________________________________________

## 🤖 Adding a Provider

1. Create adapter in `src/createagents/infra/adapters/<ProviderName>/`.
2. Implement application port `ChatRepository`.
3. Register provider in `src/createagents/infra/factories/chat_adapter_factory.py`.
4. Add unit tests in `tests/infra/adapters/`, mirroring the touched layer.

Provider selection logic must never live in application use cases; dependency wiring is managed by the composition root via the factory.

## ⌨️ Adding a CLI Command

1. Create handler in `src/createagents/presentation/cli/commands/`.
2. Register in `ChatCLIApplication._setup_commands` in `src/createagents/presentation/cli/application/chat_cli_app.py`.
3. Keep specific handlers before `ChatCommandHandler` (the fallback handler).

Consult the [CLI Architecture Guide](cli-architecture.md) for details.

______________________________________________________________________

## 📚 Contribution Examples

- Add a new custom tool (`BaseTool`)
- Fix a bug or improve error handling in a provider adapter
- Enhance unit test coverage
- Update and clarify documentation examples
- Suggest performance, security, or typing enhancements

______________________________________________________________________

## 🐞 Reporting Bugs and Suggesting Improvements

1. [Open an issue](https://github.com/jordanestralioto/Create-Agents-AI/issues)
2. Describe the issue or suggestion with full details, reproduction steps, and context
3. Include error logs, screenshots, or code snippets where helpful

______________________________________________________________________

## 📖 Documentation Guidelines

- Always document new functions, classes, and parameters with Google-style docstrings
- Update relevant Markdown files in `docs/` and `docs/en/` (e.g. examples, API reference, FAQ)
- Use clear, technical, and accessible language
- Include minimal reproducible code examples

______________________________________________________________________

## 🤝 Contact and Support

- Email: estraliotojordan@gmail.com
- GitHub: [@jordanestralioto](https://github.com/jordanestralioto)
- Discussions: [GitHub Discussions](https://github.com/jordanestralioto/Create-Agents-AI/discussions)

______________________________________________________________________

**Thank you for contributing to Create Agents AI! Your support makes the project better for the entire community.**
