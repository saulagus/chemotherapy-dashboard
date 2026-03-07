import tkinter as tk
from tkinter import messagebox
import sys
import os

# Add src/ to the path so database.py and models.py can be imported directly.
sys.path.insert(0, os.path.dirname(__file__))

from database import get_connection, create_tables


class App(tk.Tk):
    """Main application window for the AC-T Chemotherapy Dashboard.

    Inherits from tk.Tk — App IS the window, no separate root object needed.
    """

    TITLE = "AC-T Chemotherapy Dashboard"
    MIN_WIDTH = 1024
    MIN_HEIGHT = 768

    def __init__(self):
        super().__init__()  # Initialize the Tkinter root window first.
        self.conn = None    # Database connection — set in _init_database().
        self._setup_window()
        self._init_database()

    def _setup_window(self):
        self.title(self.TITLE)                           # Text shown in the OS title bar.
        self.geometry(f"{self.MIN_WIDTH}x{self.MIN_HEIGHT}")  # Initial window size in pixels.
        self.minsize(self.MIN_WIDTH, self.MIN_HEIGHT)    # Prevent shrinking below this size.

        # Override the close button (X) to run _on_close instead of quitting immediately,
        # so the database connection is properly closed before the window is destroyed.
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        # Returns nothing. Window properties are set and ready.

    def _init_database(self):
        # Wrap in try/except so a DB failure shows a clear dialog instead of a traceback.
        try:
            self.conn = get_connection()
            create_tables(self.conn)  # Safe on first run — creates tables if missing.
        except Exception as e:
            messagebox.showerror("Database Error", f"Failed to initialize database:\n{e}")
            self.destroy()  # Close the window if the database cannot be initialized.
        # Returns nothing.
        # On success: connection is open and tables exist.
        # On failure: error dialog shown and window closed.

    def _on_close(self):
        # Close the DB connection before shutting down to flush writes and release the file.
        if self.conn:
            self.conn.close()
        self.destroy()
        # Returns nothing. Application has fully shut down.


def main():
    app = App()
    # mainloop() keeps the window open and listens for user actions until the app is closed.
    app.mainloop()


if __name__ == "__main__":
    # Only runs when this file is executed directly — not when imported.
    main()
