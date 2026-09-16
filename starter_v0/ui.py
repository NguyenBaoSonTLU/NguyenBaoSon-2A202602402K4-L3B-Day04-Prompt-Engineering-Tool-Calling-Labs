"""Run with: python starter_v0/ui.py (API keys are read from starter_v0/.env)."""
from __future__ import annotations

import queue
import json
import os
import threading
import tkinter as tk
from datetime import datetime
from tkinter import messagebox, ttk
from tkinter.scrolledtext import ScrolledText

from chat import (
    ARTIFACTS_DIR, ROOT, artifact_version_dict, build_artifact_version,
    json_text, load_tool_declarations, make_provider, now_iso,
    run_model_tool_loop, safe_slug, to_openai_tools, trim_history,
    write_transcript,
)


class HelpdeskUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("IT Helpdesk · Trợ lý AI")
        self.geometry("1100x760")
        self.minsize(820, 580)
        self.configure(bg="#eef2f7")
        self.events = queue.Queue()
        self.busy = False
        self.session = None
        self.history = []
        self.provider_name = tk.StringVar(value="openai")
        self.model_name = tk.StringVar()
        self.version_name = tk.StringVar(value="v4")
        self.status = tk.StringVar(value="Điền API key trong starter_v0/.env trước khi gửi tin nhắn.")
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("TFrame", background="#eef2f7")
        style.configure("TLabel", background="#eef2f7", font=("Segoe UI", 10))
        style.configure("TButton", font=("Segoe UI", 10), padding=8)
        outer = ttk.Frame(self, padding=20)
        outer.pack(fill="both", expand=True)
        ttk.Label(outer, text="IT Helpdesk", font=("Segoe UI", 24, "bold")).pack(anchor="w")
        ttk.Label(outer, text="Chat với trợ lý • Theo dõi công cụ • Lưu hội thoại JSON").pack(anchor="w", pady=(0, 16))
        config = ttk.Frame(outer)
        config.pack(fill="x", pady=(0, 12))
        self.fields = []
        for label, variable, values, width in [
            ("Provider", self.provider_name, ["openrouter", "openai", "anthropic", "gemini"], 16),
            ("Model (trống = mặc định)", self.model_name, None, 28),
            ("Version", self.version_name, None, 12),
        ]:
            box = ttk.Frame(config)
            box.pack(side="left", padx=(0, 12))
            ttk.Label(box, text=label).pack(anchor="w")
            field = ttk.Combobox(box, textvariable=variable, values=values, state="readonly", width=width) if values else ttk.Entry(box, textvariable=variable, width=width)
            field.pack(pady=(4, 0))
            self.fields.append(field)
        self.new_button = ttk.Button(config, text="Hội thoại mới", command=self.new_session)
        self.new_button.pack(side="right", anchor="s")
        panes = ttk.Panedwindow(outer, orient="horizontal")
        panes.pack(fill="both", expand=True)
        self.chat = self.make_panel(panes, "Hội thoại", 3)
        self.trace = self.make_panel(panes, "Tool call / Input / Kết quả / Lỗi", 2)
        self.chat.tag_configure("user", foreground="#1d4ed8", font=("Segoe UI", 11, "bold"))
        self.chat.tag_configure("assistant", foreground="#047857", font=("Segoe UI", 11, "bold"))
        self.chat.tag_configure("error", foreground="#b91c1c")
        self.input = tk.Text(outer, height=3, wrap="word", font=("Segoe UI", 11), relief="flat", padx=12, pady=10)
        self.input.pack(fill="x", pady=(12, 8))
        self.input.bind("<Return>", self.on_enter)
        bottom = ttk.Frame(outer)
        bottom.pack(fill="x")
        ttk.Label(bottom, text="Enter để gửi · Shift+Enter để xuống dòng").pack(side="left")
        self.send_button = ttk.Button(bottom, text="Gửi tin nhắn →", command=self.send)
        self.send_button.pack(side="right")
        ttk.Button(bottom, text="Lưu lại JSON", command=self.save_session).pack(side="right", padx=8)
        ttk.Label(outer, textvariable=self.status, wraplength=1000).pack(anchor="w", pady=(10, 0))
        self.protocol("WM_DELETE_WINDOW", self.close)
        self.after(100, self.poll)
        self.input.focus_set()

    def make_panel(self, panes, title, weight):
        frame = ttk.Frame(panes)
        ttk.Label(frame, text=title, font=("Segoe UI", 11, "bold")).pack(anchor="w", pady=(0, 8))
        text = ScrolledText(frame, wrap="word", state="disabled", font=("Segoe UI", 11), relief="flat", padx=12, pady=12, width=35)
        text.pack(fill="both", expand=True)
        panes.add(frame, weight=weight)
        return text

    @staticmethod
    def append(widget, text, tag=None):
        widget.configure(state="normal")
        widget.insert("end", text, tag or ())
        widget.configure(state="disabled")
        widget.see("end")

    def on_enter(self, event):
        if event.state & 1:
            return None
        self.send()
        return "break"

    def new_session(self):
        if self.busy:
            return
        if self.session and not self.save_session():
            return
        self.session = None
        self.history = []
        self.input.delete("1.0", "end")
        for widget in (self.chat, self.trace):
            widget.configure(state="normal")
            widget.delete("1.0", "end")
            widget.configure(state="disabled")
        for index, field in enumerate(self.fields):
            field.configure(state="readonly" if index == 0 else "normal")
        self.status.set("Hội thoại mới. Các hội thoại trước đã được lưu trong thư mục transcripts.")

    def start_session(self):
        prompt_path = ARTIFACTS_DIR / "system_prompt.md"
        tools_path = ARTIFACTS_DIR / "tools.yaml"
        key_name = {"openai": "OPENAI_API_KEY", "openrouter": "OPENROUTER_API_KEY",
                    "anthropic": "ANTHROPIC_API_KEY", "gemini": "GEMINI_API_KEY"}[self.provider_name.get()]
        if not os.getenv(key_name):
            raise ValueError(f"Thiếu {key_name}. Điền vào starter_v0/.env rồi mở lại UI.")
        provider = make_provider(self.provider_name.get())
        model = self.model_name.get().strip() or None
        version = build_artifact_version(self.version_name.get().strip() or "v0", prompt_path, tools_path)
        session_id = f"{safe_slug(version.version)}_{self.provider_name.get()}_{datetime.now():%Y%m%dT%H%M%S%f}"
        transcript = {
            "transcript_id": session_id, **artifact_version_dict(version),
            "provider": self.provider_name.get(), "model": model or getattr(provider, "default_model", None),
            "system_prompt": str(prompt_path), "tools": str(tools_path),
            "history_window": 5, "max_tool_rounds": 4,
            "interface": "tkinter_ui",
            "created_at": now_iso(), "turns": [],
        }
        self.session = dict(provider=provider, model=model,
                            prompt=prompt_path.read_text(encoding="utf-8"),
                            tools=to_openai_tools(load_tool_declarations(tools_path)),
                            transcript=transcript, path=ROOT / "transcripts" / f"{session_id}.transcript.json")
        self.append(self.trace, f"Version: {version.artifact_version}\nModel: {transcript['model']}\n\n")
        for field in self.fields:
            field.configure(state="disabled")

    def send(self):
        text = self.input.get("1.0", "end").strip()
        if self.busy or not text:
            return
        try:
            if self.session is None:
                self.start_session()
        except Exception as exc:
            messagebox.showerror("Không thể khởi tạo", str(exc))
            return
        self.input.delete("1.0", "end")
        self.append(self.chat, "Bạn\n", "user")
        self.append(self.chat, text + "\n\n")
        self.busy = True
        self.send_button.configure(state="disabled")
        self.new_button.configure(state="disabled")
        self.status.set("Đang xử lý…")
        messages = [{"role": "system", "content": self.session["prompt"]},
                    *trim_history(self.history, 5), {"role": "user", "content": text}]
        threading.Thread(target=self.run_turn, args=(text, messages), daemon=True).start()

    def run_turn(self, text, messages):
        session = self.session
        record = {"turn_index": len(session["transcript"]["turns"]) + 1,
                  "started_at": now_iso(), "user": text, "rounds": [], "tool_events": []}
        try:
            record.update(run_model_tool_loop(provider=session["provider"], messages=messages,
                                             tools=session["tools"], model=session["model"], max_tool_rounds=4))
        except Exception as exc:
            record.update(status="provider_error", error=f"{type(exc).__name__}: {exc}")
        record["ended_at"] = now_iso()
        session["transcript"]["turns"].append(record)
        save_error = None
        try:
            write_transcript(session["path"], session["transcript"])
        except Exception as exc:
            save_error = str(exc)
        self.events.put((record, save_error))

    def poll(self):
        try:
            record, save_error = self.events.get_nowait()
        except queue.Empty:
            pass
        else:
            answer = record.get("assistant_text") or record.get("error") or "Không có nội dung trả lời."
            display_answer = answer
            try:
                structured = json.loads(answer)
                if isinstance(structured, dict) and isinstance(structured.get("reply"), str):
                    display_answer = structured["reply"]
            except (ValueError, TypeError):
                pass
            self.append(self.chat, "Trợ lý\n", "assistant")
            self.append(self.chat, display_answer + "\n\n", "error" if record["status"] == "provider_error" else None)
            if record["status"] != "provider_error":
                self.history.extend([{"role": "user", "content": record["user"]}, {"role": "assistant", "content": answer}])
            self.append(self.trace, f"Lượt {record['turn_index']} · {record['status']}\n{json_text(record)}\n\n")
            self.status.set(f"Lỗi lưu hội thoại: {save_error}" if save_error else f"Đã lưu: {self.session['path']}")
            self.busy = False
            self.send_button.configure(state="normal")
            self.new_button.configure(state="normal")
        self.after(100, self.poll)

    def save_session(self):
        if not self.session or self.busy:
            return False
        try:
            write_transcript(self.session["path"], self.session["transcript"])
        except Exception as exc:
            messagebox.showerror("Không lưu được hội thoại", str(exc))
            return False
        self.status.set(f"Đã lưu: {self.session['path']}")
        return True

    def close(self):
        if self.busy:
            messagebox.showinfo("Đang xử lý", "Vui lòng đợi phản hồi và lưu hội thoại xong trước khi đóng.")
            return
        if self.session and not self.save_session():
            return
        self.destroy()


if __name__ == "__main__":
    HelpdeskUI().mainloop()
