"""
╔══════════════════════════════════════════════════════════════════╗
║         WSL NEXUS — OS AGENT v2.0 (Groq Edition)               ║
║         IA que controla seu sistema operacional                 ║
║         Akira (Felipe) | 2026                                   ║
╚══════════════════════════════════════════════════════════════════╝

Dependências:
    uv pip install customtkinter groq psutil
    ou:
    pip install customtkinter groq psutil --break-system-packages

Como usar:
    1. Pegue sua API Key GRATUITA em: https://console.groq.com
    2. Cole no campo da interface (ou defina GROQ_API_KEY no ambiente)
    3. python os_agent.py
"""

import tkinter as tk
import customtkinter as ctk
import subprocess
import threading
import os
import sys
import json
import psutil
import platform
import shutil
import time
from pathlib import Path
from datetime import datetime
from groq import Groq

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

COLORS = {
    "bg":      "#0a0a12",
    "panel":   "#11111c",
    "card":    "#18182a",
    "accent":  "#7c3aed",
    "cyan":    "#06b6d4",
    "green":   "#10b981",
    "red":     "#ef4444",
    "yellow":  "#f59e0b",
    "text":    "#e2e8f0",
    "dim":     "#475569",
    "border":  "#2a2a42",
    "user_bg": "#1e1b4b",
    "ai_bg":   "#0f2027",
    "sys_bg":  "#0f1f14",
    "err_bg":  "#2d0f0f",
}

GROQ_MODEL = "llama-3.3-70b-versatile"

# ── Tools no formato OpenAI/Groq ──────────────────────────────────────────────
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "executar_comando",
            "description": (
                "Executa um comando PowerShell ou CMD no Windows do usuario. "
                "Use para abrir programas (Start-Process), criar arquivos, "
                "listar processos, obter informacoes do sistema, etc."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "comando": {"type": "string", "description": "Comando PowerShell ou CMD"},
                    "shell":   {"type": "string", "enum": ["powershell", "cmd"]},
                    "aguardar":{"type": "boolean", "description": "false para abrir apps, true para comandos que retornam dados"}
                },
                "required": ["comando"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "gerenciar_processo",
            "description": "Lista, encerra ou verifica processos em execucao.",
            "parameters": {
                "type": "object",
                "properties": {
                    "acao": {"type": "string", "enum": ["listar", "encerrar", "verificar"]},
                    "nome": {"type": "string", "description": "Nome do processo (ex: spotify.exe)"}
                },
                "required": ["acao"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "gerenciar_arquivos",
            "description": "Cria, lista, move, copia, deleta ou abre arquivos e pastas. Use %DESKTOP%, %DOCUMENTS%, %DOWNLOADS% como atalhos.",
            "parameters": {
                "type": "object",
                "properties": {
                    "acao":    {"type": "string", "enum": ["criar_pasta", "listar", "deletar", "mover", "copiar", "abrir"]},
                    "caminho": {"type": "string"},
                    "destino": {"type": "string"}
                },
                "required": ["acao", "caminho"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "info_sistema",
            "description": "Retorna informacoes do sistema: CPU, RAM, disco, rede, bateria, uptime, processos.",
            "parameters": {
                "type": "object",
                "properties": {
                    "tipo": {"type": "string", "enum": ["geral","cpu","ram","disco","rede","bateria","processos","usuarios"]}
                },
                "required": ["tipo"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "controle_volume",
            "description": "Controla o volume do sistema: mutar, desmutar, aumentar, diminuir ou definir valor.",
            "parameters": {
                "type": "object",
                "properties": {
                    "acao":  {"type": "string", "enum": ["mutar","desmutar","aumentar","diminuir","definir"]},
                    "valor": {"type": "integer", "description": "0-100 so para acao definir"}
                },
                "required": ["acao"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "controle_sistema",
            "description": "Controla o sistema: desligar, reiniciar, suspender, bloquear tela, limpar lixeira.",
            "parameters": {
                "type": "object",
                "properties": {
                    "acao":           {"type": "string", "enum": ["desligar","reiniciar","suspender","bloquear","limpar_lixeira","cancelar_desligamento"]},
                    "delay_segundos": {"type": "integer"}
                },
                "required": ["acao"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "wsl_controle",
            "description": "Controla o WSL: listar distros, iniciar, parar, executar comandos bash.",
            "parameters": {
                "type": "object",
                "properties": {
                    "acao":    {"type": "string", "enum": ["listar","iniciar","parar","shutdown","executar_comando"]},
                    "distro":  {"type": "string"},
                    "comando": {"type": "string"}
                },
                "required": ["acao"]
            }
        }
    }
]


# ── Executor ──────────────────────────────────────────────────────────────────
class OSExecutor:
    SPECIAL_PATHS = {
        "%DESKTOP%":   Path.home() / "Desktop",
        "%DOCUMENTS%": Path.home() / "Documents",
        "%DOWNLOADS%": Path.home() / "Downloads",
        "%PICTURES%":  Path.home() / "Pictures",
        "%MUSIC%":     Path.home() / "Music",
        "%VIDEOS%":    Path.home() / "Videos",
        "%HOME%":      Path.home(),
        "%TEMP%":      Path(os.environ.get("TEMP", "/tmp")),
    }

    def resolve_path(self, p):
        for k, v in self.SPECIAL_PATHS.items():
            p = p.replace(k, str(v))
        return Path(p)

    def run(self, name, args):
        try:
            fn = getattr(self, f"_tool_{name}", None)
            return fn(args) if fn else f"Ferramenta '{name}' nao implementada."
        except Exception as e:
            return f"[ERRO] {e}"

    def _flags(self):
        return subprocess.CREATE_NO_WINDOW if hasattr(subprocess, "CREATE_NO_WINDOW") else 0

    def _tool_executar_comando(self, inp):
        cmd      = inp["comando"]
        shell    = inp.get("shell", "powershell")
        aguardar = inp.get("aguardar", True)
        full = (["powershell", "-NoProfile", "-NonInteractive", "-Command", cmd]
                if shell == "powershell" else ["cmd", "/c", cmd])
        if aguardar:
            r = subprocess.run(full, capture_output=True, text=True,
                               timeout=30, encoding="utf-8", errors="replace",
                               creationflags=self._flags())
            return (r.stdout + r.stderr).strip() or "(executado sem saida)"
        subprocess.Popen(full, creationflags=self._flags())
        return f"Iniciado: {cmd}"

    def _tool_gerenciar_processo(self, inp):
        acao = inp["acao"]
        nome = inp.get("nome", "").lower()
        if acao == "listar":
            rows = []
            for p in psutil.process_iter(["pid","name","cpu_percent","memory_percent"]):
                try:
                    rows.append(f"PID {p.info['pid']:>6} | {p.info['name']:<30} | "
                                f"CPU {p.info['cpu_percent']:>5.1f}% | RAM {p.info['memory_percent']:>4.1f}%")
                except Exception:
                    pass
            return "\n".join(sorted(rows)[:30])
        elif acao == "encerrar":
            killed = []
            for p in psutil.process_iter(["pid","name"]):
                try:
                    if nome in p.info["name"].lower():
                        p.terminate(); killed.append(p.info["name"])
                except Exception:
                    pass
            return f"Encerrado: {', '.join(killed)}" if killed else f"'{nome}' nao encontrado."
        elif acao == "verificar":
            found = {p.info["name"] for p in psutil.process_iter(["name"]) if nome in p.info["name"].lower()}
            return f"Rodando: {', '.join(found)}" if found else f"'{nome}' nao esta rodando."

    def _tool_gerenciar_arquivos(self, inp):
        acao    = inp["acao"]
        caminho = self.resolve_path(inp["caminho"])
        destino = self.resolve_path(inp["destino"]) if inp.get("destino") else None
        if acao == "criar_pasta":
            caminho.mkdir(parents=True, exist_ok=True); return f"Pasta criada: {caminho}"
        elif acao == "listar":
            if not caminho.exists(): return f"Nao existe: {caminho}"
            items = [f"{'D' if i.is_dir() else 'F'} {i.name}" for i in sorted(caminho.iterdir())]
            return "\n".join(items) or "(vazio)"
        elif acao == "deletar":
            shutil.rmtree(caminho) if caminho.is_dir() else caminho.unlink()
            return f"Deletado: {caminho}"
        elif acao == "mover":
            shutil.move(str(caminho), str(destino)); return f"Movido: {caminho} -> {destino}"
        elif acao == "copiar":
            (shutil.copytree if caminho.is_dir() else shutil.copy2)(str(caminho), str(destino))
            return f"Copiado: {caminho} -> {destino}"
        elif acao == "abrir":
            os.startfile(str(caminho)); return f"Aberto: {caminho}"

    def _tool_info_sistema(self, inp):
        tipo = inp["tipo"]
        if tipo == "geral":
            up = time.time() - psutil.boot_time()
            h, m = divmod(int(up//60), 60)
            return (f"OS: {platform.system()} {platform.release()}\n"
                    f"Maquina: {platform.node()} | Usuario: {os.getlogin()}\n"
                    f"Uptime: {h}h {m}m\n"
                    f"Nucleos: {psutil.cpu_count(logical=False)} fisicos / {psutil.cpu_count()} logicos")
        elif tipo == "cpu":
            return f"CPU: {psutil.cpu_percent(interval=1):.1f}%"
        elif tipo == "ram":
            m = psutil.virtual_memory()
            return f"RAM: {m.used/1e9:.1f}/{m.total/1e9:.1f} GB ({m.percent}%) | Livre: {m.available/1e9:.1f} GB"
        elif tipo == "disco":
            lines = []
            for d in psutil.disk_partitions():
                try:
                    u = psutil.disk_usage(d.mountpoint)
                    lines.append(f"{d.device}: {u.used/1e9:.1f}/{u.total/1e9:.1f} GB ({u.percent}%)")
                except Exception:
                    pass
            return "\n".join(lines)
        elif tipo == "rede":
            lines = [f"{n}: {a.address}" for n,addrs in psutil.net_if_addrs().items()
                     for a in addrs if a.family.name == "AF_INET"]
            net = psutil.net_io_counters()
            return "\n".join(lines) + f"\nEnviado: {net.bytes_sent/1e6:.1f}MB | Recebido: {net.bytes_recv/1e6:.1f}MB"
        elif tipo == "bateria":
            b = psutil.sensors_battery()
            if not b: return "Sem bateria detectada."
            return f"{b.percent:.0f}% | {'Carregando' if b.power_plugged else 'Bateria'}"
        elif tipo == "processos":
            procs = sorted(psutil.process_iter(["pid","name","cpu_percent"]),
                           key=lambda p: p.info.get("cpu_percent") or 0, reverse=True)[:15]
            return "\n".join(f"PID {p.info['pid']:>6} | {p.info['name']:<30} | {p.info['cpu_percent']:.1f}%"
                             for p in procs)
        elif tipo == "usuarios":
            return "\n".join(f"{u.name} desde {datetime.fromtimestamp(u.started).strftime('%H:%M')}"
                             for u in psutil.users())

    def _tool_controle_volume(self, inp):
        acao  = inp["acao"]
        valor = inp.get("valor", 50)
        cmds  = {
            "mutar":    "$w=New-Object -Com WScript.Shell;$w.SendKeys([char]173)",
            "desmutar": "$w=New-Object -Com WScript.Shell;$w.SendKeys([char]173)",
            "aumentar": "$w=New-Object -Com WScript.Shell;1..5|%{$w.SendKeys([char]175)}",
            "diminuir": "$w=New-Object -Com WScript.Shell;1..5|%{$w.SendKeys([char]174)}",
            "definir":  (f"$w=New-Object -Com WScript.Shell;"
                         f"1..50|%{{$w.SendKeys([char]174)}};"
                         f"1..{valor//2}|%{{$w.SendKeys([char]175)}}"),
        }
        cmd = cmds.get(acao)
        if not cmd: return "Acao desconhecida."
        subprocess.Popen(["powershell","-NoProfile","-Command",cmd], creationflags=self._flags())
        return f"Volume: {acao}" + (f" -> {valor}%" if acao=="definir" else "")

    def _tool_controle_sistema(self, inp):
        acao  = inp["acao"]
        delay = inp.get("delay_segundos", 0)
        if acao == "limpar_lixeira":
            subprocess.run(["powershell","-Command","Clear-RecycleBin -Force -ErrorAction SilentlyContinue"],
                           capture_output=True)
            return "Lixeira limpa."
        cmds = {
            "desligar":              f"shutdown /s /t {delay}",
            "reiniciar":             f"shutdown /r /t {delay}",
            "suspender":             "rundll32.exe powrprof.dll,SetSuspendState 0,1,0",
            "bloquear":              "rundll32.exe user32.dll,LockWorkStation",
            "cancelar_desligamento": "shutdown /a",
        }
        cmd = cmds.get(acao)
        if not cmd: return f"Acao desconhecida: {acao}"
        subprocess.run(cmd, shell=True)
        msgs = {
            "desligar": f"PC desligara em {delay}s", "reiniciar": f"PC reiniciara em {delay}s",
            "suspender": "Suspendendo...", "bloquear": "Tela bloqueada.",
            "cancelar_desligamento": "Desligamento cancelado."
        }
        return msgs.get(acao, "Feito.")

    def _tool_wsl_controle(self, inp):
        acao   = inp["acao"]
        distro = inp.get("distro", "")
        cmd    = inp.get("comando", "")
        if acao == "listar":
            r = subprocess.run(["wsl","--list","--verbose"], capture_output=True,
                               text=True, encoding="utf-8", errors="replace")
            return r.stdout.replace("\x00","")
        elif acao == "iniciar":
            subprocess.Popen(["wsl","-d",distro,"--","bash"]); return f"WSL '{distro}' iniciado."
        elif acao == "parar":
            subprocess.run(["wsl","--terminate",distro], capture_output=True)
            return f"WSL '{distro}' encerrado."
        elif acao == "shutdown":
            subprocess.run(["wsl","--shutdown"], capture_output=True); return "WSL shutdown completo."
        elif acao == "executar_comando":
            r = subprocess.run(["wsl","-d",distro,"--","bash","-c",cmd],
                               capture_output=True, text=True,
                               encoding="utf-8", errors="replace", timeout=30)
            return r.stdout + r.stderr


# ── Agente IA ─────────────────────────────────────────────────────────────────
class OSAgent:
    def __init__(self, api_key):
        self.client   = Groq(api_key=api_key)
        self.executor = OSExecutor()
        self.history  = []
        self.system   = (
            f"Voce e um assistente de IA que controla o sistema operacional Windows do usuario.\n"
            f"OS: {platform.system()} {platform.release()} | Maquina: {platform.node()} | "
            f"Usuario: {os.getlogin()} | Hora: {datetime.now().strftime('%d/%m/%Y %H:%M')}\n\n"
            f"REGRAS:\n"
            f"- Responda SEMPRE em portugues do Brasil\n"
            f"- Execute imediatamente sem pedir confirmacao, exceto para acoes destrutivas\n"
            f"- Para abrir apps use: Start-Process <nome> no PowerShell\n"
            f"- Se falhar, tente uma abordagem alternativa\n"
            f"- Apps comuns: Spotify='spotify', Chrome='chrome', VSCode='code', Notepad='notepad'"
        )

    def chat(self, user_msg, on_tool=None, on_text=None):
        self.history.append({"role": "user", "content": user_msg})
        full = ""

        while True:
            resp = self.client.chat.completions.create(
                model=GROQ_MODEL,
                messages=[{"role": "system", "content": self.system}] + self.history,
                tools=TOOLS,
                tool_choice="auto",
                max_tokens=2048,
            )
            msg = resp.choices[0].message

            if msg.content:
                full += msg.content
                if on_text:
                    on_text(msg.content)

            # Salva a mensagem do assistente no histórico
            # Groq retorna um objeto, precisamos serializar para dict
            history_msg = {"role": "assistant", "content": msg.content or ""}
            if msg.tool_calls:
                history_msg["tool_calls"] = [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {"name": tc.function.name, "arguments": tc.function.arguments}
                    }
                    for tc in msg.tool_calls
                ]
            self.history.append(history_msg)

            tool_calls = msg.tool_calls or []
            if not tool_calls:
                break

            for tc in tool_calls:
                fn_name = tc.function.name
                fn_args = json.loads(tc.function.arguments)
                if on_tool:
                    on_tool(fn_name, fn_args)
                result = self.executor.run(fn_name, fn_args)
                self.history.append({
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "content": str(result),
                })

        return full

    def clear_history(self):
        self.history.clear()


# ── Interface ─────────────────────────────────────────────────────────────────
class OSAgentUI(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.agent = None
        self._busy = False
        self.title("WSL NEXUS — OS Agent  [Groq]")
        self.geometry("900x700")
        self.minsize(700, 500)
        self.configure(fg_color=COLORS["bg"])
        self._build_ui()
        self._load_api_key()

    def _build_ui(self):
        # Header
        hdr = ctk.CTkFrame(self, fg_color=COLORS["panel"], height=56, corner_radius=0)
        hdr.pack(fill="x"); hdr.pack_propagate(False)
        ctk.CTkLabel(hdr, text="⚡ OS AGENT", font=("JetBrains Mono",16,"bold"),
                     text_color=COLORS["accent"]).pack(side="left", padx=20, pady=12)
        ctk.CTkLabel(hdr, text="powered by GROQ", font=("JetBrains Mono",10),
                     text_color=COLORS["yellow"]).pack(side="left", padx=4)
        self.status_dot = ctk.CTkLabel(hdr, text="●  Offline",
                                        text_color=COLORS["dim"], font=("JetBrains Mono",11))
        self.status_dot.pack(side="left", padx=16)
        ctk.CTkButton(hdr, text="Limpar", width=70, height=30,
                      fg_color=COLORS["card"], text_color=COLORS["dim"],
                      hover_color=COLORS["border"], corner_radius=6,
                      font=("JetBrains Mono",10), command=self._clear_chat).pack(side="right", padx=8)

        # API bar
        api_bar = ctk.CTkFrame(self, fg_color=COLORS["card"], corner_radius=0, height=44)
        api_bar.pack(fill="x"); api_bar.pack_propagate(False)
        ctk.CTkLabel(api_bar, text="Groq API Key:", text_color=COLORS["dim"],
                     font=("JetBrains Mono",10)).pack(side="left", padx=12)
        self.api_entry = ctk.CTkEntry(api_bar, width=340, height=28, show="•",
                                       placeholder_text="gsk_...",
                                       font=("JetBrains Mono",11),
                                       fg_color=COLORS["bg"], border_color=COLORS["border"])
        self.api_entry.pack(side="left", padx=4)
        self.api_entry.bind("<Return>", lambda e: self._connect())
        ctk.CTkButton(api_bar, text="Conectar", width=80, height=28,
                      fg_color=COLORS["accent"], hover_color="#5b21b6",
                      text_color="white", corner_radius=6, font=("JetBrains Mono",10,"bold"),
                      command=self._connect).pack(side="left", padx=6)
        ctk.CTkButton(api_bar, text="👁", width=36, height=28,
                      fg_color=COLORS["card"], text_color=COLORS["dim"],
                      hover_color=COLORS["border"], corner_radius=6,
                      command=self._toggle_key).pack(side="left", padx=2)
        ctk.CTkLabel(api_bar, text="console.groq.com — gratis",
                     text_color=COLORS["dim"], font=("JetBrains Mono",9)).pack(side="right", padx=12)

        # Chat
        self.chat_frame = ctk.CTkScrollableFrame(self, fg_color=COLORS["bg"],
                                                  scrollbar_button_color=COLORS["accent"])
        self.chat_frame.pack(fill="both", expand=True)
        self._add_system_msg(
            "🤖  OS Agent pronto. Digite qualquer coisa e eu faço acontecer no seu PC.\n\n"
            "Exemplos:\n"
            "  • abre o spotify\n"
            "  • qual minha RAM disponível?\n"
            "  • cria uma pasta Projetos na área de trabalho\n"
            "  • fecha o chrome\n"
            "  • desliga o PC em 30 minutos\n"
            "  • roda no WSL: ls -la ~\n"
            "  • qual meu IP?\n"
            "  • muta o som"
        )

        # Input bar
        input_bar = ctk.CTkFrame(self, fg_color=COLORS["panel"], corner_radius=0, height=60)
        input_bar.pack(fill="x", side="bottom"); input_bar.pack_propagate(False)
        self.input_entry = ctk.CTkEntry(input_bar, height=36,
                                         placeholder_text="Digite um comando para o seu PC...",
                                         font=("JetBrains Mono",12), fg_color=COLORS["card"],
                                         border_color=COLORS["border"], text_color=COLORS["text"])
        self.input_entry.pack(side="left", fill="x", expand=True, padx=12, pady=12)
        self.input_entry.bind("<Return>", lambda e: self._send())
        self.send_btn = ctk.CTkButton(input_bar, text="Enviar ▶", width=90, height=36,
                                       fg_color=COLORS["accent"], hover_color="#5b21b6",
                                       text_color="white", corner_radius=8,
                                       font=("JetBrains Mono",11,"bold"), command=self._send)
        self.send_btn.pack(side="right", padx=(0,12))

    def _load_api_key(self):
        key = os.environ.get("GROQ_API_KEY", "")
        if not key:
            cfg = Path(__file__).parent / "agent_config.json"
            if cfg.exists():
                try:
                    key = json.loads(cfg.read_text(encoding="utf-8")).get("groq_api_key", "")
                except Exception:
                    pass
        if key:
            self.api_entry.insert(0, key)
            self._connect()

    def _toggle_key(self):
        self.api_entry.configure(show="" if self.api_entry.cget("show") == "•" else "•")

    def _connect(self):
        key = self.api_entry.get().strip()
        if not key:
            self._add_system_msg("⚠️  Cole sua Groq API Key.\nAcesse: https://console.groq.com", error=True)
            return
        try:
            self.agent = OSAgent(api_key=key)
            cfg = Path(__file__).parent / "agent_config.json"
            cfg.write_text(json.dumps({"groq_api_key": key}), encoding="utf-8")
            self.status_dot.configure(text=f"●  Online  [{GROQ_MODEL}]", text_color=COLORS["green"])
            self._add_system_msg(f"✓  Conectado via Groq! Modelo: {GROQ_MODEL}")
        except Exception as e:
            self._add_system_msg(f"Erro ao conectar: {e}", error=True)

    def _send(self):
        if self._busy: return
        if not self.agent:
            self._add_system_msg("⚠️  Conecte sua Groq API Key primeiro.", error=True); return
        msg = self.input_entry.get().strip()
        if not msg: return
        self.input_entry.delete(0, tk.END)
        self._add_user_msg(msg)
        self._busy = True
        self.send_btn.configure(state="disabled", text="...")
        threading.Thread(target=self._run_agent, args=(msg,), daemon=True).start()

    def _run_agent(self, msg):
        ai_ref = []

        def on_tool(name, args):
            labels = {
                "executar_comando":   f"💻 `{args.get('comando','')[:80]}`",
                "gerenciar_processo": f"⚙️  {args.get('acao','').upper()} → '{args.get('nome','')}'",
                "gerenciar_arquivos": f"📁 {args.get('acao','').upper()} → `{args.get('caminho','')}`",
                "info_sistema":       f"📊 coletando: {args.get('tipo','')}",
                "controle_volume":    f"🔊 volume: {args.get('acao','')}",
                "controle_sistema":   f"🖥  sistema: {args.get('acao','')}",
                "wsl_controle":       f"🐧 WSL: {args.get('acao','')}",
            }
            self.after(0, lambda t=labels.get(name, name): self._add_tool_msg(t))

        def on_text(chunk):
            if not ai_ref:
                self.after(0, lambda c=chunk: self._add_ai_bubble(c, ai_ref))

        try:
            self.agent.chat(msg, on_tool=on_tool, on_text=on_text)
        except Exception as e:
            self.after(0, lambda: self._add_system_msg(f"Erro: {e}", error=True))
        finally:
            self.after(0, self._done)

    def _done(self):
        self._busy = False
        self.send_btn.configure(state="normal", text="Enviar ▶")

    def _add_user_msg(self, text):
        b = ctk.CTkFrame(self.chat_frame, fg_color=COLORS["user_bg"], corner_radius=12,
                          border_width=1, border_color="#3730a3")
        b.pack(fill="x", padx=16, pady=(8,2))
        inner = ctk.CTkFrame(b, fg_color="transparent")
        inner.pack(fill="x", padx=14, pady=8)
        ctk.CTkLabel(inner, text="Você", text_color="#818cf8",
                     font=("JetBrains Mono",9,"bold")).pack(anchor="w")
        ctk.CTkLabel(inner, text=text, text_color=COLORS["text"],
                     font=("JetBrains Mono",12), wraplength=750, justify="left").pack(anchor="w")
        self._scroll_bottom()

    def _add_ai_bubble(self, text, ref):
        b = ctk.CTkFrame(self.chat_frame, fg_color=COLORS["ai_bg"], corner_radius=12,
                          border_width=1, border_color="#164e63")
        b.pack(fill="x", padx=16, pady=(2,2))
        inner = ctk.CTkFrame(b, fg_color="transparent")
        inner.pack(fill="x", padx=14, pady=8)
        ctk.CTkLabel(inner, text="🤖 OS Agent · Groq", text_color=COLORS["cyan"],
                     font=("JetBrains Mono",9,"bold")).pack(anchor="w")
        lbl = ctk.CTkLabel(inner, text=text, text_color=COLORS["text"],
                            font=("JetBrains Mono",12), wraplength=750, justify="left")
        lbl.pack(anchor="w")
        ref.append(lbl)
        self._scroll_bottom()

    def _add_tool_msg(self, text):
        b = ctk.CTkFrame(self.chat_frame, fg_color=COLORS["sys_bg"], corner_radius=8,
                          border_width=1, border_color="#14532d")
        b.pack(fill="x", padx=32, pady=1)
        ctk.CTkLabel(b, text=text, text_color=COLORS["green"],
                     font=("JetBrains Mono",10), anchor="w",
                     wraplength=720, justify="left").pack(anchor="w", padx=12, pady=6)
        self._scroll_bottom()

    def _add_system_msg(self, text, error=False):
        b = ctk.CTkFrame(self.chat_frame,
                          fg_color=COLORS["err_bg"] if error else COLORS["card"],
                          corner_radius=10, border_width=1,
                          border_color=COLORS["red"] if error else COLORS["border"])
        b.pack(fill="x", padx=16, pady=4)
        ctk.CTkLabel(b, text=text,
                     text_color=COLORS["red"] if error else COLORS["dim"],
                     font=("JetBrains Mono",10), wraplength=750, justify="left").pack(anchor="w", padx=14, pady=10)
        self._scroll_bottom()

    def _scroll_bottom(self):
        self.after(60, self.chat_frame._parent_canvas.yview_moveto, 1.0)

    def _clear_chat(self):
        for w in self.chat_frame.winfo_children(): w.destroy()
        if self.agent: self.agent.clear_history()
        self._add_system_msg("Chat limpo. Contexto resetado.")


if __name__ == "__main__":
    OSAgentUI().mainloop()
