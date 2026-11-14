# Planning Artifacts

Which planning artifact governs what. Four artifacts exist; only two are versioned.

## Hierarchy

1. **Constitution** (`.specify/memory/constitution.md`) — the law. Principles, contracts,
   and quality gates. Versioned.
2. **Feature specs** (`specs/<feature>/`) — one directory per feature: `spec.md`,
   `plan.md`, `research.md`, `data-model.md`, `contracts/`, `quickstart.md`, `tasks.md`.
   Versioned.
3. **Tickets** (`.scratch/<feature>/issues/`) — a local, disposable view of the work
   frontier, with blocking edges that cross feature boundaries. Not versioned; regenerable.
4. **Workflow pack** (`.ub-workflows/`) — local sprint state, vision, options, and the
   current pointer. Not versioned.

## Source of truth

**`tasks.md` is the source of truth for execution.** It carries the phases, task ids, file
paths, and "Done when" conditions, and it is the artifact the constitution refers to when it
requires a commit per completed task.

Tickets do not override it. They exist to answer two questions the per-feature task lists
cannot: what is ready now across all features, and which feature gates which. When a ticket
and a task disagree, the task wins and the ticket is regenerated.

The sprint pack is a working view over the same work; it never contains a task that no
`tasks.md` defines.

## Regeneration

- Adding or changing a task: edit the feature's `tasks.md`, then regenerate its tickets.
- Changing scope or behaviour: edit `spec.md` first, then `plan.md`, then `tasks.md`.
- The constitution outranks everything here; a conflict means an amendment, not a local fix.

## Why tickets are not versioned

They duplicate `tasks.md` at a different granularity and are useful for a single session's
frontier. Versioning them would create a second source of truth that drifts silently. The
edges they carry — which feature blocks which — are cheap to rebuild from the plans.
