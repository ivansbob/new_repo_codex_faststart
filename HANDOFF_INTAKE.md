# Handoff Intake (Round 0)

## Source package status
- Expected archive: `new_repo_codex_faststart_pack.zip`.
- In this runtime, the archive was **not found on disk**, so extraction was not performed yet.

## Confirmed splice strategy
1. PR6 skeleton as base.
2. Overlay docs/contracts.
3. Canonical strategy kernel (`strategy (2).py` + `repo/core_strategy/copy_scalp_strategy.py`).
4. Phased imports from mature engine:
   - `src/replay`
   - `trading`
   - `src/promotion`
   - `analytics`
   - `collectors`
   - `src/wallets`
   - `scoring`
   - `schemas`
   - `scripts/tests`
5. ZipWiz sidecar stays outside execution core.

## PR conveyor (fastest route)
- Adopt user-provided sequence `PR-00`..`PR-28` unchanged.
- Execution mode:
  - one zip in
  - one PR layer out
  - one output artifact zip (`new-repo_prXX_<slug>.zip`)

## Required handoff payload per PR zip
Every produced handoff zip must contain:
- `repo/`
- `PR_NOTES.md`
- `CHANGED_FILES.md`
- `TEST_COMMANDS.md`
- `NEXT_PR_SUGGESTION.md`

## Next action for following turn
Request strict per-PR contract (title -> goal -> exact files -> DoD -> tests -> codex prompt) to begin `PR-00 INIT-REPO-PR6-BASELINE`.
