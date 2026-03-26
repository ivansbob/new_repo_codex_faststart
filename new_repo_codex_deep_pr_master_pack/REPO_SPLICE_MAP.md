# Repo splice map

## Use as base
- `main_repo_skeleton_v0.5.39_pr6_execution_preflight_DONE.zip`

## Do NOT use as base
- `main_repo_skeleton_v0.5.39_pr5_1_sim_preflight_negative_DONE ... zip`
- Reason: PR6 supersedes PR5.

## Apply as overlay/spec layer
- `gmee_strategy_pack_v17_overlay_p0_v0_4_1_merged_v2_PATCHED_helpers.zip`
- Import docs, schemas, runbooks, manifests, query specs, UV mapping.

## Use as canonical strategy kernel
- `strategy (2).py`
- Mount as `repo/core_strategy/copy_scalp_strategy.py`

## Use as mature module source for selective import
- `1solana-coin-signal-engine-main (4).zip`
- Import only by phases:
  1. `src/replay`
  2. `trading`
  3. `src/promotion`
  4. `analytics`
  5. `collectors`
  6. `src/wallets`
  7. `scoring`
  8. `schemas`
  9. `scripts` and `tests`

## Keep separate as sidecar
- `zipwiz-soul-scan 2-context.txt`
- Use for voice/research/orchestration only, not inside execution core.