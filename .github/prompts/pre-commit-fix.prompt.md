---
description: Run pre-commit on all files and fix the errors using Developer Engineer.
---

# 🛠️ Pre-commit Fix Workflow (`/pre-commit-fix`)

Acione o agente **Developer Engineer** e solicite que ele execute o seguinte workflow para corrigir todos os problemas de pre-commit no repositório.

## Instructions

1. **Run the Pre-commit Suite**
   Execute the pre-commit checks across all files in the repository to identify issues.
   // turbo
   ```bash
   pre-commit run --all-files
   ```

2. **Analyze and Fix Errors**
   - Review the output of the pre-commit run carefully.
   - Fix all reported errors systematically using the appropriate tools.
   - **NO HACKS:** You must implement proper, robust solutions. Do not use bypasses like `// @ts-ignore`, `eslint-disable`, `# noqa`, or `fmt: skip` unless strictly unavoidable and architecturally justified.

3. **Follow System Rules and Principles**
   - Ensure all fixes strictly adhere to the best programming principles (Clean Code, SOLID, proper typing).
   - You MUST follow all system constraints, project structures, and guidelines defined in `AGENTS.md`.
   - Maintain the functional integrity and performance of the existing codebase.

4. **Verify the Fixes**
   - Once the fixes are applied, re-run `pre-commit run --all-files` to guarantee that the codebase is completely clean.
   - If there are still errors, iterate on steps 2-4 until all checks pass successfully.

5. **Final Status**
   - Provide a concise summary of the files changed and the nature of the fixes applied.
