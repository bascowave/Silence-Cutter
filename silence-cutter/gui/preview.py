import customtkinter as ctk


class PreviewPanel(ctk.CTkFrame):
    """Painel principal: stats, progresso, log e resultado."""

    def __init__(self, master):
        super().__init__(master, fg_color="#0d0d1a", corner_radius=8)

        self.grid_rowconfigure(3, weight=1)  # log expands
        self.grid_columnconfigure(0, weight=1)

        self._build_stats()
        self._build_progress()
        self._build_log()
        self._build_result()

    # ── Stats ─────────────────────────────────────────────────────

    def _build_stats(self):
        frame = ctk.CTkFrame(self, fg_color="#151528", corner_radius=8)
        frame.grid(row=0, column=0, padx=16, pady=(16, 8), sticky="ew")
        frame.grid_columnconfigure((0, 1, 2), weight=1)

        self._stat_original = self._stat_column(frame, 0, "Original", "#ffffff")
        self._stat_estimated = self._stat_column(frame, 1, "Após corte", "#6c5ce7")
        self._stat_removed = self._stat_column(frame, 2, "Silêncio removido", "#e74c3c")

    def _stat_column(self, parent, col, label, color):
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.grid(row=0, column=col, padx=12, pady=12)

        val = ctk.CTkLabel(
            frame, text="—",
            font=ctk.CTkFont(size=24, weight="bold"),
            text_color=color,
        )
        val.pack()

        ctk.CTkLabel(
            frame, text=label,
            font=ctk.CTkFont(size=11),
            text_color="#888",
        ).pack()

        return val

    def update_stats(self, original: float, estimated: float, removed: float):
        self._stat_original.configure(text=self._fmt_time(original))
        self._stat_estimated.configure(text=self._fmt_time(estimated))
        self._stat_removed.configure(text=self._fmt_time(removed))

    # ── Progress ──────────────────────────────────────────────────

    def _build_progress(self):
        frame = ctk.CTkFrame(self, fg_color="transparent")
        frame.grid(row=1, column=0, padx=16, pady=(8, 4), sticky="ew")
        frame.grid_columnconfigure(0, weight=1)

        self._progress_bar = ctk.CTkProgressBar(
            frame, progress_color="#6c5ce7", fg_color="#2d2d44",
            height=12, corner_radius=6,
        )
        self._progress_bar.grid(row=0, column=0, sticky="ew")
        self._progress_bar.set(0)

        self._lbl_progress = ctk.CTkLabel(
            frame, text="0% — Aguardando...",
            font=ctk.CTkFont(size=11), text_color="#888",
        )
        self._lbl_progress.grid(row=1, column=0, pady=(4, 0))

    def update_progress(self, percent: float, message: str = ""):
        self._progress_bar.set(percent / 100.0)
        msg = message or f"{percent:.0f}%"
        self._lbl_progress.configure(text=msg)

    def reset_progress(self):
        self._progress_bar.set(0)
        self._lbl_progress.configure(text="0% — Aguardando...")

    # ── Log ───────────────────────────────────────────────────────

    def _build_log(self):
        self._log = ctk.CTkTextbox(
            self, fg_color="#0a0a18", text_color="#aaa",
            font=ctk.CTkFont(family="Consolas", size=12),
            state="disabled", corner_radius=8,
        )
        self._log.grid(row=3, column=0, padx=16, pady=(4, 8), sticky="nsew")

    _LOG_COLORS = {"INFO": "#6c5ce7", "WARN": "#e8a838", "ERROR": "#e74c3c"}

    def append_log(self, line: str, level: str = "INFO"):
        tag = f"log_{level}"
        color = self._LOG_COLORS.get(level, "#aaa")
        self._log.configure(state="normal")
        self._log.tag_config(tag, foreground=color)
        self._log.insert("end", line + "\n", tag)
        self._log.see("end")
        self._log.configure(state="disabled")

    def clear_log(self):
        self._log.configure(state="normal")
        self._log.delete("1.0", "end")
        self._log.configure(state="disabled")

    # ── Result ────────────────────────────────────────────────────

    def _build_result(self):
        self._result_frame = ctk.CTkFrame(
            self, fg_color="#1a3a1a", border_color="#2d6b2d",
            border_width=1, corner_radius=8,
        )
        # initially hidden

        self._lbl_result = ctk.CTkLabel(
            self._result_frame, text="",
            font=ctk.CTkFont(size=13), text_color="#4ade80",
            wraplength=400,
        )
        self._lbl_result.pack(padx=16, pady=(12, 4))

        self._btn_open_folder = ctk.CTkButton(
            self._result_frame, text="Abrir Pasta",
            fg_color="#2d6b2d", hover_color="#3d8b3d",
            width=120,
        )
        self._btn_open_folder.pack(pady=(4, 12))

    def show_result(self, output_path: str):
        import os
        self._lbl_result.configure(
            text=f"Concluído!\n{output_path}"
        )
        self._btn_open_folder.configure(
            command=lambda: os.startfile(os.path.dirname(output_path))
        )
        self._result_frame.grid(row=4, column=0, padx=16, pady=(4, 16),
                                sticky="ew")

    def hide_result(self):
        self._result_frame.grid_forget()

    # ── Helpers ───────────────────────────────────────────────────

    @staticmethod
    def _fmt_time(seconds: float) -> str:
        if seconds <= 0:
            return "—"
        m, s = divmod(int(seconds), 60)
        h, m = divmod(m, 60)
        if h > 0:
            return f"{h}:{m:02d}:{s:02d}"
        return f"{m}:{s:02d}"
