# PR Bootstrap Checklist

## PR-00: INIT-REPO-PR6-BASELINE

### Goal
Initialize repository from PR6 skeleton and lock baseline integrity.

### Inputs expected
- `main_repo_skeleton_v0.5.39_pr6_execution_preflight_DONE.zip`
- Optional strict template from user for PR-00.

### Deliverables
- Imported `repo/` tree from PR6 skeleton.
- Baseline `PR_NOTES.md`.
- Deterministic changed-file report (`CHANGED_FILES.md`).
- Reproducible test command list (`TEST_COMMANDS.md`).
- Suggested next step (`NEXT_PR_SUGGESTION.md`) targeting PR-01.

### Definition of done
- Clean git diff scoped to PR-00 baseline import.
- Basic repo health checks pass (where available).
- Handoff files present and consistent.
# PR Bootstrap Checklist

## PR-00: INIT-REPO-PR6-BASELINE

### Goal
Initialize repository from PR6 skeleton and lock baseline integrity.

### Inputs expected
- `main_repo_skeleton_v0.5.39_pr6_execution_preflight_DONE.zip`
- Optional strict template from user for PR-00.

### Deliverables
- Imported `repo/` tree from PR6 skeleton.
- Baseline `PR_NOTES.md`.
- Deterministic changed-file report (`CHANGED_FILES.md`).
- Reproducible test command list (`TEST_COMMANDS.md`).
- Suggested next step (`NEXT_PR_SUGGESTION.md`) targeting PR-01.

### Definition of done
- Clean git diff scoped to PR-00 baseline import.
- Basic repo health checks pass (where available).
- Handoff files present and consistent.

## PR-001: SECURITY-FIRST-GATES

### Goal
Establish mandatory CI security gates before any functional imports.

### Deliverables
- `.github/workflows/pr001-security-gates.yml`
- `scripts/security/pr001_guard.sh`
- `SECURITY_BASELINE_PR001.md`

### Definition of done
- Guard script is syntax-valid and runnable locally.
- CI workflow invokes the guard script on push and pull request.
- No unresolved merge-conflict markers (`<<<<<<<`, `=======`, `>>>>>>>`) in tracked files.