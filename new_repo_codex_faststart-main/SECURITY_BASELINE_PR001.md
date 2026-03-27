# PR-001 Security Baseline

This repository starts with security-first guardrails on the first integration PR.

## Controls enabled
1. **Private key detection**
   - CI fails if key headers like `BEGIN RSA PRIVATE KEY` are found.
2. **Hardcoded credential pattern detection**
   - CI fails on common direct assignments of key/secret/token/password values.
3. **Oversized file gate**
   - CI fails if any non-git file exceeds 5 MiB.
4. **Handoff docs continuity**
   - CI requires `HANDOFF_INTAKE.md` and `PR_BOOTSTRAP_CHECKLIST.md`.

## CI entrypoint
- Workflow: `.github/workflows/pr001-security-gates.yml`
- Script: `scripts/security/pr001_guard.sh`

## Intent
This is a bootstrap security floor for `PR-001` and can be extended in later PRs with:
- signed artifact verification
- dependency scanning
- SAST and policy-as-code
