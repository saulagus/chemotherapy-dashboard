from tkinter import messagebox
from tkinter import ttk

# ── Dark theme colour palette ─────────────────────────────────────────────────
BG          = '#12151c'   # main background — deep blue-slate
BG_ALT      = '#1a1e2a'   # card / panel surfaces
BG_ROW_ODD  = '#1f2435'   # Treeview odd-row stripe
BG_HEADER   = '#1f2435'   # Treeview heading background
SEPARATOR   = '#2a2f42'   # separator lines
FG          = '#e8eaf0'   # primary text — slightly warm white
FG_MUTED    = '#6b7494'   # secondary / placeholder text
SELECTED    = '#2d5a8e'   # selected row highlight


def apply_dark_theme(style: ttk.Style) -> None:
    """Configure ttk widgets to use the dark palette.

    Call once after the Tk root is created (e.g. in App._setup_window).
    Uses the 'default' theme as the base because it allows full colour overrides;
    the macOS 'aqua' theme ignores most colour settings.
    """
    style.theme_use('default')

    style.configure('Treeview',
        background=BG_ALT,
        foreground=FG,
        fieldbackground=BG_ALT,
        borderwidth=0,
        rowheight=38,
        font=('Arial', 13),
    )
    style.configure('Treeview.Heading',
        background=BG_HEADER,
        foreground=FG_MUTED,
        borderwidth=0,
        relief='flat',
        font=('Arial', 12),
    )
    style.map('Treeview',
        background=[('selected', SELECTED)],
        foreground=[('selected', FG)],
    )
    style.map('Treeview.Heading',
        background=[('active', SEPARATOR)],
    )


def show_error(title: str, message: str) -> None:
    """Display a native OS error dialog with the given title and message."""
    messagebox.showerror(title, message)


def show_info(title: str, message: str) -> None:
    """Display a native OS info dialog with the given title and message."""
    messagebox.showinfo(title, message)
