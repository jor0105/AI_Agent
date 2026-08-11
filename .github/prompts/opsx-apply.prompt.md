---
name: "OPSX: Apply"
description: Implement tasks from an OpenSpec change using Developer Engineer
category: Workflow
tags: [workflow, artifacts, experimental]
---

Implement tasks from an OpenSpec change using the **Developer Engineer** agent (`developer-engineer`).

**Agent**: Always activate the **Developer Engineer** agent (`developer-engineer`) as the primary executor before proceeding with any steps below.

**Input**: Optionally specify a change name (e.g., `/opsx:apply add-auth`). If omitted, `apply` is the only OPSX workflow allowed to infer from conversation context or auto-select when there is exactly one safe active candidate. If that is not true, you MUST prompt for available changes.

**Selection policy exception**: Unlike `continue`, `sync`, `archive` and `verify`, this workflow may infer or auto-select the change when it is safe to do so. Always announce the chosen change and how to override it.

**Schema note**: Use `openspec status --change "<name>" --json` and `openspec instructions apply --change "<name>" --json` as the source of truth for schema, context files and task state. Do not assume `spec-driven` unless the CLI output indicates it.

**Steps**

1. **Activate Developer Engineer Agent**

   Invoke and adopt the identity and rules of the **Developer Engineer** agent (`developer-engineer`). All code modifications, verifications, and task updates in this workflow MUST be executed under this agent's identity and governance.

2. **Select the change (exception policy)**

   If a name is provided, use it. Otherwise:
   - Infer from conversation context if the user mentioned a change
   - Auto-select if only one active change exists
   - If ambiguous, run `openspec list --json` to get available changes and use the **AskUserQuestion tool** to let the user select

   Always announce: "Using change: <name>" and how to override (e.g., `/opsx:apply <other>`).

2. **Check status to understand the schema**

   ```bash
   openspec status --change "<name>" --json
   ```

   Parse the JSON to understand:
   - `schemaName`: The workflow being used (e.g., "spec-driven")
   - Which artifact contains the tasks (typically "tasks" for spec-driven, check status for others)

3. **Get apply instructions**

   ```bash
   openspec instructions apply --change "<name>" --json
   ```

   *(CLI Fallback: If `openspec` CLI fails or is unavailable, read the artifact files directly from `openspec/changes/<name>/`)*

   This returns:
   - Context file paths (varies by schema)
   - Progress (total, complete, remaining)
   - Task list with status
   - Dynamic instruction based on current state

   **Handle states:**
   - If `state: "blocked"` (missing artifacts): show message, suggest using `/opsx:continue`
   - If `state: "all_done"`: congratulate, suggest archive
   - Otherwise: proceed to implementation

4. **Read context files**

   Read the files listed in `contextFiles` from the apply instructions output.
   The files depend on the schema being used:
   - **spec-driven**: proposal, specs, design, tasks
   - Other schemas: follow the contextFiles from CLI output

5. **Show current progress**

   Display:
   - Schema being used
   - Progress: "N/M tasks complete"
   - Remaining tasks overview
   - Dynamic instruction from CLI

6. **Implement tasks (loop until done or blocked)**

   For each pending task:
   - Show which task is being worked on
   - Make the code changes required
   - Keep changes minimal and focused
   - **Execute project tests/validation** (e.g. project test suite, linters) relevant to the changes to ensure no regressions
   - Mark task complete in the tasks file: `- [ ]` → `- [x]` **only AFTER verification passes**
   - Continue to next task

   **Pause if:**
   - Task is unclear → ask for clarification
   - Implementation reveals a design issue → suggest updating artifacts
   - Error or blocker encountered → report and wait for guidance
   - User interrupts

7. **On completion or pause, show status**

   Display:
   - Tasks completed this session
   - Overall progress: "N/M tasks complete"
   - If all done: suggest archive
   - If paused: explain why and wait for guidance

**Output During Implementation**

```
## Implementing: <change-name> (schema: <schema-name>)

Working on task 3/7: <task description>
[...implementation happening...]
✓ Task complete

Working on task 4/7: <task description>
[...implementation happening...]
✓ Task complete
```

**Output On Completion**

```
## Implementation Complete

**Change:** <change-name>
**Schema:** <schema-name>
**Progress:** 7/7 tasks complete ✓

### Completed This Session
- [x] Task 1
- [x] Task 2
...

All tasks complete! You can archive this change with `/opsx:archive`.
```

**Output On Pause (Issue Encountered)**

```
## Implementation Paused

**Change:** <change-name>
**Schema:** <schema-name>
**Progress:** 4/7 tasks complete

### Issue Encountered
<description of the issue>

**Options:**
1. <option 1>
2. <option 2>
3. Other approach

What would you like to do?
```

**Guardrails**

- Keep going through tasks until done or blocked
- Always read context files before starting (from the apply instructions output or directory fallback)
- If task is ambiguous, pause and ask before implementing
- If implementation reveals issues, pause and suggest artifact updates
- Keep code changes minimal and scoped to each task
- **Validate task changes using the project's native test/build command before checking the task off**
- Update task checkbox immediately after completing and validating each task
- Pause on errors, blockers, or unclear requirements - don't guess
- Use contextFiles from CLI output, don't assume specific file names

**Fluid Workflow Integration**

This skill supports the "actions on a change" model:

- **Can be invoked anytime**: Before all artifacts are done (if tasks exist), after partial implementation, interleaved with other actions
- **Allows artifact updates**: If implementation reveals design issues, suggest updating artifacts - not phase-locked, work fluidly
