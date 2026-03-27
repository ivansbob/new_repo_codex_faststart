# PR-003 — MOUNT-CANONICAL-STRATEGY-KERNEL

## Goal
Mount `strategy (2).py` into the repository as the canonical strategy kernel without refactoring unrelated files.

## Why PR-003 is next
- PR-001 established security gates.
- PR-002 imported the canonical docs/contracts/spec layer.
- PR-003 now mounts the actual one-formula strategy kernel so later runtime and paper layers have a single decision core.

## Source of truth
Use the uploaded file `strategy (2).py` as the source strategy kernel.
Do not redesign the formula. Preserve intent and naming as much as practical.

## Expected repository changes
Create these files/directories if missing:
- `repo/core_strategy/__init__.py`
- `repo/core_strategy/copy_scalp_strategy.py`
- `repo/docs/strategy_kernel_mount.md`
- `repo/tests/test_strategy_kernel_import.py`
- `repo/tests/test_strategy_kernel_smoke.py`

## Required implementation
1. Copy the logic from `strategy (2).py` into `repo/core_strategy/copy_scalp_strategy.py`.
2. Preserve these canonical types/classes where present in the source file:
   - `WalletProfile`
   - `TokenSnapshot`
   - `PolymarketSnapshot`
   - `WalletBuyEvent`
   - `PortfolioState`
   - `Signal`
   - `FeatureBuilder`
   - `CalibratedModel`
   - `StrategyParams`
   - `CopyScalpStrategy`
3. Keep the kernel independent from external live APIs.
4. Add a short mount doc describing:
   - where the kernel came from
   - that it is the canonical decision core
   - that later PRs should call into it instead of duplicating the formula
5. Add smoke tests that only verify importability/basic construction and one simple decision-path sanity check using fixtures or minimal stubs.

## Constraints
- Do not start PR-004.
- Do not add live trading.
- Do not redesign the repo layout beyond the files listed above.
- Do not rewrite the strategy into a different architecture.
- Keep changes deterministic and minimal.

## Definition of done
- `repo/core_strategy/copy_scalp_strategy.py` exists and is importable.
- Canonical classes are present or faithfully represented.
- Minimal tests pass.
- Mount doc exists.
- Output zip contains handoff notes.

## Required output zip contents
- `repo/`
- `PR_NOTES.md`
- `CHANGED_FILES.md`
- `TEST_COMMANDS.md`
- `NEXT_PR_SUGGESTION.md`
