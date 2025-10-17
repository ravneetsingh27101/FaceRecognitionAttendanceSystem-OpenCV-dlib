import tkinter as tk
from tkinter import messagebox
from core.trainer import train_and_save
from core.evaluator import evaluate

class TrainingView(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        tk.Button(self, text="Train LBPH", command=self.train).pack(pady=8)
        tk.Button(self, text="Evaluate", command=self.eval).pack(pady=8)
        self.out = tk.Text(self, height=20)
        self.out.pack(expand=True, fill="both")

    def train(self):
        res = train_and_save()
        self.out.insert("end", f"{res}\n")
        if not res.get("ok"):
            messagebox.showerror("Training", res.get("msg","Error"))
        else:
            messagebox.showinfo("Training", "Model trained and saved.")

    def eval(self):
        res = evaluate()
        self.out.insert("end", f"{res}\n")
        if not res.get("ok"):
            messagebox.showerror("Evaluate", res.get("msg","Error"))
