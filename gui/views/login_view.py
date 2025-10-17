import tkinter as tk
from tkinter import ttk, messagebox
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import bcrypt

from config.settings import settings
from scripts.init_db import Base, User, Role


class LoginDialog(tk.Toplevel):
    """
    Modal login dialog.
    On success, calls on_success(user_dict) with {"id","email","role"}.
    """
    def __init__(self, parent, on_success):
        super().__init__(parent)
        self.title("Admin Login – FRAS")
        self.resizable(False, False)
        self.protocol("WM_DELETE_WINDOW", self._on_close)

        self._on_success = on_success

        # Center near parent
        self.geometry("+%d+%d" % (parent.winfo_rootx() + 80, parent.winfo_rooty() + 80))

        frm = ttk.Frame(self, padding=16)
        frm.grid(row=0, column=0)

        ttk.Label(frm, text="Email").grid(row=0, column=0, sticky="w")
        self.email_var = tk.StringVar(value="admin@local")
        ttk.Entry(frm, textvariable=self.email_var, width=32).grid(row=1, column=0, columnspan=2, pady=(0,8))

        ttk.Label(frm, text="Password").grid(row=2, column=0, sticky="w")
        self.pass_var = tk.StringVar()
        ttk.Entry(frm, textvariable=self.pass_var, show="*", width=32).grid(row=3, column=0, columnspan=2, pady=(0,12))

        self.info_var = tk.StringVar(value="")
        ttk.Label(frm, textvariable=self.info_var, foreground="#666").grid(row=4, column=0, columnspan=2, sticky="w", pady=(0,8))

        btns = ttk.Frame(frm)
        btns.grid(row=5, column=0, columnspan=2, sticky="e")
        ttk.Button(btns, text="Cancel", command=self._on_close).pack(side="right", padx=6)
        ttk.Button(btns, text="Login", command=self._login).pack(side="right")

        self._engine = create_engine(settings.DB_URL, future=True)
        Base.metadata.create_all(self._engine)
        self._Session = sessionmaker(bind=self._engine, autoflush=False, autocommit=False)

        # Modal
        self.transient(parent)
        self.grab_set()
        self.focus_force()

    def _on_close(self):
        self.grab_release()
        self.destroy()

    def _login(self):
        email = (self.email_var.get() or "").strip()
        pw = self.pass_var.get() or ""
        if not email or not pw:
            messagebox.showerror("Login", "Please enter email and password.")
            return

        db = self._Session()
        try:
            user = db.query(User).filter(User.email == email).first()
            if not user or not bcrypt.checkpw(pw.encode(), user.password_hash.encode()):
                messagebox.showerror("Login", "Invalid credentials.")
                return

            role_name = None
            if user.role_id:
                role = db.query(Role).filter(Role.id == user.role_id).first()
                role_name = role.name if role else None

            user_dict = {"id": user.id, "email": user.email, "role": role_name or "Unknown"}
            self._on_success(user_dict)
            self.grab_release()
            self.destroy()
        finally:
            db.close()
