# Conceptual Gate Catalog and Tool Mapping

> Summary: Mapping of conceptual quality gate slots ([HYGIENE], [SYNTAX], [FORMATTER], [LINTER], [TYPE_CHECK], [CIRCULAR_DEPENDENCIES], [SECRETS], [DIFF_SANITY], [TESTS]) to concrete commands per tech stack.

## 1. Quality Gate Slot Matrix

| Slot                          | Purpose                                                                                                  | Python                         | JS / TS                                   | Go / Rust                                                         |
| :---------------------------- | :------------------------------------------------------------------------------------------------------- | :----------------------------- | :---------------------------------------- | :---------------------------------------------------------------- |
| **`[HYGIENE]`**               | Whitespace, EOF, merge markers, large files                                                              | `pre-commit-hooks`             | `pre-commit-hooks` / `lint-staged`        | `git diff --check`                                                |
| **`[SYNTAX]`**                | Fast parse/compilation check                                                                             | `python -m py_compile`         | `tsc --noEmit`                            | `go vet` / `cargo check`                                          |
| **`[FORMATTER]`**             | Deterministic code formatting (auto-fix)                                                                 | `ruff format`                  | `prettier --write` / `biome format`       | `gofmt -w` / `cargo fmt`                                          |
| **`[LINTER]`**                | Code quality, unused vars, clean imports                                                                 | `ruff check --fix`             | `eslint --fix` / `biome lint`             | `golangci-lint` / `cargo clippy`                                  |
| **`[TYPE_CHECK]`**            | Static typing validation                                                                                 | `mypy` / `pyright`             | `tsc --noEmit`                            | Built-in                                                          |
| **`[CIRCULAR_DEPENDENCIES]`** | **Required** detection of direct/indirect import cycles; fail new cycles and ratchet historical baseline | `import-linter` / `pycycle`    | `madge --circular` / `dependency-cruiser` | Go compiler / `cargo metadata` plus configured architecture check |
| **`[SECRETS]`**               | Prevent committing credentials/keys                                                                      | `gitleaks protect`             | `gitleaks protect`                        | `gitleaks protect`                                                |
| **`[DIFF_SANITY]`**           | Detect debuggers, stubs, unverified bypasses                                                             | `check_diff_sanity.py`         | `check_diff_sanity.py`                    | `check_diff_sanity.py`                                            |
| **`[LOCKFILE]`**              | Parity between manifest and lockfile                                                                     | `check_lockfile_sync.py`       | `check_lockfile_sync.py`                  | `check_lockfile_sync.py`                                          |
| **`[TEST_INTEGRITY]`**        | Prevent test deletions, `.only`, and skips                                                               | `check_test_integrity.py`      | `check_test_integrity.py`                 | `check_test_integrity.py`                                         |
| **`[TESTS_FAST]`**            | Run unit tests impacted by changed files                                                                 | `pytest -m "not slow" <files>` | `vitest related <files>` / `jest -o`      | `go test -short <pkg>`                                            |

## 2. Configuration & Structured Data Validations

- **YAML**: `check-yaml` or `yamllint`
- **JSON**: `check-json` or `jq . <file>`
- **TOML**: `check-toml` or `taplo check`
- **Docker**: `hadolint`
- **Shell**: `shellcheck`, `bash -n`

## 3. Tool Selection Rules

1. **Prefer project-native tools**: If the repository configures a tool via `pyproject.toml` or `package.json`, execute it via the project's package manager (`uv run`, `pnpm exec`).
2. **Circular dependency requirement**: Every repository with importable code must configure `[CIRCULAR_DEPENDENCIES]` in pre-commit. Reuse an existing compiler, graph checker, or architecture command; do not silently omit the slot because no dedicated package is installed. If no deterministic local command can inspect the graph, return `ERROR` and leave setup incomplete.
3. **Measure, do not impose a universal speed budget**: Choose each hook's scope
   and stage from the repository's actual cost and workflow. Keep a check in
   pre-commit when its safety value justifies the observed latency; move it to
   pre-push or CI when it harms the workflow or encourages `--no-verify`.
