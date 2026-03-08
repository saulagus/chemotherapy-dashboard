from tkinter import messagebox


def show_error(title: str, message: str) -> None:
    """Display a native OS error dialog with the given title and message."""
    messagebox.showerror(title, message)


def show_info(title: str, message: str) -> None:
    """Display a native OS info dialog with the given title and message."""
    messagebox.showinfo(title, message)
