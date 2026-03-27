# New Repo Codex Faststart Pack

This pack is the fastest clean-room starting point for a new repo.

Base layers included:
- `repo/` = PR6 baseline skeleton (use as initial import)
- `canon/` = strategy overlay docs/spec/contracts to apply on top
- `repo/core_strategy/copy_scalp_strategy.py` = canonical one-formula strategy
- `control_plane/zipwiz/ZIPWIZ_CONTEXT.md` = sidecar voice/research control-plane context
- `MAIN_REPO_MODULE_INVENTORY.json` = module inventory from the large main engine to splice in phase by phase

Recommended splice order:
1. Start from `repo/`
2. Import `canon/` as docs/spec/contracts layer
3. Wire `repo/core_strategy/copy_scalp_strategy.py` as canonical decision kernel
4. Import selected modules from large main repo by PR sequence, not all at once
5. Keep ZipWiz as a separate sidecar service

This pack is for Codex handoff and iterative refinement.