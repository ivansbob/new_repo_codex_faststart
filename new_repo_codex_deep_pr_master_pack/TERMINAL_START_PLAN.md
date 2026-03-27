# Terminal plan to start the new repo

```bash
mkdir new-repo
cd new-repo
unzip ../main_repo_skeleton_v0.5.39_pr6_execution_preflight_DONE.zip
# import overlay docs manually into canon/
# copy strategy file into repo/core_strategy/copy_scalp_strategy.py
# keep zipwiz outside execution core, under control_plane/zipwiz/
```

Then commit in this order:
1. PR-00 baseline import
2. PR-01 canon lock and CI
3. PR-02 overlay docs/contracts
4. PR-03 strategy kernel mount

After each PR, build a new zip for Codex.