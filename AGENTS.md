# AGENTS.md

> Owner: Jordan Estralioto (@jordanestralioto)
> Last reviewed: 2026-08-10
> Status: Confirmed
> Knowledge class: Agent policy

Operating policy for coding agents. Kept deliberately short: it loads in full on
every session, so it carries only what the code, `pyproject.toml`, CI and
`docs/` do not already state.

## System Overview

**Create Agents AI** (PyPI package `createagents`) is a Python library for
building conversational AI agents with pluggable providers (OpenAI, Ollama),
extensible tools, conversation history and metrics, plus an interactive terminal
CLI. Consumers import `CreateAgent`, `BaseTool` and `LoggingConfig` from
`createagents`. The repository owns the framework and its CLI, not the providers.

**The product is not the harness.** Two unrelated things are called "agent" here:

|         | What it is                                        | Where                       | Published    |
| ------- | ------------------------------------------------- | --------------------------- | ------------ |
| Product | the library consumers install                     | `src/`, `docs/`, `tests/`   | yes, to PyPI |
| Harness | tooling that assists whoever develops the product | `.agents/` + hidden mirrors | no           |

`.agents/`, `.claude/`, `.opencode/`, `opencode.json` and `.github/agents/` are
gitignored on purpose and never ship; `uv build` packages only `src/`.

## Success Metrics

| Metric           | Target                                                                                                    |
| ---------------- | --------------------------------------------------------------------------------------------------------- |
| Coverage gate    | 85% (`pytest.ini`, CI)                                                                                    |
| Python matrix    | >= 3.12                                                                                                   |
| Every other gate | whatever `.pre-commit-config.yaml` and `.github/workflows/` enforce — they are the source, not this table |

## Pipeline Architecture

A library plus a CLI, not a data pipeline. Dependencies point inward:
`presentation`/`infra` → `application` → `domain`.

`CreateAgent` (`main/facade/client.py`) → `AgentComposer` (`main/composers/`,
the only wiring point) → use cases (`application/use_cases/`) →
`ChatAdapterFactory` (`infra/factories/`) → provider adapter
(`infra/adapters/`). The terminal experience lives in `presentation/cli/`.

Design detail is owned by `docs/dev-guide/architecture-developer.md`, and
`docs/dev-guide/cli-architecture.md` for the terminal layer. Start there, not
here.

## Configuration & Runtime

| Surface                             | Location                  | Purpose                                                                                                                    |
| ----------------------------------- | ------------------------- | -------------------------------------------------------------------------------------------------------------------------- |
| Manifest, dependencies, tool config | `pyproject.toml`          | the authority on stack, versions and lint/type settings                                                                    |
| Lockfile                            | `uv.lock`                 | owned by `uv`; never hand-edited                                                                                           |
| Quality gates                       | `.pre-commit-config.yaml` | the 42 hooks: 39 on `pre-commit` and 2 on `pre-push` (both run by `ai:verify`), plus `validate-commit-msg` on `commit-msg` |
| Environment variable names          | `.env.example`            | names only; `OPENAI_API_KEY` for the openai provider, none for Ollama                                                      |
| Agent harness                       | `.agents/`                | internal and gitignored; `.agents/README.md` is its manual                                                                 |

### Commands

| Action                   | Command                                                                             |
| ------------------------ | ----------------------------------------------------------------------------------- |
| Install                  | `uv sync`                                                                           |
| All quality hooks        | `uv run pre-commit run --all-files`                                                 |
| Tests                    | `uv run pytest -m 'not integration and not slow' -ra`                               |
| Tests with coverage gate | `uv run pytest -m 'not integration and not slow' -ra --cov=src --cov-fail-under=85` |
| Docs, strict as in CI    | `uv run mkdocs build --strict`                                                      |
| Aggregated verification  | `uv run python .agents/scripts/harness_verify.py`                                   |
| Verify a harness change  | `uv run python .agents/scripts/harness_verify.py --changed-file <path>`             |
| Sync harness mirrors     | `harness-sync`                                                                      |

Run all Python tooling and tests directly through `uv run`.

## Technical Stack

Python `>=3.12,<4.0` managed by `uv`, setuptools src-layout build. Clean
Architecture + SOLID with no web framework. Ruff (79 columns, single quotes),
mypy, pydocstyle (Google), pytest with pytest-asyncio, bandit, pip-audit,
MkDocs Material. `pyproject.toml` is the authority on versions; this file does
not restate them.

## Mandatory Rules

- **Critical Stance.** Act as a rigorous skeptic. Do not accept hypotheses — whether
  proposed by the user or self-generated — without empirical proof. NEVER flatter
  or engage in sycophancy; prioritize technical rigor, root-cause evidence, and
  honest trade-offs.
- Verify files before editing; do not assume structure or behavior. A claim
  about current behavior needs a path you opened, not a recollection.
- Keep scope small and reviewable, and deliver one kind of work per change.
- Treat runtime code and accepted decisions as current state; treat proposals
  and unimplemented specs as planned state.
- Put detailed contracts in their canonical doc and link to them; do not
  re-inline a table that an owner document already holds.
- **Layering.** `domain/` imports nothing above it; `application/` imports
  **only** `domain/`, never `infra/` or `main/`. If an application component
  needs infrastructure, declare a port in `application/interfaces/` and let
  `AgentComposer` inject it. A function-level import hides a cycle instead of
  removing it.
- **Wiring.** All dependency wiring goes in `main/composers/agent_composer.py`.
  Never instantiate adapters or use cases from `presentation/` or the facade.
- **Extension points.** New provider → adapter under `infra/adapters/`,
  registered in `ChatAdapterFactory`. New tool → implement `BaseTool` from
  `createagents.domain`. New CLI command → `presentation/cli/commands/` plus
  `command_registry.py`. Never branch on provider names inside a use case.
- **Published API.** `src/createagents/__init__.py` and the public signatures of
  `main/facade/client.py` are released to PyPI. Do not change them without an
  explicit decision.
- **Module Structure & Exports.** Do not create code files whose sole purpose is to
  re-export other modules. `__init__.py` files must NEVER contain implementation
  logic; use them ONLY for package exports and public imports.
- **Language.** `Chat/Docs = Portuguese`, `Code/Comments/Git = English`. Commit
  messages follow Conventional Commits.
- **Tooling.** `uv` for every dependency operation, `uv run` for every tool.
  Never `pip install`, `poetry`, or a second lockfile.
- **Tests.** Mirror the layer you touched under `tests/`. Mark external-API
  tests `@pytest.mark.integration` and slow ones `@pytest.mark.slow`. A test
  that passes without proving the behavior is worse than no test.
- **Secrets.** Credentials resolve from the environment. Never hardcode keys or
  endpoints, never read or commit `.env` values, and extend `.env.example` with
  names only.
- **Security invariants.** Keep XML parsing on `defusedxml`. Keep the library
  silent by default — no handlers or `basicConfig` on the package logger;
  configure through `LoggingConfig`. Never weaken bandit or pip-audit to make a
  check pass.
- **Harness.** `.agents/` is gitignored by design; never `git add -f` it and
  never move harness content into `src/` or `docs/`. Skill routing lives in
  `.agents/README.md`, verification detail in `.agents/verification-harness.md`.
- **Evidence.** "Done" means terminal output or a gate result reported back.
  Report `passed`, `failed`, `skipped` and `external_failure` as four distinct
  outcomes; never summarize a skipped or environment-failed gate as a pass.

## Execution Policy

### Precedence

Rank: system constraints → repository policy and tooling → user request. Act on
the highest-ranking unambiguous, safe instruction without asking again. Skills
and subagent prompts may tighten this section; they never relax it.

### Hard Blocks

Never without the user naming the exact action: `git reset --hard`,
`git clean -fd`, `git push --force` or any history rewrite; remote piping
(`curl | bash`, `wget | sh`); writes to `/etc`, `~/.ssh` or outside the
repository; anything that bypasses permissions, sandbox limits or auth controls.

Specific to this repository: publishing to PyPI or triggering
`.github/workflows/publish.yml`; `git commit --no-verify` or any pre-commit
bypass; `git add -f` on a gitignored path; running `@pytest.mark.integration`
tests, which spend real provider quota.

### Secrets

Never seek, log, copy or expand secrets. Treat `.env`, api keys, tokens,
certificates and private keys as sensitive. If one appears in output: stop,
redact it, and report that sensitive data was found.

### Repo Alignment

Follow canonical contracts, current code and official scripts before inventing a
workflow. Do not silently change public contracts, persisted formats, auth flows
or security boundaries. If code, docs and tooling disagree: stop, report the
ambiguity, and name the conflicting sources.

### Autonomy

Execute reversible changes without confirmation only when the goal is
unambiguous, the change stays inside the repository, and it is fully
recoverable through version control.
Stop and ask on ambiguous scope, destructive side effects, external systems,
secrets, the published API, a `version` bump, or any `.github/workflows/` edit.

### Validation

Before concluding, use the official validation entrypoint:
`uv run pre-commit run --all-files`, then `uv run pytest -m 'not integration and not slow' -ra --cov=src --cov-fail-under=85` for behavior
changes. `uv run python .agents/scripts/harness_verify.py` is the aggregated agent-facing harness; state which
`effectiveProfile` ran. If validation is skipped or failing, report that with
the reason and impact.

### Execution Safety

Before anything destructive, publishing, migration-like or external-state:
state exactly what will be affected, inspect and validate the target, run a dry
run when supported, and keep the steps readable. Inspect the command path
before running local scripts; stop if a script is obfuscated, downloads
executables, or touches secrets.

### Failure Handling

A security lock, permission denial or authorization boundary stops the task. Do
not work around it — report the block, the evidence and the safest next step.
When verification returns `securityRequired=true`, the verdict belongs to
`security-engineer` and closes only as `cleared`, `requires_remediation` or
`blocked`; an audit that could not be completed is `blocked`, not `cleared`.

## Related Documentation

Open only what the task needs.

| Doc                                        | Knowledge class          | Purpose                                                                                                   |
| ------------------------------------------ | ------------------------ | --------------------------------------------------------------------------------------------------------- |
| `README.md`, `docs/`                       | Unclassified             | Product identity, usage and the full Portuguese corpus; `mkdocs.yml` is its index.                        |
| `docs/dev-guide/architecture-developer.md` | Unclassified             | Layer design. First stop for architecture; `cli-architecture.md` for the terminal layer.                  |
| `docs/dev-guide/contribute.md`             | Unclassified             | PR workflow, quality checklist, Conventional Commits, `develop` as target branch.                         |
| `.agents/README.md`                        | Agent framework manual   | Product-vs-harness scope, agent ownership, skill routing, mirrors and sync. Open second, after this file. |
| `.agents/verification-harness.md`          | Agent framework manual   | `ai:verify` profiles, path rules, escalations and gate statuses.                                          |
| `.agents/agents/*.agent.md`                | Agent prompt (canonical) | `developer-engineer` implements; `security-engineer` judges risk and never implements.                    |
| Architecture decision records              | Not documented           | No ADR directory exists in this repository.                                                               |
