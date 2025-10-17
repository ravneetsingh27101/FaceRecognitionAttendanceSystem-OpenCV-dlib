import tkinter as tk
from tkinter import ttk, messagebox

from config.settings import settings
from gui.views.dashboard_view import DashboardView
from gui.views.enroll_view import EnrollView
from gui.views.training_view import TrainingView
from gui.views.attendance_view import AttendanceView
from gui.views.reports_view import ReportsView
from gui.views.admin_view import AdminView
from gui.views.login_view import LoginDialog


class App:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("FRAS - Face Recognition Attendance System")
        self.root.geometry("1100x700")

        # --- Session state ---
        self.current_user = None
        self._login_open = False

        # --- Menu ---
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        account_menu = tk.Menu(menubar, tearoff=0)
        account_menu.add_command(label="Login (Admin)", command=self.show_login)
        account_menu.add_command(label="Logout", command=self.logout)
        account_menu.add_separator()
        account_menu.add_command(label="Exit", command=self.root.destroy)
        menubar.add_cascade(label="Account", menu=account_menu)

        # --- Tabs ---
        self.tabs = ttk.Notebook(self.root)

        self.dashboard = DashboardView(self.tabs)
        self.enroll = EnrollView(self.tabs)
        self.training = TrainingView(self.tabs)
        self.attendance = AttendanceView(self.tabs)
        self.reports = ReportsView(self.tabs)
        self.admin = AdminView(self.tabs)

        self.tabs.add(self.dashboard, text="Dashboard")
        self.tabs.add(self.enroll, text="Enrollment")
        self.tabs.add(self.training, text="Training")
        self.tabs.add(self.attendance, text="Take Attendance")
        self.tabs.add(self.reports, text="Reports")
        self.tabs.add(self.admin, text="Admin")
        self.tabs.pack(expand=1, fill="both")

        # Lock Enrollment/Training until Admin logs in
        self._disable_tab_by_text("Enrollment")
        self._disable_tab_by_text("Training")

        # Status bar
        self.status_var = tk.StringVar(value=self._status_text())
        status = tk.Label(self.root, textvariable=self.status_var, anchor="w")
        status.pack(side="bottom", fill="x")

        # Auto-start attendance on tab select (if enabled in view)
        def on_tab_changed(event):
            try:
                selected_widget = event.widget.nametowidget(event.widget.select())
            except Exception:
                return
            if selected_widget is self.attendance:
                if hasattr(self.attendance, "maybe_auto_start"):
                    try:
                        self.attendance.maybe_auto_start()
                    except Exception:
                        pass
        self.tabs.bind("<<NotebookTabChanged>>", on_tab_changed)

        # >>> Refresh dashboard immediately when attendance logs <<<
        def on_attendance_logged(event):
            if hasattr(self.dashboard, "refresh_now"):
                self.dashboard.refresh_now()
        self.root.bind("<<AttendanceLogged>>", on_attendance_logged)

        # Prompt login shortly after launch
        self.root.after(200, self.show_login)

    # ---------- Tab helpers ----------
    def _find_tab_index_by_text(self, label_text: str):
        for i in range(self.tabs.index("end")):
            if self.tabs.tab(i, "text") == label_text:
                return i
        return None

    def _disable_tab_by_text(self, label_text: str):
        idx = self._find_tab_index_by_text(label_text)
        if idx is not None:
            self.tabs.tab(idx, state="disabled")

    def _enable_tab_by_text(self, label_text: str):
        idx = self._find_tab_index_by_text(label_text)
        if idx is not None:
            self.tabs.tab(idx, state="normal")

    # ---------- Login / Logout ----------
    def show_login(self):
        if self._login_open:
            return
        self._login_open = True

        def _on_success_wrapped(user_dict):
            self._login_open = False
            self._on_login_success(user_dict)

        dlg = LoginDialog(self.root, on_success=_on_success_wrapped)
        dlg.bind("<Destroy>", lambda e: setattr(self, "_login_open", False))

    def _on_login_success(self, user_dict):
        self.current_user = user_dict
        role = (self.current_user.get("role") or "").lower()
        if role == "admin":
            self._enable_tab_by_text("Enrollment")
            self._enable_tab_by_text("Training")
            messagebox.showinfo("Login", f"Welcome, Admin!\nEmail: {self.current_user.get('email')}")
        else:
            self._disable_tab_by_text("Enrollment")
            self._disable_tab_by_text("Training")
            messagebox.showinfo("Login", f"Welcome, {self.current_user.get('email')}\nRole: {self.current_user.get('role')}")
        self.status_var.set(self._status_text())

    def logout(self):
        self.current_user = None
        self._disable_tab_by_text("Enrollment")
        self._disable_tab_by_text("Training")
        messagebox.showinfo("Logout", "You are now logged out.")
        self.status_var.set(self._status_text())

    def _status_text(self):
        who = "Not logged in"
        if self.current_user:
            who = f"{self.current_user.get('email')} ({self.current_user.get('role')})"
        return f"DB: {settings.DB_URL} | Cam: {settings.CAMERA_INDEX} | Liveness: {settings.ENABLE_LIVENESS} | User: {who}"

    def run(self):
        self.root.mainloop()
