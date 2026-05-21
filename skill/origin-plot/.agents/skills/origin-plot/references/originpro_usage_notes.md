# OriginPro Usage Notes

## Why not automate GUI clicks

Origin scientific plotting should be reproducible. GUI clicking, screenshot recognition, and mouse-coordinate automation are fragile because window layout, scaling, language, dialogs, and focus can change. They also make it difficult to prove which data and settings produced a figure. Use `originpro` so data import, plotting, exporting, and project saving are described in code.

## Why Windows Python is preferred

Windows Origin/OriginPro exposes automation through Windows COM. The `originpro` package connects through that local Windows automation layer. WSL Python usually cannot directly call Windows COM / Origin Automation, even when it can see Windows files. Use `py` or a Windows `python.exe` when controlling installed Windows Origin.

## originpro, OriginExt, and COM

`originpro` is OriginLab's Python package for controlling Origin from external Python or Origin's embedded Python. For external Python automation, it relies on Origin Automation Server / COM under the hood. OriginExt is the lower-level bridge used by OriginLab tooling. If COM registration or the Origin installation is broken, `originpro` may import but fail when attaching to or launching Origin.

## Common errors

- `ModuleNotFoundError: originpro`: install the Python package into the Windows Python environment used by Codex.
- `Origin not installed`: install Origin/OriginPro 2021 or later, then confirm common OriginLab paths or Start Menu entries exist.
- `COM launch failed`: confirm Origin can start normally, repair/register the installation if needed, and use Windows Python with the same user account.
- `running from WSL`: switch to PowerShell/CMD and run `py`, because WSL Python usually cannot control Windows COM.
- `no numeric columns`: clean the data file or choose numeric columns explicitly before plotting.

## Common repair command

```powershell
py -m pip install originpro pandas openpyxl
```

## Recommended run order

```powershell
py .agents\skills\origin-plot\scripts\check_origin_env.py
py .agents\skills\origin-plot\scripts\plot_origin_template.py
```

Run the plotting script only after the environment report says `ready_for_origin_automation` is true, unless you are intentionally debugging a known Origin/COM failure.
