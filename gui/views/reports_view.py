import tkinter as tk
from tkinter import filedialog, messagebox
import os, csv
import pandas as pd

class ReportsView(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        tk.Button(self, text="Open Exports Folder", command=self.open_dir).pack(pady=8)
        tk.Button(self, text="Export Sample XLSX", command=self.export_xlsx).pack(pady=8)

    def open_dir(self):
        path = "reports/exports"
        os.makedirs(path, exist_ok=True)
        messagebox.showinfo("Exports", f"Exports at: {os.path.abspath(path)}")

    def export_xlsx(self):
        path = "reports/exports"
        os.makedirs(path, exist_ok=True)
        csvs = [f for f in os.listdir(path) if f.endswith(".csv")]
        if not csvs:
            messagebox.showwarning("No CSV", "No CSV attendance found yet.")
            return
        df = pd.read_csv(os.path.join(path, csvs[-1]))
        out = os.path.join(path, "latest.xlsx")
        df.to_excel(out, index=False)
        messagebox.showinfo("XLSX", f"Created: {os.path.abspath(out)}")
