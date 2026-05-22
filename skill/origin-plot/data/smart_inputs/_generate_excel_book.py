"""One-shot helper to (re)create the sample Excel input.

Run from ``skill/origin-plot/`` if the workbook is missing or out of date::

    py data\\smart_inputs\\_generate_excel_book.py
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

OUTPUT = Path(__file__).resolve().parents[0] / "sample_excel_book.xlsx"

df = pd.DataFrame(
    {
        "时间(s)": [0, 1, 2, 3, 4],
        "温度(C)": [20.1, 22.4, 25.3, 28.0, 31.5],
        "湿度(%)": [55, 53, 50, 48, 45],
    }
)

with pd.ExcelWriter(OUTPUT, engine="openpyxl") as writer:
    df.to_excel(writer, sheet_name="实验数据", index=False)

print(f"wrote: {OUTPUT}")
