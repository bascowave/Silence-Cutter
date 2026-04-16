import customtkinter as ctk


class ProgressPanel(ctk.CTkFrame):
    """Painel de progresso, loading e batch progress."""

    def __init__(self, master):
        super().__init__(master, fg_color="transparent")

        self.grid_columnconfigure(0, weight=1)

        self._build_batch_progress()
        self._build_loading()
        self._build_progress()

    # ── Batch Progress ────────────────────────────────────────────

    def _build_batch_progress(self):
        """Build batch progress section (for multi-file processing)."""
        self._batch_frame = ctk.CTkFrame(self, fg_color="transparent")
        # Not gridded initially - only shown during batch processing

        self._batch_frame.grid_columnconfigure(0, weight=1)

        # Batch progress label: "Arquivo 2/5"
        self._lbl_batch_progress = ctk.CTkLabel(
            self._batch_frame, text="",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#6c5ce7",
        )
        self._lbl_batch_progress.grid(row=0, column=0, pady=(0, 4))

        # Overall progress bar for batch
        self._batch_progress_bar = ctk.CTkProgressBar(
            self._batch_frame, progress_color="#4ade80",
            fg_color="#2d2d44",
            height=8, corner_radius=4,
        )
        self._batch_progress_bar.grid(row=1, column=0, sticky="ew")
        self._batch_progress_bar.set(0)

    def show_batch_progress(self, current: int, total: int):
        """Show batch progress UI with 'Arquivo X/N' label."""
        self._lbl_batch_progress.configure(text=f"Arquivo {current}/{total}")
        self._batch_progress_bar.set((current - 1) / total if total > 0 else 0)
        self._batch_frame.grid(row=0, column=0, padx=0, pady=(0, 8), sticky="ew")

    def hide_batch_progress(self):
        """Hide batch progress UI."""
        self._batch_frame.grid_forget()

    def update_batch_progress(self, current: int, total: int):
        """Update batch progress values."""
        self._lbl_batch_progress.configure(text=f"Arquivo {current}/{total}")
        self._batch_progress_bar.set(current / total if total > 0 else 0)

    # ── Loading ───────────────────────────────────────────────────

    def _build_loading(self):
        self._loading_frame = ctk.CTkFrame(self, fg_color="transparent")
        # not gridded initially

        self._loading_bar = ctk.CTkProgressBar(
            self._loading_frame, progress_color="#6c5ce7", fg_color="#2d2d44",
            height=8, corner_radius=4, mode="indeterminate",
        )
        self._loading_bar.grid(row=0, column=0, sticky="ew")

        self._loading_label = ctk.CTkLabel(
            self._loading_frame, text="Analisando...",
            font=ctk.CTkFont(size=11), text_color="#888",
        )
        self._loading_label.grid(row=1, column=0, pady=(4, 0))

    def show_loading(self, message: str = "Analisando..."):
        """Show indeterminate loading bar with message."""
        self._loading_label.configure(text=message)
        self._loading_bar.configure(mode="indeterminate")
        self._loading_bar.start()
        self._loading_frame.grid(row=1, column=0, padx=0, pady=(0, 8), sticky="ew")

    def hide_loading(self):
        """Hide loading bar."""
        self._loading_bar.stop()
        self._loading_frame.grid_forget()

    # ── Progress ──────────────────────────────────────────────────

    def _build_progress(self):
        self._progress_frame = ctk.CTkFrame(self, fg_color="transparent")
        self._progress_frame.grid(row=2, column=0, padx=0, pady=(0, 0), sticky="ew")
        self._progress_frame.grid_columnconfigure(0, weight=1)

        self._progress_bar = ctk.CTkProgressBar(
            self._progress_frame, progress_color="#6c5ce7", fg_color="#2d2d44",
            height=12, corner_radius=6,
        )
        self._progress_bar.grid(row=0, column=0, sticky="ew")
        self._progress_bar.set(0)

        self._lbl_progress = ctk.CTkLabel(
            self._progress_frame, text="0% — Aguardando...",
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
