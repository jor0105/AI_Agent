# Conceptual Gate Catalog and Tool Mapping

> Summary: Mapping of conceptual quality gate slots to project-native tools,
> including the structural coverage required from `[LINTER]` and the separate
> responsibilities of `[TEST_INTEGRITY]`.

## 1. Quality Gate Slot Matrix

| Slot                          | Purpose                                                                                                  | Python                                                               | JS / TS                                                                       | Go / Rust                                                                                              |
| :---------------------------- | :------------------------------------------------------------------------------------------------------- | :------------------------------------------------------------------- | :---------------------------------------------------------------------------- | :----------------------------------------------------------------------------------------------------- |
| **`[HYGIENE]`**               | Whitespace, EOF, merge markers, large files                                                              | `pre-commit-hooks`                                                   | `pre-commit-hooks` / `lint-staged`                                            | `git diff --check`                                                                                     |
| **`[SYNTAX]`**                | Fast parse/compilation check                                                                             | `python -m py_compile`                                               | `tsc --noEmit`                                                                | `go vet` / `cargo check`                                                                               |
| **`[FORMATTER]`**             | Deterministic code formatting (auto-fix)                                                                 | `ruff format`                                                        | `prettier --write` / `biome format`                                           | `gofmt -w` / `cargo fmt`                                                                               |
| **`[LINTER]`**                | Code quality plus structural complexity, nesting, flow, error handling, and routine scope                | `ruff check` or configured equivalent                                | `eslint` / `biome lint` or configured equivalent                              | `golangci-lint` / `cargo clippy` or configured equivalent                                              |
| **`[TYPE_CHECK]`**            | Static typing validation                                                                                 | `mypy` / `pyright`                                                   | `tsc --noEmit`                                                                | Built-in                                                                                               |
| **`[CIRCULAR_DEPENDENCIES]`** | **Required** detection of direct/indirect import cycles; fail new cycles and ratchet historical baseline | `import-linter` / `pycycle`                                          | `madge --circular` / `dependency-cruiser`                                     | Go compiler / `cargo metadata` plus configured architecture check                                      |
| **`[SECRETS]`**               | Prevent committing credentials/keys                                                                      | `gitleaks protect`                                                   | `gitleaks protect`                                                            | `gitleaks protect`                                                                                     |
| **`[DIFF_SANITY]`**           | Detect debuggers, stubs, unverified bypasses                                                             | `check_diff_sanity.py`                                               | `check_diff_sanity.py`                                                        | `check_diff_sanity.py`                                                                                 |
| **`[LOCKFILE]`**              | Deterministic manifest/lockfile validation; never automatic dependency updates                           | `uv lock --check` / `poetry check --lock` / `check_lockfile_sync.py` | `check_lockfile_sync.py` plus a project-native immutable check when available | `cargo check --locked` / `check_lockfile_sync.py`; Go may configure `go mod tidy -diff` when supported |
| **`[TEST_INTEGRITY]`**        | Prevent test deletions, focused tests, skips, assertion loss, and hollow verification                    | `check_test_integrity.py` plus native test lint                      | `check_test_integrity.py` plus native test lint                               | `check_test_integrity.py` plus native test lint                                                        |
| **`[TESTS_FAST]`**            | Run unit tests impacted by changed files                                                                 | `pytest -m "not slow" <files>`                                       | `vitest related <files>` / `jest -o`                                          | `go test -short <pkg>`                                                                                 |

## 2. Structural `[LINTER]` Profile

The project-native linter must cover or explicitly classify each dimension.
Defaults apply to new or changed routines; historical findings may use a
non-growing baseline, but the baseline must not authorize a regression.

| Dimension             | Blocking default                                                    | Review signal                              | Interpretation                                                                                              |
| :-------------------- | :------------------------------------------------------------------ | :----------------------------------------- | :---------------------------------------------------------------------------------------------------------- |
| Cyclomatic complexity | Maximum `15`                                                        | Greater than `10`                          | Record as cyclomatic complexity, not as a literal count of runtime paths.                                   |
| Cognitive complexity  | Maximum `15` when supported                                         | Greater than `10`                          | Keep separate from cyclomatic complexity; do not silently substitute one metric for the other.              |
| Nesting depth         | Maximum `4`                                                         | Greater than `3`                           | Use the analyzer's syntactic nesting semantics for conditions, loops, and handlers.                         |
| Flow simplification   | Reject redundant branches after terminal statements when supported  | Review avoidable nesting                   | Prefer guard clauses when they clarify the main path; never enforce a blanket single-exit rule.             |
| Error handling        | Reject empty or silent handlers and broad catches in ordinary logic | Review handler scope and preserved context | A boundary catch is valid only when narrow, actionable, and cause-preserving.                               |
| Routine scope         | Maximum `50` executable statements                                  | Greater than `30`                          | Lines are not statements. More than five positional parameters is a review signal, not a universal failure. |

Classify every dimension in the gap analysis:

- `ENABLED`: a native deterministic rule is configured with metric, threshold,
  and scope.
- `DELEGATED`: another existing gate proves the same property deterministically.
- `MANUAL`: no adequate automatic rule exists and an explicit review control
  remains.
- `UNSUPPORTED`: the stack cannot provide the requested deterministic check.

Only `ENABLED` and `DELEGATED` satisfy a complete blocking profile. When the
user requested blocking enforcement, `UNSUPPORTED` is an `ERROR`; do not add an
unrequested dependency or claim a false `PASS`. `MANUAL` must be reported as
partial coverage with residual risk.

Structural checks require parser-aware analysis. `check_diff_sanity.py` remains
a staged-text gate and must not be extended with regexes that pretend to count
nesting, statements, or complexity.

Assertion vacuum and tautological assertions belong to `[TEST_INTEGRITY]`.
Use native test lint when available and otherwise require review through the
`testing-patterns` skill. `check_test_integrity.py` does not prove assertion
meaning across every framework.

## 3. Configuration & Structured Data Validations

- **YAML**: `check-yaml` or `yamllint`
- **JSON**: `check-json` or `jq . <file>`
- **TOML**: `check-toml` or `taplo check`
- **Docker**: `hadolint`
- **Shell**: `shellcheck`, `bash -n`

## 4. Tool Selection Rules

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
6. **Structural coverage must be explicit**: Inspect the configured linter for
   every structural dimension and record its metric, threshold, scope, and
   coverage status. Tool names in this catalog are examples, not mandatory
   dependencies.
7. **Keep structural rules read-only**: Do not auto-fix conditionals, returns,
   exception handlers, or other business logic from a commit hook.
