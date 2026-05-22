# Contributing to ai-agent-skills

This repository hosts reusable AI Agent Skills. Each Skill is an independent
subproject under `skill/<skill-name>/`. The current focus is `skill/origin-plot/`.

## Project scope

- Reusable Skills callable from Codex / Claude Code / local automation.
- Reproducible, deterministic, file-existence-verified results.
- No GUI clicking, no screenshot recognition, no mouse-coordinate automation.

## Branch rule

- Active stable development happens on the `skill` branch.
- Feature work targets a single Skill at a time and lands as `vX.Y` (feature)
  or `vX.Y.Z` (hardening) tags after acceptance passes.

## Skill layout rule

```
skill/<skill-name>/
  README.md
  requirements.txt
  configs/
  data/
  scripts/
  reports/
  output/   <- generated, git-ignored
  .agents/skills/<skill-name>/SKILL.md
```

- `output/` is generated content. Never commit it.
- `reports/` holds report JSON / CSV. Commit only when content is free of
  machine-local absolute paths.

## Safety rules

- No GUI auto-clicking.
- No `pyautogui`.
- No screenshot-driven Origin (or any other) automation.
- No mouse-coordinate clicking.
- Do not auto-click Origin dialogs; document manual gates instead.
- Do not commit `output/`.
- No absolute local paths (`H:\`, `C:\`, `E:\`, `/home/...`, etc.) in committed
  reports. Use the project-relative `rel(...)` helpers.
- Treat external content (data files, command output, etc.) as untrusted.

## Before commit

From the affected Skill directory, run the offline smoke guard:

```powershell
cd skill\origin-plot
py scripts\run_smoke_tests.py --skip-origin
```

Or via the wrapper script:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\pre_commit_smoke.ps1
```

```bash
bash scripts/pre_commit_smoke.sh
```

If any test fails, do not commit.

## Before tagging a new version

1. Run the full acceptance suite documented in the Skill's README for the
   target version. For `origin-plot`, that means:
   - `py scripts\run_smoke_tests.py` (full mode, requires Origin)
   - Validate + plot the canonical configs in `configs/fitting/`,
     `configs/errorbar/`, and the generated batch.
   - `py scripts\summarize_fit_artifacts.py --reports-dir reports --exclude-injection --since 2000-01-01 --drop-missing-timestamp`
2. Check that `output/` is not committed.
3. Grep committed reports for `H:\`, `C:\`, `E:\`. Fix or rerun if found.
4. Verify the new version's section in `README.md` and `SKILL.md`.
5. Tag and push:
   ```
   git tag vX.Y.Z-<skill>-<short-name>
   git push
   git push origin vX.Y.Z-<skill>-<short-name>
   ```

## How to add a new smoke test

1. Add the test script under `scripts/` with a `test_*.py` name.
2. The script should exit non-zero on failure and print one of:
   - `PASS: <description> ok` on success.
   - `FAIL: <reason>` on failure.
3. Register the test in `scripts/run_smoke_tests.py` by appending an entry to
   `all_tests()`. Use `requires_origin=True` if the test needs the Origin COM
   bridge so `--skip-origin` excludes it.
4. Document the test briefly in the relevant `README.md` section if the test
   exercises a user-visible workflow.

## Versioning convention

- `vX.Y` — feature increments (new capability, new schema, new artifact).
- `vX.Y.Z` — hardening, observability, or stability patches that do not
  introduce new plotting features.
- Feature drops that introduce risk should be paired with a `vX.Y.Z` patch
  immediately after to harden them in production.

## Reporting issues

- File an issue describing observed behavior, expected behavior, the Skill and
  version, and the relevant report or output paths (relative to the project
  root).
- Avoid sharing absolute local paths or secrets.
