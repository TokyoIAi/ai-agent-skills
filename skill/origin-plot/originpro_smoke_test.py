from __future__ import annotations

import platform
import sys
import traceback
import faulthandler


def main() -> int:
    faulthandler.enable()
    faulthandler.dump_traceback_later(120, exit=True)
    op = None
    try:
        print("Python executable:", sys.executable, flush=True)
        print("Python version:", sys.version, flush=True)
        print("Platform:", platform.platform(), flush=True)

        import originpro as op  # type: ignore

        print("originpro import ok", flush=True)
        print("originpro version:", getattr(op, "__version__", "version unknown"), flush=True)
        op.set_show(True)
        wks = op.new_sheet()
        print("new_sheet ok", wks, flush=True)
        try:
            op.exit()
        except Exception:
            pass
        faulthandler.cancel_dump_traceback_later()
        print("PASS: originpro smoke test ok", flush=True)
        return 0
    except Exception:
        faulthandler.cancel_dump_traceback_later()
        print("FAIL: originpro smoke test failed", flush=True)
        traceback.print_exc()
        return 1
    finally:
        if op is not None:
            try:
                op.exit()
            except Exception:
                pass


if __name__ == "__main__":
    raise SystemExit(main())
