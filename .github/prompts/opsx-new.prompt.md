---
name: "OPSX: New"
description: Start a new change using the experimental artifact workflow (OPSX)
category: Workflow
tags: [workflow, artifacts, experimental]
---

Start a new change using the experimental artifact-driven approach.

**Input**: The argument after `/opsx:new` is the change name (kebab-case), OR a description of what the user wants to build.

**Schema policy**: Use the default schema unless the user explicitly requests a different workflow or schema.

**Stop condition**: Stop after creating the change, showing the current artifact status, and printing the instructions for the first artifact `ready`.

**Steps**

1. **If no input provided, ask what they want to build**

   Use the **AskUserQuestion tool** (open-ended, no preset options) to ask:

   > "What change do you want to work on? Describe what you want to build or fix."

   From their description, derive a kebab-case name (e.g., "add user authentication" → `add-user-auth`).

   **IMPORTANT**: Do NOT proceed without understanding what the user wants to build.

2. **Determine the workflow schema**

   Use the default schema (omit `--schema`) unless the user explicitly requests a different workflow.

   **Use a different schema only if the user mentions:**
   - A specific schema name → use `--schema <name>`
   - "show workflows" or "what workflows" → run `openspec schemas --json` and let them choose

3. **Preflight Spec Consistency Check**

   Before scaffolding the new change, inspect existing changes to ensure main specs (`openspec/specs/`) are up to date:

   a. Run `openspec list --json` (or inspect active changes under `openspec/changes/`).
   b. Identify active changes containing delta specs at `specs/<capability>/spec.md`.
   c. **Check for un-synced completed changes**: If any active change has all tasks completed (`- [x]`) or status `all_done`, but its delta specs have not been merged into `openspec/specs/`:
      - Display warning `[WARNING]`: *"Change `<name>` appears completed but its delta specs are not synced to main specs (`openspec/specs/`). Recommended: run `/opsx:sync <name>` and `/opsx:archive <name>` before designing the new change."*
      - Ask the user via **AskUserQuestion tool** whether to sync first or proceed anyway.
   d. **Check for active concurrent changes**: If active changes modify related specs, display an informational note `[INFO]`: *"Active changes with delta specs in progress: `<list>`. Be aware of potential spec overlap."*

4. **Create the change directory**

   ```bash
   openspec new change "<name>"
   ```

   Add `--schema <name>` only if the user requested a specific workflow.
   This creates a scaffolded change at `openspec/changes/<name>/` with the selected schema.

   *(CLI Fallback: If `openspec` CLI fails or is missing, manually create the directory `openspec/changes/<name>/` and scaffold basic empty markdown files like `proposal.md`)*

5. **Show the artifact status**

   ```bash
   openspec status --change "<name>"
   ```

   This shows which artifacts need to be created and which are ready (dependencies satisfied).

   *(CLI Fallback: If `openspec` CLI fails, simply list the empty files that need to be filled in order)*

6. **Get instructions for the first artifact**
   The first artifact depends on the schema. Check the status output to find the first artifact with status "ready".

   ```bash
   openspec instructions <first-artifact-id> --change "<name>"
   ```

   This outputs the template and context for creating the first artifact.

   *(CLI Fallback: If `openspec` CLI fails, use standard markdown structure for the first artifact, e.g., a simple proposal outline)*

7. **STOP and wait for user direction**

**Output**

After completing the steps, summarize:

- Change name and location
- Schema/workflow being used and its artifact sequence
- Current status (0/N artifacts complete)
- The template for the first artifact
- Prompt: "Ready to create the first artifact? Run `/opsx:continue` or just describe what this change is about and I'll draft it."

**Guardrails**

- Do NOT create any artifacts yet - just show the instructions
- Do NOT advance beyond showing the first artifact template
- If the name is invalid (not kebab-case), ask for a valid name
- If a change with that name already exists, suggest using `/opsx:continue` instead
- Pass --schema if using a non-default workflow
