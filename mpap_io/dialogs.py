"""
===============================================================================
MPAP
Melt Pool Analysis Platform

File Dialog Utilities
===============================================================================
"""

from pathlib import Path
from tkinter import Tk, filedialog


def select_file(
    *,
    title: str = "Select File",
    filetypes: list[tuple[str, str]] | None = None,
) -> Path | None:
    """
    Open a file picker and return the selected file.

    Returns
    -------
    Path | None
        Selected file, or None if the dialog is cancelled.
    """

    root = Tk()
    root.withdraw()

    filename = filedialog.askopenfilename(
        title=title,
        filetypes=filetypes,
    )

    root.destroy()

    if not filename:
        return None

    return Path(filename)