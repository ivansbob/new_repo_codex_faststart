# Codex handoff protocol

## Goal
Each iteration should produce exactly one new PR layer and one new handoff zip.

## Input to Codex each round
- previous repo zip
- this PR target title
- this PR goal
- explicit DoD
- tests to run

## Output from Codex each round
1. updated repo zip
2. CHANGED_FILES.md
3. PR_NOTES.md
4. TEST_COMMANDS.md
5. NEXT_PR_SUGGESTION.md

## Naming rule
`new-repo_prXX_<slug>.zip`

## Required contents of each output zip
- repo/
- PR_NOTES.md
- CHANGED_FILES.md
- TEST_COMMANDS.md
- NEXT_PR_SUGGESTION.md

## Suggested Codex prompt skeleton
"Take the attached repo zip as the current base. Implement only PR-XX <TITLE>. Keep changes minimal and deterministic. Update tests and smoke scripts. Return a new zip with repo plus PR_NOTES.md, CHANGED_FILES.md, TEST_COMMANDS.md, and NEXT_PR_SUGGESTION.md."