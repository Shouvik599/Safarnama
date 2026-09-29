## Batch Configuration

```text
BATCH_NUMBER: [N]
STITCH_PROJECT: Safarnama
PREVIOUS_BATCH: Batch [N-1]
NEXT_BATCH: Batch [N+1]

CURRENT_BATCH_SCREENS:
[Paste the finalized screen list for this batch]
```

## Task

We are implementing Batch [N] of the Safarnama frontend.

This is a **planning and inspection task only**.

**Do NOT modify any application code.**

## Repository

The repository contains:

- `frontend/` — frontend application
- `src/` — backend/AI/graph application
- `data/` — fixtures and static data
- `project_docs/` — project documentation
- `tests/` — automated tests
- `scripts/` — project scripts

Focus primarily on `frontend/`, `project_docs/`, and relevant `data/`. Inspect `src/` or `tests/` only when required to understand an existing integration relevant to this batch.

## Planning Task

First inspect the relevant project documentation under `project_docs/` and the existing implementation of the previous batch.

Then inspect the existing Stitch project **Safarnama** using Stitch MCP. Inspect only designs relevant to the current batch.

Determine:

1. How the previous batch currently works.
2. How this batch connects to the previous batch.
3. Existing routes.
4. Existing state/context/models.
5. State this batch consumes and creates.
6. Existing reusable components.
7. New components required.
8. Functionality required for each screen.
9. Validation requirements.
10. Data/backend/mock/service boundaries.
11. Routes required.
12. Forward and backward navigation.
13. Responsive behavior.
14. Accessibility requirements.
15. Verification strategy.
16. What the next batch will need from this batch.

### Important Constraints

- Do not invent APIs or backend capabilities.
- Do not invent credentials, providers, or live data.
- Reuse existing architecture and patterns where possible.
- Do not implement the next batch.
- Do not modify source code.
- Do not redesign existing screens unless required for integration.
- Treat the current repository and project documentation as the source of truth for existing behavior.
- Treat the relevant Stitch designs as the visual source of truth for the current batch.

## Output

Create:

```text
project_docs/01-planning/frontend_batch_plans/batch-[N]-plan.md
```

The plan must contain:

- Batch summary
- Screen-by-screen implementation plan
- Routes
- State/data flow
- Components to reuse
- Components to create
- Backend/data/service dependencies
- Validation
- Navigation
- Previous-batch integration
- State/data required by the next batch
- Responsive behavior
- Accessibility
- Verification plan
- Risks and unknowns

Keep the plan concise but sufficiently detailed for another AI coding agent to implement without needing the planning conversation.

After creating the plan:

1. Report what you inspected.
2. Report the generated plan path.
3. Mention important risks or unresolved questions.
4. Stop.

Do not implement anything.
