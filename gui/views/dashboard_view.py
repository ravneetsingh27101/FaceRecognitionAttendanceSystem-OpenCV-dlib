# gui/views/dashboard_view.py
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import os, csv, glob
from datetime import datetime

EXPORTS_DIR = os.path.join("reports", "exports")

class DashboardView(tk.Frame):
    """
    Shows today's attendance log from reports/exports/{YYYY-MM-DD}.csv.
    Auto-refreshes every few seconds and refreshes immediately when an
    attendance event is logged (App binds <<AttendanceLogged>> to refresh_now).
    """
    def __init__(self, parent):
        super().__init__(parent)

        header = tk.Frame(self); header.pack(fill="x", pady=(8, 6))
        tk.Label(header, text="Today’s Attendance", font=("Segoe UI", 14, "bold")).pack(side="left", padx=10)

        btns = tk.Frame(self); btns.pack(fill="x", pady=(0, 6))
        tk.Button(btns, text="Refresh Now", command=self.refresh_now, width=14).pack(side="left", padx=(10, 6))
        tk.Button(btns, text="Open Exports Folder", command=self._open_exports, width=18).pack(side="left")

        # summary line
        self.summary_var = tk.StringVar(value="No data yet.")
        tk.Label(self, textvariable=self.summary_var, anchor="w").pack(fill="x", padx=10, pady=(2, 6))

        # table
        cols = ("person_id", "timestamp", "status")
        self.tree = ttk.Treeview(self, columns=cols, show="headings", height=20)
        self.tree.heading("person_id", text="Person ID")
        self.tree.heading("timestamp", text="Timestamp")
        self.tree.heading("status", text="Status")

        self.tree.column("person_id", width=180, anchor="w")
        self.tree.column("timestamp", width=260, anchor="w")
        self.tree.column("status", width=120, anchor="center")

        vsb = ttk.Scrollbar(self, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)

        table_wrap = tk.Frame(self); table_wrap.pack(fill="both", expand=True, padx=10)
        self.tree.pack(in_=table_wrap, side="left", fill="both", expand=True)
        vsb.pack(in_=table_wrap, side="right", fill="y")

        # kick off
        self._auto_ms = 3000
        self.after(300, self.refresh_now)
        self._schedule_auto()

    # ---------- data helpers ----------

    def _today_csv_path(self):
        today = datetime.now().strftime("%Y-%m-%d")
        path = os.path.join(EXPORTS_DIR, f"{today}.csv")
        if os.path.exists(path):
            return path
        # fallback: most recent CSV in exports
        if os.path.isdir(EXPORTS_DIR):
            candidates = sorted(glob.glob(os.path.join(EXPORTS_DIR, "*.csv")), key=os.path.getmtime, reverse=True)
            if candidates:
                return candidates[0]
        return None

    def _read_rows(self, csv_path):
        rows = []
        if not csv_path or not os.path.exists(csv_path):
            return rows
        try:
            with open(csv_path, "r", encoding="utf-8") as f:
                r = csv.DictReader(f)
                for row in r:
                    rows.append({
                        "person_id": row.get("person_id", ""),
                        "timestamp": row.get("timestamp", ""),
                        "status": row.get("status", ""),
                    })
        except Exception as e:
            messagebox.showerror("Dashboard", f"Failed to read log: {e}")
        return rows

    # ---------- UI actions ----------

    def refresh_now(self, *_):
        csv_path = self._today_csv_path()
        rows = self._read_rows(csv_path)
        
        # clear
        for i in self.tree.get_children():
            self.tree.delete(i)
        # fill
        for r in rows:
            self.tree.insert("", "end", values=(r["person_id"], r["timestamp"], r["status"]))

        # summary
        present = sum(1 for r in rows if (r.get("status") or "").lower() == "present")
        self.summary_var.set(
            f"File: {os.path.basename(csv_path) if csv_path else '—'} | Total rows: {len(rows)} | Present: {present}"
            if rows else "No attendance logged yet for today."
        )

    def _open_exports(self):
        os.makedirs(EXPORTS_DIR, exist_ok=True)
        try:
            # Ask the OS to open the folder
            os.startfile(EXPORTS_DIR)  # Windows
        except Exception:
            # Fallback: show a dialog pointing there
            filedialog.askopenfilename(initialdir=EXPORTS_DIR, title="Exports Folder")

    # ---------- auto refresh ----------

    def _schedule_auto(self):
        self.after(self._auto_ms, self._auto_refresh)

    def _auto_refresh(self):
        self.refresh_now()
        self._schedule_auto()
