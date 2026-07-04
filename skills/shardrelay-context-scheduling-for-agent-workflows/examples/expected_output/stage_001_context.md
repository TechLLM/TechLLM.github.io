# Context Pack: stage_001 - Plan shard index

Task: Plan a workflow DAG parser and memory shard index for context scheduling.
Depends on: none
Budget: 230 estimated tokens

## Scheduled Memory Shards

### project_brief - Project brief
Source: brief; priority: 5; created_at: 2026-01-01
Tags: shardrelay, context, workflow
Included because: explicitly required; matches: context, memory, workflow; high priority: 5; source type: brief; recent shard

ShardRelay builds context bundles from memory shards for each workflow stage. It preserves dependency handoffs and token budgets.

### dag_notes - DAG notes
Source: note; priority: 4; created_at: 2026-01-02
Tags: dag, workflow, json
Included because: matches: dag, workflow; high priority: 4; recent shard

Workflow input is a DAG. Each stage has an id, task, dependencies, budget, priority terms, and required shards.
