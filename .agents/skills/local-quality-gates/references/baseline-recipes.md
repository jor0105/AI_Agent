# Baseline Strategies for Legacy Projects

> Summary: Techniques for establishing non-growing baseline debt files in legacy codebases so that AI agents are not blocked by pre-existing errors, while preventing any new regression.

## 1. The Baseline / Ratchet Principle

In legacy repositories, full repository validation may yield hundreds of existing lint or type errors. Forcing an AI agent to fix all historical debt in a single localized task leads to scope explosion and broken features.

The baseline strategy enforces two complementary rules:

1. **Historical debt is frozen**: Existing recorded violations do not fail the gate.
2. **Zero new regressions**: Any newly introduced violation or increase in error counts triggers an immediate `FAIL`.

## 2. Tool-Specific Baseline Recipes

### 2.1 Mypy / Python Typing Baseline

- Option A (Error count caps): Store maximum allowed error count per module in a configuration file (e.g. `.mypy-baseline.json`).
- Option B (Mypy baseline plugin): Use `mypy-baseline` to record error signatures.

### 2.2 ESLint Baseline

- Use `.eslint-baseline.json` or run ESLint only against staged files:
  ```bash
  pnpm eslint --fix $(git diff --staged --name-only --diff-filter=d | grep -E '\.(js|jsx|ts|tsx)$')
  ```

### 2.3 Gitleaks / Secret Scanning Baseline

- Generate `.gitleaksignore` with fingerprints of known false positives:
  ```bash
  gitleaks detect --report-path /tmp/gitleaks-report.json
  # Whitelist confirmed false positives into .gitleaksignore
  ```

### 2.4 File Size / Max Lines Baseline

- Record existing oversized files in `.max-lines-baseline.json` with their exact line limits. Any increase in line count beyond the recorded limit fails the gate.

## 3. Ratchet Workflow

1. When cleaning up a file, update the baseline to reflect the reduced error count or line count.
2. The gate must disallow manual inflation of the baseline.
