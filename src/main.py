import tkinter as tk
from tkinter import messagebox
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from database import get_connection, create_tables


class App(tk.Tk):
    """Main application window for the AC-T Chemotherapy Dashboard."""

    TITLE = "AC-T Chemotherapy Dashboard"
    MIN_WIDTH = 1024
    MIN_HEIGHT = 768

    def __init__(self):
        super().__init__()
        self.conn = None
        self._setup_window()
        self._init_database()

    def _setup_window(self):
        self.title(self.TITLE)
        self.geometry(f"{self.MIN_WIDTH}x{self.MIN_HEIGHT}")
        self.minsize(self.MIN_WIDTH, self.MIN_HEIGHT)
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _init_database(self):
        try:
            self.conn = get_connection()
            create_tables(self.conn)
        except Exception as e:
            messagebox.showerror("Database Error", f"Failed to initialize database:\n{e}")
            self.destroy()

    def _on_close(self):
        if self.conn:
            self.conn.close()
        self.destroy()


def main():
    app = App()
    app.mainloop()


if __name__ == "__main__":
    main()
