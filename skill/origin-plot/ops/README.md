# ops/

Advanced maintenance tooling. **Not** a daily entry surface.

If you only need to render a figure, ignore this directory and use
[`../workflows/`](../workflows/README.md).

Every Python file under `ops/` is a thin re-export of the verified
v0.8.7 implementation in [`../scripts/`](../scripts/). The shell scripts
under `ops/release/` are equally thin wrappers around the matching
`scripts/...` shell scripts. The intent of `ops/` is not to add
behavior; it is to give operators a categorised, stable layout while
the legacy entry surface in `scripts/` is preserved.

## Subdirectories

| Subdirectory | Purpose | Example command |
|---|---|---|
| [`diagnostics/`](diagnostics/) | Test injection / retry path diagnostics. | `py ops\diagnostics\test_cli_retry_injection.py` |
| [`health/`](health/) | Session history, retry/health logic tests, history reset. | `py ops\health\reset_session_history.py` |
| [`smoke/`](smoke/) | Aggregate smoke test runner. | `py ops\smoke\run_smoke_tests.py --skip-origin` |
| [`hygiene/`](hygiene/) | Pre-commit / report path leak guards. | `py ops\hygiene\check_committed_reports.py` |
| [`release/`](release/) | Pre-commit shells (PowerShell + bash). | `powershell -ExecutionPolicy Bypass -File ops\release\pre_commit_smoke.ps1` |
| [`reports/`](reports/) | Cross-report fit-artifact rollups. | `py ops\reports\summarize_fit_artifacts.py --reports-dir reports --exclude-injection --since 2000-01-01 --drop-missing-timestamp` |

## Why a re-export layer?

The v1.0 refactor made the public surface live in `workflows/` while
keeping the verified v0.8.7 implementation in `scripts/` unchanged.
`ops/` documents the maintenance side of that surface in a categorised
form so links from `README.md` and `DIRECTORY.md` are stable. Under the
hood, every shim invokes the matching legacy script via `runpy` (Python)
or by passing `@args` (PowerShell / bash); behaviour and exit codes
match the legacy invocation byte-for-byte.

## When to use what

- **Fix a daily plot:** use `workflows/run_plot.py`.
- **Validate before committing:** run `ops/release/pre_commit_smoke.ps1`
  (or `.sh`). It runs the offline smoke runner and the report path leak
  scan in sequence.
- **Investigate a flaky Origin run:** start with
  `ops/diagnostics/test_cli_retry_injection.py` to verify the retry path
  itself, then look at the session history under `ops/health/`.
- **Reset accumulated session history:** use
  `ops/health/reset_session_history.py`.
- **Cross-batch rollup of fit artifacts:** use
  `ops/reports/summarize_fit_artifacts.py`.

## What `ops/` does NOT do

- It does not introduce new behavior. Replacing the v0.8.7 backend is a
  v1.x task, not a v1.0 task. See
  [`../archive/v1_0_scope_clarification.md`](../archive/v1_0_scope_clarification.md).
- It does not gate the daily workflow. `workflows/run_plot.py` and
  `workflows/run_batch.py` work without ever invoking anything under
  `ops/`.

## Cross-links

- Daily users: [`../workflows/README.md`](../workflows/README.md)
- Codex contract: [`../contracts/README.md`](../contracts/README.md)
- Verified backend (source of truth): [`../scripts/`](../scripts/)
- Historical anchors: [`../archive/README.md`](../archive/README.md)
