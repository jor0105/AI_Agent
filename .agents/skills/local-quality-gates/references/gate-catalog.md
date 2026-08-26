# Conceptual Gate Catalog and Tool Mapping

> Summary: Mapping of conceptual quality gate slots ([HYGIENE], [SYNTAX], [FORMATTER], [LINTER], [TYPE_CHECK], [CIRCULAR_DEPENDENCIES], [SECRETS], [DIFF_SANITY], [LOCKFILE], [TESTS]) to concrete commands per tech stack.

## 1. Quality Gate Slot Matrix

| Slot                          | Purpose                                                                                                  | Python                                                               | JS / TS                                                                       | Go / Rust                                                                                              |
| :---------------------------- | :------------------------------------------------------------------------------------------------------- | :------------------------------------------------------------------- | :---------------------------------------------------------------------------- | :----------------------------------------------------------------------------------------------------- |
| **`[HYGIENE]`**               | Whitespace, EOF, merge markers, large files                                                              | `pre-commit-hooks`                                                   | `pre-commit-hooks` / `lint-staged`                                            | `git diff --check`                                                                                     |
| **`[SYNTAX]`**                | Fast parse/compilation check                                                                             | `python -m py_compile`                                               | `tsc --noEmit`                                                                | `go vet` / `cargo check`                                                                               |
| **`[FORMATTER]`**             | Deterministic code formatting (auto-fix)                                                                 | `ruff format`                                                        | `prettier --write` / `biome format`                                           | `gofmt -w` / `cargo fmt`                                                                               |
| **`[LINTER]`**                | Code quality, unused vars, clean imports                                                                 | `ruff check --fix`                                                   | `eslint --fix` / `biome lint`                                                 | `golangci-lint` / `cargo clippy`                                                                       |
| **`[TYPE_CHECK]`**            | Static typing validation                                                                                 | `mypy` / `pyright`                                                   | `tsc --noEmit`                                                                | Built-in                                                                                               |
| **`[CIRCULAR_DEPENDENCIES]`** | **Required** detection of direct/indirect import cycles; fail new cycles and ratchet historical baseline | `import-linter` / `pycycle`                                          | `madge --circular` / `dependency-cruiser`                                     | Go compiler / `cargo metadata` plus configured architecture check                                      |
| **`[SECRETS]`**               | Prevent committing credentials/keys                                                                      | `gitleaks protect`                                                   | `gitleaks protect`                                                            | `gitleaks protect`                                                                                     |
| **`[DIFF_SANITY]`**           | Detect debuggers, stubs, unverified bypasses                                                             | `check_diff_sanity.py`                                               | `check_diff_sanity.py`                                                        | `check_diff_sanity.py`                                                                                 |
| **`[LOCKFILE]`**              | Deterministic manifest/lockfile validation; never automatic dependency updates                           | `uv lock --check` / `poetry check --lock` / `check_lockfile_sync.py` | `check_lockfile_sync.py` plus a project-native immutable check when available | `cargo check --locked` / `check_lockfile_sync.py`; Go may configure `go mod tidy -diff` when supported |
| **`[TEST_INTEGRITY]`**        | Prevent test deletions, `.only`, and skips                                                               | `check_test_integrity.py`                                            | `check_test_integrity.py`                                                     | `check_test_integrity.py`                                                                              |
| **`[TESTS_FAST]`**            | Run unit tests impacted by changed files                                                                 | `pytest -m "not slow" <files>`                                       | `vitest related <files>` / `jest -o`                                          | `go test -short <pkg>`                                                                                 |

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
4. **Separate dependency lifecycle operations**: `[LOCKFILE]` may validate
   existing state only. Environment synchronization and dependency updates
   belong to explicit setup or reviewed maintenance changes, not to a default
   pre-commit hook. Commands such as `uv sync --locked`, `npm ci`, `pnpm install`, `cargo update`, and `poetry update` must not be inferred as hooks.
5. **Fallback without invention**: If a stack has no deterministic native
   lockfile check, require staged manifest/lockfile parity through
   `check_lockfile_sync.py` and document the limitation. Do not replace the
   missing check with a mutating install, resolver, updater, or sync command.
   Treat `go mod verify` as module-cache integrity auditing, not as a
   substitute for manifest/lockfile coherence.
