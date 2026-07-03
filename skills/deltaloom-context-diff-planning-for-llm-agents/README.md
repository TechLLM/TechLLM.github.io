# DeltaLoom Context Diff Planning Skill

Minimal installable skill for generating context-diff plans for LLM and agent workflows.

## Install

From this folder:

```bash
mkdir -p "$HOME/.claude/skills/deltaloom-context-diff-planning-for-llm-agents"
cp -R SKILL.md README.md scripts examples "$HOME/.claude/skills/deltaloom-context-diff-planning-for-llm-agents/"
```

## Run

Use the built-in sample:

```bash
python scripts/run.py
```

Compare the included examples:

```bash
python scripts/run.py --previous examples/context_previous.md --current examples/context_current.md --format summary
```

Save a JSON plan:

```bash
python scripts/run.py --previous examples/context_previous.md --current examples/context_current.md --output examples/plan.json
```

## Output

The CLI prints or writes a JSON object with:

- `current_snapshot`: chunked current context with fingerprints.
- `changed_block_manifest`: block-level reuse, refresh, add, delete, split, and merge decisions.
- `summary_tasks`: downstream tasks for selective summary updates.
- `dependency_hints`: invalidations from explicit `[block:block-id]` references.
- `json_patch`: deterministic JSON Patch operations to update the stored snapshot.

No third-party Python packages are required.
