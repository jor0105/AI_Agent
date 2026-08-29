# AGENTS.md

> Owner: Jordan Estralioto (@jordanestralioto)
> Last reviewed: 2026-08-29
> Status: Confirmed
> Knowledge class: Agent policy

Operating policy for coding agents working in this repository. It gives agents
the system map, durable engineering rules, official commands, and safe limits;
detailed contracts remain in their owning documentation.

## System Overview

**Create Agents AI** (PyPI package `createagents`) is a Python library for
building conversational AI agents with pluggable OpenAI and Ollama providers,
extensible tools, conversation history, metrics, and an interactive terminal
CLI. Python applications consume its public exports from
`src/createagents/__init__.py`; the public facade is
`src/createagents/main/facade/client.py`. The repository owns the framework and
its CLI, not the external provider services.

The runtime boundary accepts agent configuration, user messages, tools, and
environment configuration. It produces complete or streaming responses,
conversation state, metrics, and terminal output. Non-negotiable invariants are
the inward dependency direction, provider isolation behind application ports,
explicit composition in `src/createagents/main/composers/agent_composer.py`,
and silent library logging until the consumer opts in through `LoggingConfig`.
The `.agents/` harness is a development aid, not part of the published product.

**The product is not the harness.** Two unrelated things are called "agent" here:

|         | What it is                                        | Where                                  | Published    |
| ------- | ------------------------------------------------- | -------------------------------------- | ------------ |
| Product | the library consumers install                     | `src/createagents/`, `docs/`, `tests/` | yes, to PyPI |
| Harness | tooling that assists whoever develops the product | `.agents/` + hidden mirrors            | no           |

`.claude/`, `.codex/`, `.opencode/`, `opencode.json` and `.github/agents/` are
gitignored on purpose and never ship; `uv build` packages only `src/`.

## Success Metrics

| Metric        | Target                                                   |
| ------------- | -------------------------------------------------------- |
| Coverage gate | 85% (`pytest.ini`, `.github/workflows/pipeline.yml`)     |
| Python matrix | >= 3.12 (`pyproject.toml`; CI runs 3.12, 3.13, and 3.14) |

## Pipeline Architecture

A library plus a CLI, not a data pipeline. The runtime starts at
`src/createagents/main/facade/client.py` (`CreateAgent`), which delegates
construction and dependency wiring to
`src/createagents/main/composers/agent_composer.py` (`AgentComposer`). The
composition root creates the application use cases in
`src/createagents/application/use_cases/`, injects ports, and obtains provider
adapters through `src/createagents/infra/factories/chat_adapter_factory.py`
(`ChatAdapterFactory`). Provider implementations live under
`src/createagents/infra/adapters/`; the current providers are OpenAI and Ollama.

The dependency direction is `src/createagents/presentation/` /
`src/createagents/infra/` → `src/createagents/application/` →
`src/createagents/domain/`. `src/createagents/application/` must depend only on
`src/createagents/domain/`; `src/createagents/main/` is the composition root
that knows the concrete infrastructure. The terminal entrypoint is
`src/createagents/presentation/cli/application/chat_cli_app.py`; its command
handlers are resolved by the CLI registry. `CreateAgent.start_cli()` reaches
that presentation layer lazily, so consumers that only use the library do not
need to start the terminal UI.

For navigation, open [README.md](README.md) for identity and onboarding, then
[docs/dev-guide/architecture-developer.md](docs/dev-guide/architecture-developer.md)
for the macro design and
[docs/dev-guide/cli-architecture.md](docs/dev-guide/cli-architecture.md) for the
terminal boundary. Use [docs/dev-guide/contribute.md](docs/dev-guide/contribute.md)
for the contribution workflow and the sources in Related Documentation for
commands, testing, governance, and harness details.

## Configuration & Runtime

| Surface                         | Location                                                         | Purpose                                                                                  |
| ------------------------------- | ---------------------------------------------------------------- | ---------------------------------------------------------------------------------------- |
| Manifest and tool configuration | `pyproject.toml`                                                 | dependency metadata, Python range, build backend, and tool configuration                 |
| Resolved dependencies           | `uv.lock`                                                        | uv-owned lockfile; never hand-edit                                                       |
| Test configuration              | `pytest.ini`                                                     | test paths, markers, options, and the 85% coverage floor                                 |
| Secret scanning policy          | `.gitleaks.toml`                                                 | minimal default-rule policy used by local and CI Gitleaks                                |
| Local quality hooks             | `.pre-commit-config.yaml`                                        | 44 hooks: 38 pre-commit, 4 pre-push, 1 commit-msg, and 1 manual                          |
| Public environment names        | `.env.example`                                                   | names only for provider, retry, tool-iteration, logging, and file-tool settings          |
| Documentation configuration     | `mkdocs.yml`                                                     | MkDocs Material site configuration and navigation                                        |
| CI, docs, and release workflows | `.github/workflows/` (`pipeline.yml`, `docs.yml`, `publish.yml`) | quality gates/tests (`pipeline.yml`), docs deploy (`docs.yml`), and PyPI (`publish.yml`) |
| Agent harness manifest          | `.agents/harness.json`                                           | internal component declarations for agents, skills, tools, and workflows                 |

### Commands

| Action                        | Command                                                                                                                                  |
| ----------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------- |
| Install dependencies          | `uv sync --locked`                                                                                                                       |
| Install hooks                 | `uv run --locked --no-sync pre-commit install --install-hooks`                                                                           |
| Pre-commit hooks (38)         | `uv run --locked --no-sync pre-commit run --all-files`                                                                                   |
| Pre-push hooks (4)            | `uv run --locked --no-sync pre-commit run --all-files --hook-stage pre-push`                                                             |
| Safe local tests and coverage | `uv run --locked --no-sync pytest -m 'not integration and not slow' -ra --cov`                                                           |
| Primary type checking         | `uv run --locked --no-sync mypy src --pretty`                                                                                            |
| Supporting type checking      | `uv run --locked --no-sync mypy tests scripts --disable-error-code no-untyped-def --pretty`                                              |
| Ruff lint and format          | `uv run --locked --no-sync ruff check src tests scripts`                                                                                 |
| Source security scan          | `uv run --locked --no-sync bandit -c pyproject.toml -r src -ll`                                                                          |
| Dependency audit              | `uv run --locked --no-sync pip-audit --timeout 60`                                                                                       |
| Strict documentation build    | `uv run --locked --no-sync mkdocs build --strict`                                                                                        |
| Package build                 | `uv build`                                                                                                                               |
| Optional harness mirror check | `uv run --locked --no-sync harness-sync --check`                                                                                         |
| Harness evidence              | `uv run --locked --no-sync python .agents/scripts/harness_verify.py --evidence-path openspec/changes/<name>/evidence/gate-report.json`   |
| Verify harness evidence       | `uv run --locked --no-sync python .agents/scripts/harness_verify.py --verify-evidence openspec/changes/<name>/evidence/gate-report.json` |

Run all Python tooling and tests directly through `uv run --locked --no-sync`.
Use `uv sync --locked` only as explicit environment bootstrap; local hooks must
not synchronize the environment or update dependency resolution.

The normal hooks do not require `central-skills`. `.agents/` is tracked because
it carries the portable validator projection. `.codex/`, `.claude/`, `.opencode/`,
and `.github/prompts/` are generated ignored mirrors outside the Git index.
`check-harness-sync` is the optional manual-only mirror check; if its external
dependency is unavailable, its result is `skipped`, not a normal-hook pass.
Review mutator output before staging and stage only explicit paths. In a dirty
working tree, do not use `git add .` or `git add -A`.

The harness commands apply only when an OpenSpec change exists. They accept a
per-change JSON gate report only at
`openspec/changes/<name>/evidence/gate-report.json`; `<name>` is an existing
change directory, not an arbitrary filesystem path. The first command creates
the report and the second re-checks an existing report. The report uses the
`harness` effective profile and must be current before it is trusted.

Public environment names, with no values copied into this policy, are
`OPENAI_API_KEY`, `OPENAI_TIMEOUT`, `OPENAI_MAX_RETRIES`,
`OPENAI_MAX_TOOL_ITERATIONS`, `OLLAMA_HOST`, `OLLAMA_MAX_RETRIES`,
`OLLAMA_MAX_TOOL_ITERATIONS`, `LOG_LEVEL`, `LOG_TO_FILE`, `LOG_FILE_PATH`,
`LOG_JSON_FORMAT`, and `FILE_TOOL_BASE_DIR`. OpenAI requires
`OPENAI_API_KEY`; Ollama requires a reachable server. The package installs a
`NullHandler` and remains silent until logging is explicitly configured through
`LoggingConfig`.

## Technical Stack

Python `>=3.12,<4.0` is managed and run with `uv`. The application framework is
Create Agents AI itself; no web framework is confirmed. The package uses the
runtime libraries `openai`, `ollama`, `python-dotenv`, `defusedxml`, and `rich`,
with optional file-tool dependencies declared separately in `pyproject.toml`.
It follows Clean Architecture and SOLID. `setuptools` is the packaging/build
backend, not the dependency manager. Quality and documentation tooling includes
Ruff (79-column, single-quote format, including Google-style docstrings via
the D rules), mypy, pytest,
pytest-cov, pytest-asyncio, Bandit, pip-audit, import-linter, the cycle detector
at `scripts/check-import-cycles.py`, mdformat, yamllint, actionlint, codespell,
gitleaks, zizmor, MkDocs Material, and setuptools. `pyproject.toml` is the
authority on declared versions and configuration.

## Mandatory Rules

- Do not write irrelevant comments in code.

- Verify files before editing; do not assume structure or behavior. A claim
  about current behavior needs a path you opened, not a recollection.

- Plan before modifying and keep scope small, reviewable, and verifiable.
  Deliver only what is necessary to satisfy the request end-to-end; do not
  bundle unrequested changes or mix structural refactors with bug fixes.

- Write well-factored code with clear single responsibility per function,
  class, or module; do not create monolithic functions that handle multiple
  concerns.

- Never leave duplicated logic; extract common functionality into shared
  functions or modules.

- Never introduce circular imports or mutual module dependencies.

- Tests must prove relevant behavior, edge cases, and regressions, not
  merely nominal line coverage. Mirror the layer touched under `tests/`. Mark
  external API tests with `@pytest.mark.integration` and slow tests with
  `@pytest.mark.slow`; do not spend external provider quota in safe local runs.

- Always act as a skeptic: verify hypotheses empirically instead of
  accepting them, whether they came from the user or from you. Never flatter
  the user or engage in sycophantic agreement.

- Do not write code files whose sole purpose is to re-export other files or
  modules without added value.

- `__init__.py` files must never contain code or implementation logic; they
  must only contain explicit exports.

- Never edit generated mirrors or generated files directly; change the source
  and re-run its generation or sync command.

- Chat is Portuguese (or adapted to the user's preferred language). Product
  documentation is maintained bilingually in both Portuguese (`docs/`) and
  English (`docs/en/`). Code, comments, Git commits/branches/PRs, and planning
  artifacts are English. Commit messages use Conventional Commits.

- Use `uv` for every dependency operation and `uv run --locked --no-sync` for
  every Python tool or test. Never use `pip install`, Poetry, or a second
  lockfile for repository development. The supported Python range is
  `>=3.12,<4.0`.

- Follow the repository's established naming, formatting, ownership, and module
  boundaries. Use `src/createagents/` as the real package root and prefer
  repository-native entrypoints and official scripts before ad hoc commands.

- Preserve Clean Architecture and SOLID: the existing ports, adapters, use
  cases, and composition patterns are the framework to extend; do not add
  a competing framework or parallel architectural path without an explicit
  decision.

- `src/createagents/domain/` imports nothing above it;
  `src/createagents/application/` imports **only** `src/createagents/domain/`,
  never `src/createagents/infra/`, `src/createagents/main/`, or
  `src/createagents/presentation/`. If an application component
  needs infrastructure, declare a port in
  `src/createagents/application/interfaces/` and let
  `src/createagents/main/composers/agent_composer.py` inject it. A function-level
  import hides a cycle instead of removing it.

- All dependency wiring goes in
  `src/createagents/main/composers/agent_composer.py`. Never instantiate
  adapters or use cases from `src/createagents/presentation/` or
  `src/createagents/main/facade/`.

- New provider adapters belong under `src/createagents/infra/adapters/` and are
  registered in `ChatAdapterFactory` at
  `src/createagents/infra/factories/chat_adapter_factory.py`. New tools implement
  `BaseTool` from `src/createagents/domain/`. New CLI handlers belong under
  `src/createagents/presentation/cli/commands/` and are registered in
  `ChatCLIApplication._setup_commands` at
  `src/createagents/presentation/cli/application/chat_cli_app.py`. Never branch
  on provider names inside an application use case.

- The published API is exported by `src/createagents/__init__.py` and includes
  the public signatures of `src/createagents/main/facade/client.py`. Do not
  change either public boundary without an explicit decision.

- OpenAI requires `OPENAI_API_KEY`. Ollama does not require an API key, but it
  does require a reachable server. Keep these provider boundaries in
  infrastructure adapters rather than application use cases.

- Keep XML parsing on `defusedxml`. Credentials resolve from the environment;
  never hardcode keys or endpoints, never read or commit `.env` values, and
  extend `.env.example` with names only.

- The package logger stays silent initially through `NullHandler`; consumers
  configure logging explicitly through `LoggingConfig`.

- `.agents/` is internal harness tooling, not product code. Its component
  manifest is `.agents/harness.json`; do not move harness content into
  `src/createagents/` or `docs/`, and do not edit generated mirrors directly.
  Gitleaks intentionally scans every tracked `.agents/` file, while generic
  mutating hooks exclude the five external harness roots.

- Treat runtime code and accepted decisions as current state; treat proposals
  and unimplemented specs as planned state.

- Put detailed contracts in their canonical doc and link to them; do not
  re-inline a table that an owner document already holds.

- Update tests, contracts, and canonical documentation when behavior or a public
  boundary changes.

- Do not leave dead code, unused compatibility paths, duplicated ownership, or
  stale documentation after a completed clean cutover unless compatibility is an
  explicit project requirement.

- Do not silently change public contracts, persisted formats, authentication
  flows, security boundaries, runtime topology, or deployment behavior.

- "Done" means terminal output or a gate result reported back. Report
  `passed`, `failed`, `skipped`, and `external_failure` as four distinct
  outcomes; never summarize a skipped or environment-failed gate as a pass.

## Execution Policy

### Precedence

Rank: system constraints → repository/workspace policy and tooling → user request. Act on
the highest-ranking unambiguous, safe instruction without asking again. Skills
and subagent prompts may tighten this section; they never relax it.
If same-rank instructions conflict, prefer the more specific and safer one.

### Hard Blocks

Never execute without the user naming the exact action:

- `git reset --hard`, `git reset --soft`, `git reset --mixed`, `git reset HEAD`,
  `git clean -fd`, forced checkouts (including `git checkout -f`), or any
  history rewrite.
- `git push --force`, `git push --force-with-lease`, `git rebase --root`,
  `git rebase -i --root`, `git filter-branch`, `git reflog expire`,
  `git update-ref --delete`, or any destructive remote/history operation.
- Remote piping: `curl | bash`, `wget | sh`, or any equivalent.
- Writes to `/etc`, `~/.ssh`, system packages, or paths outside the authorized
  repository/workspace scope.
- Anything that bypasses permissions, sandbox limits, authentication, or
  authorization controls.
- Reverting, resetting, unstaging, editing, or regenerating pre-existing work
  outside the authorized scope.

Specific to this repository: publishing to PyPI or triggering
`.github/workflows/publish.yml`; `git commit --no-verify` or any pre-commit
bypass; `git add -f` on an ignored path; running `@pytest.mark.integration`
tests without explicit authorization (spends real provider quota); or changing
any file under `.github/workflows/` without explicit authorization.

### Secrets

Never seek, log, copy, or expand secrets. Treat `.env`, API keys, tokens,
cookies, auth sessions, certificates, and private keys as sensitive. If one
appears in output: stop, redact it, and report that sensitive data was found.

### Repo Alignment

Follow the repository's canonical contracts, documentation, current code,
accepted decisions, and official scripts before inventing a new workflow. Prefer
existing project patterns, entrypoints, and abstractions over ad hoc
alternatives. Do not silently change public contracts, persisted formats, auth
flows, runtime topology, or security boundaries. If code, docs, and tooling
disagree: stop, report the ambiguity, and identify the conflicting sources.

### Autonomy

Execute reversible repository/workspace changes without confirmation only when
all hold:

- Goal and success criteria are unambiguous.
- Change is contained inside the authorized repository/workspace scope.
- Change is fully recoverable via version control.

Stop and ask when: ambiguous scope, destructive side effects, external systems,
production impact, secrets involved, or conflict between same-rank
instructions. Also stop and ask before changing the published API, a `version`
bump, or any `.github/workflows/` file. Do not autonomously alter
authentication or authorization boundaries; stop and ask for an explicit
decision.

### Validation

Before concluding code or tooling changes, use the repository's official
validation entrypoint when applicable. Prefer repository-native commands and
scripts over custom one-off equivalents. The required local entrypoints are
`uv run --locked --no-sync pre-commit run --all-files` and
`uv run --locked --no-sync pytest -m 'not integration and not slow' -ra --cov`
for behavior changes. The aggregated agent-facing harness accepts
`uv run --locked --no-sync python .agents/scripts/harness_verify.py --evidence-path openspec/changes/<name>/evidence/gate-report.json`
(state which `effectiveProfile` ran). Report `passed`, `failed`, `skipped`, and
`external_failure` separately. If validation is skipped, unsupported, or
failing, report that explicitly with the reason and impact; never treat a skip
or environment failure as a pass.

### Execution Safety

Before any destructive, publish, migration, deployment-like, or external-state
operation: state exactly what will be affected, inspect and validate the target,
run a dry run when supported, and keep the steps readable. Inspect the command
path before running local scripts; stop if a script is obfuscated, downloads
executables, or touches secrets.

### Failure Handling

A security lock, permission denial, or authorization boundary stops the task. Do
not work around it — report the block, the evidence, and the safest next step.
When verification returns `securityRequired=true`, the verdict belongs to
`security-engineer` and closes only as `cleared`, `requires_remediation`, or
`blocked`; an audit that could not be completed is `blocked`, not `cleared`. All
such decisions fail closed until the relevant security or authorization
boundary is explicitly cleared.

## Related Documentation

Open only what the task needs. Read these sources in progressive-disclosure
order:

| Doc                                                                                                                                                                              | Knowledge class          | Purpose                                                                      |
| -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------ | ---------------------------------------------------------------------------- |
| [README.md](README.md)                                                                                                                                                           | Unclassified             | Product identity and onboarding; open first for the public entrypoint.       |
| [docs/index.md](docs/index.md)                                                                                                                                                   | Unclassified             | Published documentation index and public navigation.                         |
| [docs/dev-guide/architecture-developer.md](docs/dev-guide/architecture-developer.md)                                                                                             | Unclassified             | Clean Architecture layer ownership and runtime design.                       |
| [docs/dev-guide/cli-architecture.md](docs/dev-guide/cli-architecture.md)                                                                                                         | Unclassified             | CLI boundary, registry, handlers, and terminal flow.                         |
| [docs/dev-guide/contribute.md](docs/dev-guide/contribute.md)                                                                                                                     | Unclassified             | Contribution workflow, quality gates, and English Conventional Commits.      |
| [docs/dev-guide/logging_guide.md](docs/dev-guide/logging_guide.md)                                                                                                               | Unclassified             | Consumer logging configuration and the library's silent-by-default behavior. |
| [docs/reference/api.md](docs/reference/api.md)                                                                                                                                   | Unclassified             | Public API signatures and released contract examples.                        |
| [docs/user-guide/installation-user.md](docs/user-guide/installation-user.md)                                                                                                     | Unclassified             | User installation and provider/environment setup.                            |
| [tests/](tests/)                                                                                                                                                                 | Unclassified             | Behavioral proof organized by the layer under test.                          |
| [pyproject.toml](pyproject.toml), [pytest.ini](pytest.ini), [.pre-commit-config.yaml](.pre-commit-config.yaml), [.github/workflows/pipeline.yml](.github/workflows/pipeline.yml) | Unclassified             | Tooling, tests, hooks, and the complete CI gate source.                      |
| [.agents/harness.json](.agents/harness.json)                                                                                                                                     | Agent harness manifest   | Harness component declarations and ownership of internal tooling.            |
| [.agents/agents/developer-engineer.agent.md](.agents/agents/developer-engineer.agent.md)                                                                                         | Agent prompt (canonical) | Developer implementation scope and delivery responsibilities.                |
| Not documented                                                                                                                                                                   | Not documented           | No architecture decision record directory is confirmed in this repository.   |
