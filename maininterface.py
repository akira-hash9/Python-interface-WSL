import tkinter as tk
from tkinter import scrolledtext
import subprocess
import threading
import os
from datetime import datetime

EXEC_PATH = os.path.join(os.path.dirname(__file__), "executers")

LOG_DIR = os.path.join(os.path.dirname(__file__), "logs")
os.makedirs(LOG_DIR, exist_ok=True)

def run_script(script_name):
    script_path = os.path.join(EXEC_PATH, script_name)

    if not os.path.isfile(script_path):
        log(f"[ERRO] Arquivo não encontrado: {script_path}")
        return

    log(f"[EXECUTANDO] {script_name}...\n")

    def thread_func():
        process = subprocess.Popen(
            f'"{script_path}"',
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True
        )

        script_log_path = os.path.join(LOG_DIR, f"{script_name}.log")
        with open(script_log_path, "a", encoding="utf-8") as script_log:
            for line in process.stdout:
                clean_line = line.strip()
                log(clean_line)
                script_log.write(clean_line + "\n")

        process.stdout.close()
        process.wait()
        log(f"[FINALIZADO] {script_name} (código {process.returncode})\n")

    threading.Thread(target=thread_func, daemon=True).start()

def log(message):
    timestamp = datetime.now().strftime("[%Y-%m-%d %H:%M:%S]")
    full_message = f"{timestamp} {message}"

    terminal.configure(state="normal")
    terminal.insert(tk.END, full_message + "\n")
    terminal.see(tk.END)
    terminal.configure(state="disabled")

    log_file_path = os.path.join(LOG_DIR, "interface_log.txt")
    with open(log_file_path, "a", encoding="utf-8") as f:
        f.write(full_message + "\n")

def limpar_logs():
    terminal.configure(state="normal")
    terminal.delete("1.0", tk.END)
    terminal.configure(state="disabled")

root = tk.Tk()
root.title("Painel de Scripts WSL")
root.geometry("650x500")
root.configure(bg="#1e1e2f")  

frame = tk.Frame(root, bg="#1e1e2f")
frame.pack(pady=20)

botao_style = {
    "bg": "#6a0dad",      # Roxo
    "fg": "white",        # Texto branco
    "activebackground": "#8a2be2",
    "activeforeground": "white",
    "width": 40,
    "font": ("Segoe UI", 10, "bold"),
    "bd": 0,
    "relief": tk.FLAT,
    "cursor": "hand2"
}

scripts = [
    ("Ativar WSL", "ativarwsl.exe"),
    ("Desativar WSL", "desativarwsl.exe"),
    ("Python No Update", "pythonnoupdate.exe")
]

for label, filename in scripts:
    tk.Button(frame, text=label, command=lambda f=filename: run_script(f), **botao_style).pack(pady=5)

tk.Button(root, text="🧹 Limpar Logs", command=limpar_logs, **botao_style).pack(pady=10)

terminal = scrolledtext.ScrolledText(root, height=15, state="disabled", font=("Courier", 10), bg="#2d2d3a", fg="white", insertbackground="white")
terminal.pack(fill=tk.BOTH, padx=10, pady=10, expand=True)

root.mainloop()
