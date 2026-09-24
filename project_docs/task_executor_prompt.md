Start **Task X — [TASK NAME]**.

Review the relevant requirements in `phases.md`, `rules.md`, `architecture.md`, and `memory.md`, then inspect the existing implementation before making changes.

Also consider **all decisions and requirements we have agreed on in this conversation**, including anything that has not yet been reflected in the project documentation.

Implement **only Task X**. Reuse existing work, avoid unnecessary changes, and do not proceed to later tasks.

### Documentation Sync

If our discussion introduced or changed any project decisions, update the relevant documentation so it stays consistent with the latest agreed state:

* `prd.md`
* `phases.md`
* `architecture.md`
* `rules.md` — if applicable
* `design.md` — if applicable
* `README.md`

Do not invent new requirements or rewrite documentation unnecessarily. Only update documentation affected by decisions actually made.

### Verification

After implementation:

* Run relevant tests/checks and fix failures.
* Verify the actual behavior.
* Review the final changes for consistency with the project documentation.
* Update `memory.md` with the new project state, including important decisions and documentation updates.

Report:

* What changed
* Documentation updated
* What was verified
* Tests/checks run
* Known issues
* Next recommended task

**Stop after Task X is complete.**
