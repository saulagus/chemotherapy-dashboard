import tkinter as tk
import sys
import os

# Add the src/ directory to Python's search path so we can import
# database.py and models.py using simple 'from database import ...' statements.
sys.path.insert(0, os.path.dirname(__file__))

from database import get_connection, create_tables
from utils import show_error


class App(tk.Tk):
    """Main application window for the AC-T Chemotherapy Dashboard.

    Inherits from tk.Tk, which is the root Tkinter window.
    Inheriting means App IS the window — we don't create a separate tk.Tk() object.
    """

    TITLE = "AC-T Chemotherapy Dashboard"
    MIN_WIDTH = 1024
    MIN_HEIGHT = 768

    def __init__(self):
        # Initialize the Tkinter root window (the parent class).
        # This must be called before any other Tkinter setup.
        super().__init__()
        self.conn = None    # Database connection — set in _init_database().
        self.frames = {}    # Stores instantiated views keyed by their class.
        self._setup_window()
        self._init_database()
        self._init_navigation()

    def _setup_window(self):
        # Set the text shown in the OS title bar.
        self.title(self.TITLE)

        # Set the initial window size in pixels (width x height).
        self.geometry(f"{self.MIN_WIDTH}x{self.MIN_HEIGHT}")

        # Prevent the user from resizing the window smaller than this.
        self.minsize(self.MIN_WIDTH, self.MIN_HEIGHT)

        # WM_DELETE_WINDOW is the event fired when the user clicks the
        # window's close button (the X). By default it just destroys the
        # window without cleanup. We override it to close the DB connection first.
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        # Returns nothing. The window properties are now set and ready.

    def _init_database(self):
        # Wrap database setup in a try/except so any failure shows a clear
        # error message instead of a raw Python traceback.
        try:
            self.conn = get_connection()
            # Create tables if they don't exist yet (safe on first run).
            create_tables(self.conn)
        except Exception as e:
            show_error("Database Error", f"Failed to initialize database:\n{e}")
            # destroy() closes the window and ends the application.
            self.destroy()
        # Returns nothing.
        # On success: the database connection is open and all tables are ready.
        # On failure: an error dialog was shown and the window has been closed.

    def _init_navigation(self):
        # Container fills the entire window. All views are stacked inside it.
        # grid is used so the container stretches to fill available space.
        self.container = tk.Frame(self)
        self.container.pack(fill='both', expand=True)
        self.container.grid_rowconfigure(0, weight=1)
        self.container.grid_columnconfigure(0, weight=1)

        # Import here to avoid circular imports (views import App).
        from views.patient_list import PatientListView
        self.show_frame(PatientListView)

    def show_frame(self, frame_class, **kwargs):
        """Switch the visible view to the given frame class.

        If the frame has not been created yet, it is instantiated and stored.
        DashboardView is always recreated so it reflects the selected patient.
        kwargs are passed to the frame constructor (e.g. patient_id for dashboard).
        """
        # Import here to avoid circular imports at module level.
        from views.dashboard import DashboardView

        # Always recreate DashboardView so it loads fresh patient data.
        if frame_class is DashboardView and DashboardView in self.frames:
            self.frames[DashboardView].destroy()
            del self.frames[DashboardView]

        if frame_class not in self.frames:
            # Each view receives the container as its parent and app as a reference,
            # so views can call app.show_frame() to trigger navigation themselves.
            frame = frame_class(self.container, self, **kwargs)
            self.frames[frame_class] = frame
            # Place every frame in the same grid cell — only the raised one is visible.
            frame.grid(row=0, column=0, sticky='nsew')

        # tkraise() brings this frame to the top of the stack, hiding all others.
        self.frames[frame_class].tkraise()

    def _on_close(self):
        # Close the database connection before shutting down.
        # This ensures all pending writes are flushed and the file is not left locked.
        if self.conn:
            self.conn.close()
        self.destroy()
        # Returns nothing. The application has fully shut down.


def main():
    app = App()
    # mainloop() starts the Tkinter event loop — it listens for user actions
    # (clicks, key presses, window events) and keeps the window open until
    # the application is closed.
    app.mainloop()


if __name__ == "__main__":
    # This block only runs when the file is executed directly (e.g. python main.py).
    # It does not run when main.py is imported by another file or by tests.
    main()
