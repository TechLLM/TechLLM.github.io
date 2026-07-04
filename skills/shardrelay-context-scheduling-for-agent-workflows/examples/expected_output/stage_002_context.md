# Context Pack: stage_002 - Emit review handoff

Task: Create deterministic manifest output and handoff context for the next agent.
Depends on: stage_001
Budget: 230 estimated tokens

## Scheduled Memory Shards

### handoff_log - Handoff log
Source: log; priority: 4; created_at: 2026-01-03
Tags: manifest, handoff, deterministic
Included because: matches: agent, deterministic, handoff, manifest, output, review; high priority: 4; recent shard

Prior agent output defined manifest fields for selected shards, estimated tokens, inclusion reasons, output files, and deterministic review handoff.

### project_brief - Project brief
Source: brief; priority: 5; created_at: 2026-01-01
Tags: shardrelay, context, workflow
Included because: matches: context; dependency continuity; high priority: 5; source type: brief; recent shard

ShardRelay builds context bundles from memory shards for each workflow stage. It preserves dependency handoffs and token budgets.
