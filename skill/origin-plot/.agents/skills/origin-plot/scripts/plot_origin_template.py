"""Template: generate a verified Origin/OriginPro plot from CSV data.

Default input order:
1. data/sample.csv
2. .agents/skills/origin-plot/assets/sample.csv
"""

from __future__ import annotations

import sys
import traceback
from pathlib import Path
from typing import Iterable


PROJECT_ROOT = Path(__file__).resolve().parents[4]
DEFAULT_DATA = PROJECT_ROOT / "data" / "sample.csv"
FALLBACK_DATA = PROJECT_ROOT / ".agents" / "skills" / "origin-plot" / "assets" / "sample.csv"
OUTPUT_DIR = PROJECT_ROOT / "output" / "origin_plot"
PNG_PATH = OUTPUT_DIR / "origin_plot.png"
PDF_PATH = OUTPUT_DIR / "origin_plot.pdf"
OPJU_PATH = OUTPUT_DIR / "origin_plot_project.opju"


def fail(message: str, code: int = 1) -> None:
    print(f"ERROR: {message}")
    raise SystemExit(code)


def require_outputs(paths: Iterable[Path]) -> None:
    missing = [str(path) for path in paths if not path.exists()]
    if missing:
        print("FAIL: missing expected Origin outputs:")
        for path in missing:
            print(f"- {path}")
        raise SystemExit(1)
    print("PASS: generated all expected Origin outputs")


def choose_input() -> Path:
    if DEFAULT_DATA.exists():
        return DEFAULT_DATA
    if FALLBACK_DATA.exists():
        return FALLBACK_DATA
    fail(f"No input CSV found at {DEFAULT_DATA} or {FALLBACK_DATA}")
    raise AssertionError("unreachable")


def main() -> int:
    try:
        import pandas as pd
    except Exception as exc:  # noqa: BLE001 - report dependency failure clearly
        fail(f"Could not import pandas: {type(exc).__name__}: {exc}")

    try:
        import originpro as op  # type: ignore
    except Exception as exc:  # noqa: BLE001 - report dependency failure clearly
        fail(
            "Could not import originpro. Install prerequisites with "
            f"'py -m pip install originpro pandas openpyxl'. Details: {type(exc).__name__}: {exc}"
        )

    input_path = choose_input()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(input_path)
    numeric_df = df.select_dtypes(include="number")
    if numeric_df.shape[1] < 2:
        fail(
            "At least two numeric columns are required: first numeric column as X, "
            "remaining numeric columns as Y."
        )

    x_col = numeric_df.columns[0]
    y_cols = list(numeric_df.columns[1:])
    plot_df = numeric_df[[x_col] + y_cols].copy()

    origin_started = False
    try:
        op.set_show(True)
        op.new()
        origin_started = True

        wks = op.new_sheet("w", lname="Codex_Data")
        wks.from_df(plot_df)

        try:
            wks.cols_axis("X" + "Y" * len(y_cols))
        except Exception:
            # Older originpro versions can still plot by explicit column ranges.
            pass

        graph = op.new_graph(template="line")
        layer = graph[0]

        for y_index, y_col in enumerate(y_cols, start=1):
            plot = layer.add_plot(wks, coly=y_index, colx=0, type="l")
            try:
                plot.name = str(y_col)
            except Exception:
                pass

        layer.rescale()

        title = f"Origin plot from {input_path.name}"
        try:
            graph.lt_exec(f'title.text$ = "{title}";')
        except Exception:
            pass

        try:
            layer.axis("x").title = str(x_col)
            layer.axis("y").title = ", ".join(str(col) for col in y_cols)
        except Exception:
            pass

        try:
            graph.lt_exec("legend -r;")
        except Exception:
            pass

        graph.save_fig(str(PNG_PATH))
        graph.save_fig(str(PDF_PATH))
        op.save(str(OPJU_PATH))

    except Exception as exc:  # noqa: BLE001 - Origin COM failures need clear reporting
        traceback.print_exc()
        fail(
            "Origin automation failed. Confirm Windows Origin/OriginPro is installed, "
            f"registered, and compatible with originpro. Details: {type(exc).__name__}: {exc}"
        )
    finally:
        if origin_started:
            try:
                op.exit()
            except Exception:
                pass

    require_outputs([PNG_PATH, PDF_PATH, OPJU_PATH])
    print(f"PNG: {PNG_PATH}")
    print(f"PDF: {PDF_PATH}")
    print(f"OPJU: {OPJU_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
