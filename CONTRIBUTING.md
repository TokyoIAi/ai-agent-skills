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

## Adding a new smoke test (concrete example)

Suppose you want to verify a hypothetical helper `format_summary()` exposed by
`scripts/example_utils.py`. The full workflow:

### 1. Create the script

`scripts/test_example_logic.py`:

```python
from __future__ import annotations

import sys
import traceback
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from example_utils import format_summary  # noqa: E402


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def test_format_summary_includes_status() -> None:
    payload = format_summary({"status": "PASS"})
    assert_true("PASS" in payload, f"expected PASS in payload; got {payload!r}")


def run_all() -> int:
    tests = [test_format_summary_includes_status]
    failed = 0
    for test in tests:
        try:
            test()
            print(f"ok: {test.__name__}")
        except AssertionError as exc:
            failed += 1
            print(f"FAIL: {test.__name__}: {exc}")
        except Exception:  # noqa: BLE001
            failed += 1
            print(f"FAIL: {test.__name__} raised an unexpected error")
            traceback.print_exc()
    if failed:
        print(f"FAIL: {failed} test(s) failed")
        return 1
    print("PASS: example logic smoke tests ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(run_all())
```

### 2. Exit code contract

- `0` (zero) means PASS.
- Non-zero means FAIL. Always print a `FAIL: ...` line so the runner can show
  the reason.

### 3. Stdout contract

- A single `PASS: <description> ok` on success, after any per-test `ok: ...`
  lines.
- One or more `FAIL: <reason>` lines on failure.
- Avoid printing absolute paths.

### 4. Register in `run_smoke_tests.py`

Append a tuple to `all_tests()`:

```python
(
    "test_example_logic",
    [sys.executable, "scripts/test_example_logic.py"],
    False,  # requires_origin
),
```

### 5. When to set `requires_origin=True`

Set it to `True` when the test:

- Imports `originpro` (or `OriginExt`).
- Spawns a subprocess that calls `originpro` (e.g., the CLI retry test that
  invokes `origin_plot_from_config.py`).
- Depends on a running Origin install or COM bridge.

When unsure, prefer `True`. Tests marked `requires_origin=True` are skipped by
`run_smoke_tests.py --skip-origin` and the pre-commit guard.

### 6. Run before committing

From `skill/origin-plot/`:

```powershell
py scripts\run_smoke_tests.py --skip-origin
powershell -ExecutionPolicy Bypass -File scripts\pre_commit_smoke.ps1
```

```bash
bash scripts/pre_commit_smoke.sh
```

If either fails, fix the test or the code before committing.

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
