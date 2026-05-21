from __future__ import annotations

import platform
import sys
import traceback
import faulthandler


def main() -> int:
    faulthandler.enable()
    faulthandler.dump_traceback_later(120, exit=True)
    app = None
    try:
        print("Python executable:", sys.executable, flush=True)
        print("Python version:", sys.version, flush=True)
        print("Platform:", platform.platform(), flush=True)

        import OriginExt as O  # type: ignore

        print("OriginExt import ok", flush=True)
        app = O.Application()
        print("app object:", app, flush=True)
        app.Visible = 1
        app.LT_execute('type -b "Origin COM OK";')
        try:
            app.Exit()
        finally:
            del app
        faulthandler.cancel_dump_traceback_later()
        print("PASS: OriginExt COM smoke test ok", flush=True)
        return 0
    except Exception:
        faulthandler.cancel_dump_traceback_later()
        print("FAIL: OriginExt COM smoke test failed", flush=True)
        traceback.print_exc()
        try:
            if app is not None:
                app.Exit()
        except Exception:
            pass
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
