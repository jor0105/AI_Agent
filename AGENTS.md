# AGENTS.md

> Owner: Jordan Estralioto (@jordanestralioto)
> Last reviewed: 2026-08-29
> Status: Confirmed
> Knowledge class: Agent policy

Operational policy for coding agents working in this repository. This file is a
durable system map, a development policy, and a navigation aid. Detailed
implementation, provider, CLI, and harness contracts belong to their owning
documents.

## System Overview

Create Agents AI (PyPI package createagents) is a Python library and terminal
CLI for applications that build conversational AI agents. Consumers configure an
agent, message it, and optionally supply tools; the library returns complete or
streaming responses, conversation state, metrics, and terminal output.

The product supports pluggable provider and tool integrations while keeping
external services outside the repository boundary. Its non-negotiable
invariants are inward Clean Architecture dependencies, provider isolation behind
application ports, explicit composition of concrete dependencies, and silent
library logging until a consumer configures it.

The .agents directory is internal development harness tooling, not published
product code. Do not treat harness configuration or generated client mirrors as
part of the createagents package contract.

## Success Metrics

| Metric           | Target                                                  |
| ---------------- | ------------------------------------------------------- |
| Coverage gate    | 85% minimum, enforced by pytest.ini and CI              |
| Supported Python | >=3.12,\<4.0; CI validates CPython 3.12, 3.13, and 3.14 |

## Pipeline Architecture

This is a library plus a CLI, not a data pipeline. Runtime starts at
`src/createagents/main/facade/client.py` (`CreateAgent`) and delegates concrete
construction to
`src/createagents/main/composers/agent_composer.py` (`AgentComposer`). The
composer builds use cases from `src/createagents/application/use_cases/` and
resolves provider ports through
`src/createagents/infra/factories/chat_adapter_factory.py`
(`ChatAdapterFactory`), whose implementations live under
`src/createagents/infra/adapters/`. The runtime returns a response or stream and
updates conversation history and metrics.

Dependencies point inward: presentation and infrastructure depend on
application and domain abstractions; application depends on domain behavior and
ports declared under `src/createagents/application/interfaces/`; domain remains
independent of outer layers. The public package exports in
`src/createagents/__init__.py` and the facade are semver-relevant boundaries.
The terminal boundary is
`src/createagents/presentation/cli/application/chat_cli_app.py`; the facade
reaches it lazily through `CreateAgent.start_cli()`.

For a safe first change, read README.md for product identity, then
docs/dev-guide/architecture-developer.md for layer ownership. Read
docs/dev-guide/cli-architecture.md only for terminal changes and
docs/dev-guide/contribute.md for quality gates and extension procedures. Those
documents own module-level details and registration steps.

## Configuration & Runtime

| Surface                                   | Location                       | Purpose                                                                           |
| ----------------------------------------- | ------------------------------ | --------------------------------------------------------------------------------- |
| Package, build, and quality configuration | pyproject.toml                 | Python range, dependencies, build backend, import boundaries, and tool settings   |
| Resolved dependencies                     | uv.lock                        | Locked uv dependency state; never hand-edit                                       |
| Public runtime configuration              | .env.example                   | Public environment variable names and documented defaults; never copy real values |
| Test configuration                        | pytest.ini                     | Test markers, discovery, and the coverage floor                                   |
| Local quality hooks                       | .pre-commit-config.yaml        | Repository-owned validation and formatting hooks                                  |
| CI quality contract                       | .github/workflows/pipeline.yml | Supported Python matrix and required CI gates                                     |
| Documentation site                        | mkdocs.yml                     | MkDocs Material configuration and navigation                                      |
| Internal harness                          | .agents/harness.json           | Development harness declaration; open only for harness work                       |

### Commands

| Action                            | Command                                                                                   |
| --------------------------------- | ----------------------------------------------------------------------------------------- |
| Bootstrap locked dependencies     | uv sync --locked                                                                          |
| Install repository hooks          | uv run --locked --no-sync pre-commit install --install-hooks                              |
| Run pre-commit validation         | uv run --locked --no-sync pre-commit run --all-files                                      |
| Run pre-push validation           | uv run --locked --no-sync pre-commit run --all-files --hook-stage pre-push                |
| Run safe local tests and coverage | uv run --locked --no-sync pytest -m 'not integration and not slow' -ra --cov              |
| Type-check product code           | uv run --locked --no-sync mypy src --pretty                                               |
| Type-check tests and scripts      | uv run --locked --no-sync mypy tests scripts --disable-error-code no-untyped-def --pretty |
| Lint product, tests, and scripts  | uv run --locked --no-sync ruff check src tests scripts                                    |
| Scan product source               | uv run --locked --no-sync bandit -c pyproject.toml -r src -ll                             |
| Audit dependencies                | uv run --locked --no-sync pip-audit --timeout 60                                          |
| Build documentation strictly      | uv run --locked --no-sync mkdocs build --strict                                           |
| Build the package                 | uv build                                                                                  |

Run Python tooling through uv run --locked --no-sync. Use uv sync --locked only
as deliberate environment bootstrap or when the task explicitly changes locked
dependencies. Do not introduce pip, Poetry, or another lockfile for repository
development.

Use .env.example for public configuration names and provider prerequisites. It
is not a source of secret values; never read, print, copy, or commit a real .env
file.

## Technical Stack

The package targets Python >=3.12,\<4.0, uses uv for dependency management and
command execution, and uses setuptools as its build backend. It follows Clean
Architecture and SOLID with provider adapters for OpenAI and Ollama.

Ruff formats and lints with a 79-character line length, single-quote formatting,
Google-style docstrings, and McCabe complexity capped at 10. Mypy type-checks;
pytest and pytest-cov validate behavior and coverage; Bandit scans product
source; pip-audit audits dependencies; import-linter and
`scripts/check-import-cycles.py` protect boundaries; pre-commit coordinates
local checks; and MkDocs Material builds documentation. `pyproject.toml` owns
the exact rule selection and scoped exceptions; do not treat an existing
per-file ignore as general precedent.

## Mandatory Rules

- Do not write irrelevant comments in code.
- Verify files before editing; do not assume structure or behavior.
- Plan before modifying and keep scope small, reviewable, and verifiable.
- Write well-factored code with clear single responsibility per function,
  class, or module; do not create monolithic functions that handle multiple
  concerns.
- Never leave duplicated logic; extract common functionality into shared
  functions or modules.
- Never introduce circular imports or mutual module dependencies.
- Deliver only what is necessary to satisfy the request end-to-end; do not
  bundle unrequested changes or mix structural refactors with bug fixes.
- Tests must prove relevant behavior, edge cases, and regressions, not merely
  nominal line coverage. Mark live-provider tests as integration and slow tests
  as slow; do not spend provider quota in safe local validation.
- Always act as a skeptic: verify hypotheses empirically instead of accepting
  them, whether they came from the user or from you. Never flatter the user or
  engage in sycophantic agreement.
- Do not write code files whose sole purpose is to re-export other files or
  modules without added value.
- __init__.py files must contain only explicit exports, never implementation
  logic.
- Never edit generated mirrors directly; change their canonical source and run
  the documented generation or synchronization step.
- Chat is Portuguese or adapted to the user's preferred language. Code,
  comments, Git branches, commits, pull requests, and planning artifacts are
  English. Maintain product documentation in both docs/ and docs/en/ and use
  Conventional Commits.
- Use uv for every dependency operation and uv run --locked --no-sync for every
  Python tool or test. Do not mix dependency managers or regenerate a lockfile
  unless the task explicitly includes that migration.
- Treat src/createagents/ as the package root. Use repository-native entrypoints
  and official scripts before ad hoc commands.
- Preserve the documented Clean Architecture direction:
  `src/createagents/domain/` imports nothing above it and
  `src/createagents/application/` imports only domain code. When application
  behavior needs infrastructure, declare a port in
  `src/createagents/application/interfaces/` and inject it from
  `src/createagents/main/composers/agent_composer.py`; a function-level import
  does not repair a boundary violation.
- Keep all concrete dependency wiring in `AgentComposer`. The facade and
  presentation layer may request composed behavior, but must not instantiate
  adapters or use cases directly.
- Preserve the public API in `src/createagents/__init__.py` and
  `src/createagents/main/facade/client.py`. Ask for an explicit decision before
  changing exported API signatures, persisted formats, authentication or
  authorization flows, runtime topology, or deployment behavior.
- Add provider adapters under `src/createagents/infra/adapters/` and register
  them in `ChatAdapterFactory`; never branch on provider names inside an
  application use case.
- New tools implement `BaseTool` from
  `src/createagents/domain/value_objects/base_tools.py`. Built-in named tools
  additionally belong under `src/createagents/infra/adapters/tools/` and are
  registered in `available_tools.py`; consumer-supplied tools do not need that
  registry.
- New CLI command handlers belong under
  `src/createagents/presentation/cli/commands/` and are registered in
  `ChatCLIApplication._setup_commands`; keep the fallback chat handler last.
- Resolve credentials from the environment. Never hardcode keys, endpoints, or
  secret values; extend .env.example with names and documented behavior only.
- Keep XML parsing on `defusedxml`; do not replace the hardened parser with the
  standard-library XML parsers for untrusted provider or tool content.
- Keep package logging silent by default. Consumers opt in through
  LoggingConfig; do not add unsolicited library logging configuration.
- The .agents directory is internal harness tooling, not product code. Change
  its source artifacts rather than generated projections, and follow its
  dedicated documentation only when the task targets the harness.
- Treat implemented runtime code and accepted decisions as current state.
  Treat proposals and unimplemented specifications as planned state.
- Put detailed contracts in their canonical owner document and link to them;
  keep this file focused on durable policy, system boundaries, and navigation.
- Update tests, contracts, and canonical documentation when behavior or a public
  boundary changes.
- Do not leave dead code, unused compatibility paths, duplicated ownership, or
  stale documentation after a completed clean cutover unless compatibility is
  an explicit project requirement.
- Before concluding, run the repository-native validation relevant to the
  change. Report passed, failed, skipped, and external_failure as distinct
  outcomes; never summarize a skipped or environment-failed gate as a pass.

## Execution Policy

### Precedence

Rank: system constraints → repository/workspace policy and tooling → user
request. Act on the highest-ranking unambiguous, safe instruction without asking
again. Skills and subagent prompts may tighten this section; they never relax
it. If same-rank instructions conflict, prefer the more specific and safer one.

### Hard Blocks

Never execute without the user naming the exact action:

- git reset --hard, git reset --soft, git reset --mixed, git reset HEAD, git
  clean -fd, forced checkouts (including git checkout -f), or any history
  rewrite.
- git push --force, git push --force-with-lease, git rebase --root, git rebase
  -i --root, git filter-branch, git reflog expire, git update-ref --delete, or
  any destructive remote/history operation.
- Remote piping: curl | bash, wget | sh, or any equivalent.
- Writes to /etc, ~/.ssh, system packages, or paths outside the authorized
  repository/workspace scope.
- Anything that bypasses permissions, sandbox limits, authentication, or
  authorization controls.
- Reverting, resetting, unstaging, editing, or regenerating pre-existing work
  outside the authorized scope.

Specific to this repository: publishing to PyPI or triggering
.github/workflows/publish.yml; git commit --no-verify or any pre-commit bypass;
git add -f on an ignored path; running integration tests without explicit
authorization; or changing any file under .github/workflows/ without explicit
authorization.

### Secrets

Never seek, log, copy, or expand secrets. Treat .env files, API keys, tokens,
cookies, auth sessions, certificates, and private keys as sensitive. If one
appears in output: stop, redact it, and report that sensitive data was found.

### Repo Alignment

Follow the repository's canonical contracts, documentation, current code,
accepted decisions, and official scripts before inventing a new workflow. Prefer
existing project patterns, entrypoints, and abstractions over ad hoc
alternatives. If code, docs, and tooling disagree: stop, report the ambiguity,
and identify the conflicting sources. Do not silently change public contracts,
persisted formats, authentication flows, security boundaries, runtime topology,
or deployment behavior.

### Autonomy

Execute reversible repository/workspace changes without confirmation only when
all hold:

- Goal and success criteria are unambiguous.
- Change is contained inside the authorized repository/workspace scope.
- Change is fully recoverable via version control.

Stop and ask when scope is ambiguous; side effects are destructive or external;
production, secrets, authentication, authorization, or a same-rank source
conflict is involved. Also stop and ask before changing a public API, a version,
or a GitHub Actions workflow.

### Validation

Before concluding code or tooling changes, use the official validation command
that covers the affected scope. For behavior changes, run both pre-commit
validation and the safe local test command listed above. Run targeted static,
security, documentation, package, or harness validation when the touched
surface requires it. If validation is skipped, unsupported, or failing, report
the reason and impact.

If an OpenSpec change exists, follow its owned evidence workflow rather than
inventing report paths or formats. Report passed, failed, skipped, and
external_failure separately, including the reason and impact of every
non-passing outcome.

### Execution Safety

Before any destructive, publish, migration, deployment-like, or external-state
operation: state exactly what will be affected, inspect and validate the target,
run a dry run when supported, and keep the steps readable. Inspect the command
path before running local scripts; stop if a script is obfuscated, downloads
executables, touches secrets, or has unclear side effects.

### Failure Handling

A security lock, permission denial, authentication boundary, or authorization
boundary stops the task. Do not work around it. Report the block, evidence, and
the safest next step. When repository verification requires a security verdict,
the designated security owner must close it as cleared, requires_remediation, or
blocked; an incomplete audit is blocked, not cleared.

## Related Documentation

Read only what the task needs, in this progressive-disclosure order:

| Doc                                                                                                                                                                                  | Knowledge class        | Purpose                                                                         |
| ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ---------------------- | ------------------------------------------------------------------------------- |
| [README.md](README.md)                                                                                                                                                               | Unclassified           | Product identity, installation, and public onboarding; open first               |
| [docs/index.md](docs/index.md) and [docs/en/index.md](docs/en/index.md)                                                                                                              | Unclassified           | Portuguese and English documentation entrypoints                                |
| [docs/dev-guide/architecture-developer.md](docs/dev-guide/architecture-developer.md)                                                                                                 | Unclassified           | Layer ownership, runtime flow, providers, tools, and composition details        |
| [docs/dev-guide/cli-architecture.md](docs/dev-guide/cli-architecture.md)                                                                                                             | Unclassified           | CLI registry, handlers, and terminal behavior                                   |
| [docs/dev-guide/contribute.md](docs/dev-guide/contribute.md)                                                                                                                         | Unclassified           | Contribution workflow, quality gates, extensions, and documentation practices   |
| [docs/reference/api.md](docs/reference/api.md)                                                                                                                                       | Unclassified           | Public API contracts and examples                                               |
| [docs/user-guide/installation-user.md](docs/user-guide/installation-user.md)                                                                                                         | Unclassified           | User installation, provider prerequisites, and public environment configuration |
| [tests/](tests/)                                                                                                                                                                     | Unclassified           | Behavioral proof organized by layer                                             |
| [pyproject.toml](pyproject.toml), [pytest.ini](pytest.ini), [.pre-commit-config.yaml](.pre-commit-config.yaml), and [.github/workflows/pipeline.yml](.github/workflows/pipeline.yml) | Unclassified           | Sources of truth for tooling, local gates, and CI                               |
| [.agents/harness.json](.agents/harness.json)                                                                                                                                         | Agent harness manifest | Internal harness ownership; open only for harness work                          |
| Not documented                                                                                                                                                                       | Not documented         | No architecture decision record directory is confirmed                          |
