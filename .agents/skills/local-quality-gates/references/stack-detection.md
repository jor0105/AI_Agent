# Workspace Stack and Toolchain Detection Guide

> Summary: Heuristics and indicator files for identifying languages, package managers, formatters, linters, typecheckers, and test runners in a workspace.

## 1. Package Managers and Language Indicators

| Ecosystem           | Manifest File                         | Lockfile            | Execution Prefix     |
| :------------------ | :------------------------------------ | :------------------ | :------------------- |
| **Python (uv)**     | `pyproject.toml`                      | `uv.lock`           | `uv run`             |
| **Python (poetry)** | `pyproject.toml`                      | `poetry.lock`       | `poetry run`         |
| **Python (pip)**    | `requirements.txt`, `requirements.in` | `requirements.txt`  | `python -m`          |
| **Node (pnpm)**     | `package.json`                        | `pnpm-lock.yaml`    | `pnpm exec` / `pnpm` |
| **Node (npm)**      | `package.json`                        | `package-lock.json` | `npx` / `npm run`    |
| **Node (yarn)**     | `package.json`                        | `yarn.lock`         | `yarn`               |
| **Node (bun)**      | `package.json`                        | `bun.lockb`         | `bun x` / `bun`      |
| **Rust**            | `Cargo.toml`                          | `Cargo.lock`        | `cargo`              |
| **Go**              | `go.mod`                              | `go.sum`            | `go`                 |
| **PHP**             | `composer.json`                       | `composer.lock`     | `composer exec`      |

## 1.1 Dependency Lifecycle Classification

The manifest and lockfile table identifies the files to protect; it does not
tell the agent to update dependencies in a hook. Classify the package-manager
commands into three separate roles before composing a gate:

| Role                       | Allowed in pre-commit?                                                                  | Examples                                                                                                                                                      |
| :------------------------- | :-------------------------------------------------------------------------------------- | :------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| Lockfile validation        | Yes, when deterministic and it does not rewrite dependency declarations or the lockfile | `uv lock --check`, `poetry check --lock`, `cargo check --locked`, a project-configured `go mod tidy -diff` when supported, or staged manifest/lockfile parity |
| Environment sync/bootstrap | No by default; run explicitly during setup                                              | `uv sync --locked`, `poetry install`, `npm ci`, `pnpm install --frozen-lockfile`, `yarn install --immutable`, `go mod download`                               |
| Dependency update/resolve  | No; perform as a reviewed change                                                        | `uv lock --upgrade`, `poetry update`, `npm update`, `pnpm update`, `yarn up`, `bun update`, `cargo update`, `go get -u`, `composer update`                    |

The execution prefix (`uv run`, `pnpm exec`, `cargo`, and so on) is not a
lockfile policy by itself. If it implicitly synchronizes an environment, use
it only as an existing project contract or add the manager's no-sync option
after explicit setup. Never infer an updater from the presence of a manifest
and lockfile. When the manager has no safe native check, use the shared
lockfile-parity gate and document the limitation instead of inventing a
mutating command.

Go nuance: `go.sum` records module checksums, not a fully resolved lockfile.
`go mod verify` audits downloaded module-cache contents and may add missing
checksum entries, so it is not a read-only `go.mod`/`go.sum` coherence check.
Prefer `go mod tidy -diff` when the project's Go version supports it and the
observed cost is acceptable; otherwise use staged parity and keep cache
integrity auditing in a separate gate.

## 2. Toolchain Discovery Heuristics

Before selecting a tool, inspect the workspace configuration files:

### Python

- **Ruff**: Search for `[tool.ruff]` in `pyproject.toml` or `ruff.toml`.
- **Mypy**: Search for `[tool.mypy]` in `pyproject.toml` or `mypy.ini` / `setup.cfg`.
- **Pyright**: Search for `pyrightconfig.json` or `[tool.pyright]` in `pyproject.toml`.
- **Pytest**: Search for `[tool.pytest.ini_options]` in `pyproject.toml` or `pytest.ini` / `conftest.py`.
- **Circular imports**: Reuse `import-linter`, `pycycle` or an existing architecture/dependency command. If none is configured, the required gate must fail closed until a deterministic local command is selected.

### JavaScript / TypeScript

- **Biome**: Search for `biome.json` or `biome.jsonc`.
- **ESLint**: Search for `eslint.config.js`, `.eslintrc.*`, or `"eslintConfig"` in `package.json`.
- **Prettier**: Search for `.prettierrc*`, `prettier.config.js`, or `"prettier"` in `package.json`.
- **TypeScript (tsc)**: Search for `tsconfig.json`.
- **Test Runners**: Inspect `package.json` for `vitest`, `jest`, `playwright`, `mocha`.
- **Circular dependencies**: Reuse `madge --circular`, `dependency-cruiser` or an existing package script. Do not treat the absence of a dedicated package as permission to omit the required gate.

### Go

- Standard: `gofmt`, `go vet`, `golangci-lint` (`.golangci.yml`).
- **Circular imports**: The Go compiler rejects import cycles; run the narrowest affected `go test`/`go list` package check as the required gate and report compiler errors as `FAIL`.

### Rust

- Standard: `cargo fmt`, `cargo clippy` (`clippy.toml`), `cargo check`.
- **Circular dependencies**: Inspect the existing Cargo/module architecture command. `cargo check` remains mandatory for compiler-level cycles; use any configured dependency graph checker for module-level cycles.

### Other or polyglot repositories

- Locate the project's configured dependency graph or architecture validator and wire it into the required `[CIRCULAR_DEPENDENCIES]` slot. A missing tool is an `ERROR` during setup, not an optional gate.

## 3. Existing Hook Runner Detection

Check for prior git hook configurations:

1. `.pre-commit-config.yaml` -> Python-based pre-commit framework.
2. `.husky/` -> Node Husky hook runner.
3. `lefthook.yml` / `.lefthook/` -> Lefthook binary runner.
4. `.git/hooks/` -> Plain shell scripts.

## 4. Reuse-First Decision Matrix

1. If the repository already uses `biome`, do not introduce `eslint` or `prettier`.
2. If the repository uses `ruff`, do not introduce `black`, `flake8`, or `isort`.
3. If the repository already has an active runner (e.g. Husky or pre-commit), extend the existing runner instead of replacing it.
