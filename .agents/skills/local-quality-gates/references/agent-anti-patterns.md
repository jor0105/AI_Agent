# AI Coding Agent Anti-Patterns and Diff Sanity Guide

> Summary: Comprehensive reference of common mistakes, shortcuts, and erosion patterns introduced by AI coding agents during refactoring or feature implementation, and how to intercept them locally.

## 1. Catalog of AI Coding Agent Traps

### 1.1 Leftover Debug and Inspection Artifacts

AI agents frequently insert statements to inspect runtime states and forget to remove them:

- **Python**: `breakpoint()`, `import pdb; pdb.set_trace()`, raw `print()` statements in library/core code.
- **JavaScript/TypeScript**: `debugger;`, `console.log(`, `console.dir(`.
- **Rust**: `dbg!(...)`, `println!(...)` in production crates.
- **Go**: `fmt.Println` in internal services without logger.

### 1.2 Unfulfilled Stubs and Placeholders

When generating broad scaffolds or completing functions hurriedly, agents may leave placeholder implementations:

- `raise NotImplementedError("TODO")`
- `throw new Error("TODO: implement")`
- `pass  # TODO` as sole body of new public functions.
- `return null; // FIXME`

### 1.3 Erosion of Type Safety and Lint Disables

To pass validation gates without fixing underlying contract issues, agents often silence compilers:

- `@ts-ignore`, `@ts-nocheck` or `@ts-expect-error` in executable TypeScript or configuration.
- `# type: ignore` or `# noqa` in executable Python or configuration. The diff
  gate rejects these markers, including rule-specific forms and lines with a
  reason. A `.md`, `.markdown`, `.rst` or `.txt` file may quote them as
  explanatory documentation, including inside a fenced code block; that
  exception does not apply to any executable or configuration format.
- `as any` casting without explanation.
- `// eslint-disable-next-line` without a stated reason.

### 1.4 Test Integrity Violations

When a test fails following an implementation change, agents sometimes weaken or skip the test instead of fixing the implementation:

- Inserting `.only` (e.g. `it.only(`, `describe.only(`) to run only one test and bypass failures elsewhere.
- Adding `@pytest.mark.skip`, `@pytest.mark.xfail`, `it.skip()`, `xit()`.
- Removing assertions (`assert`, `expect(...)`) or replacing specific assertions with tautologies (`expect(true).toBe(true)`).

### 1.5 Unsynchronized Dependency Changes

- Adding a dependency to `package.json` or `pyproject.toml` without running the package manager lock command.
- Committing phantom packages not reflected in lockfiles.

### 1.6 Operational bypasses in every textual diff

The operational scan is independent of the code classifier and applies to
every textual file, including documentation, OpenSpec Markdown, generated
projections, scripts and configuration. It blocks download-to-shell
pipelines, hook-disabling command flags, hook-skip environment assignments,
CI settings that continue after an error, and shell fallbacks that force a
successful exit. A documentation citation never authorizes one of these
operations.

## 2. Detection Strategy in Diff

Quality gates must analyze lines starting with `+` in `git diff --cached`:

1. **New violations must trigger `FAIL`**: A newly introduced `console.log` on a staged line is a hard block.
2. **Intentional exceptions require the narrowest safe scope**:
   - If a third-party type boundary needs explanation, describe it in the
     surrounding documentation or fix the contract at the source; do not add a
     type-check suppression to executable code.
   - `# noqa`, `# noqa: <rule>`, type-ignore markers, and TypeScript suppression
     markers are violations in executable/configuration formats regardless of
     the reason attached. Documentation may quote them only as non-executable
     examples.
