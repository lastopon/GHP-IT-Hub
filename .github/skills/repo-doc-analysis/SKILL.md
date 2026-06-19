---
name: repo-doc-analysis
description: "Use when: you need to inspect a documentation-first repository, identify the main source of truth, understand conventions, and decide what chat customization files should be created or updated."
---

# Repo Documentation Analysis

## When to use this skill
Use this skill for repositories that are mostly documentation, design notes, or architecture plans, especially when the agent needs to understand what is real versus what is still assumed.

## Workflow
1. **Inventory the repo**
   - Check the root folder, hidden config files, and important documentation files.
   - Look for files such as README, AGENTS.md, copilot instructions, architecture docs, and docs folders.

2. **Find the source of truth**
   - Identify the primary document that explains the project structure, goals, and decisions.
   - Prefer linking to that document instead of repeating its contents.

3. **Confirm what exists**
   - Look for build commands, tests, framework hints, or deployment setup.
   - If the repo does not show these yet, say so explicitly rather than guessing.

4. **Understand conventions**
   - Note language/style patterns, module boundaries, and how documentation is organized.
   - Capture any project-specific rules that agents should follow.

5. **Decide what customization files to update**
   - Create or update agent instructions when the repo needs always-on guidance.
   - Use a skill when the task is a reusable workflow for exploration or documentation review.

## Quality criteria
- Keep guidance concise and actionable.
- Do not invent missing runtime behavior, stack choices, or commands.
- Prefer documentation links over copied text.
- Make instructions easy to trace back to the repo's actual docs.

## Output expectations
- A short summary of the repository's current state.
- The main documentation source(s) that should guide future work.
- Recommended customization files to create or update.
- Any assumptions that should be avoided.
