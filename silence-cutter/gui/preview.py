import customtkinter as ctk

from gui.stats_panel import StatsPanel
from gui.progress_panel import ProgressPanel
from gui.log_panel import LogPanel
from gui.result_panel import ResultPanel


class PreviewPanel(ctk.CTkFrame):
    """Container principal que orquestra stats, progresso, log e resultado."""

    def __init__(self, master):
        super().__init__(master, fg_color="#0d0d1a", corner_radius=8)

        self.grid_rowconfigure(3, weight=1)  # log expands
        self.grid_columnconfigure(0, weight=1)

        # Create sub-panels
        self._stats_panel = StatsPanel(self)
        self._stats_panel.grid(row=0, column=0, padx=16, pady=(16, 8), sticky="ew")

        self._progress_panel = ProgressPanel(self)
        self._progress_panel.grid(row=1, column=0, padx=16, pady=(8, 4), sticky="ew")

        self._info_frame = self._build_info()
        # not gridded initially

        self._log_panel = LogPanel(self)
        self._log_panel.grid(row=3, column=0, padx=16, pady=(4, 8), sticky="nsew")

        self._result_panel = ResultPanel(self)
        # initially hidden

    # ── Info (mantido no PreviewPanel pois é coordenado com progress) ──

    def _build_info(self):
        frame = ctk.CTkFrame(self, fg_color="#151528", corner_radius=8)
        frame.grid_columnconfigure((0, 1, 2), weight=1)

        self._info_name = self._info_column(frame, 0, "Arquivo", "#ccc")
        self._info_size = self._info_column(frame, 1, "Tamanho", "#ccc")
        self._info_format = self._info_column(frame, 2, "Formato", "#ccc")

        return frame

    def _info_column(self, parent, col, label, color):
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.grid(row=0, column=col, padx=12, pady=8)

        val = ctk.CTkLabel(
            frame, text="—",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=color,
        )
        val.pack()

        ctk.CTkLabel(
            frame, text=label,
            font=ctk.CTkFont(size=10),
            text_color="#666",
        ).pack()

        return val

    def show_info(self, name: str, size: str, format_ext: str):
        """Show video file info."""
        self._info_name.configure(text=name)
        self._info_size.configure(text=size)
        self._info_format.configure(text=format_ext.upper())
        self._info_frame.grid(row=2, column=0, padx=16, pady=(4, 4), sticky="ew")
        # Shift log down when info is shown
        self._log_panel.grid(row=4, column=0, padx=16, pady=(4, 8), sticky="nsew")

    def hide_info(self):
        """Hide info section."""
        self._info_frame.grid_forget()
        # Reset log position when info is hidden
        self._log_panel.grid(row=3, column=0, padx=16, pady=(4, 8), sticky="nsew")

    # ── Stats (delegated to StatsPanel) ───────────────────────────

    def update_stats(self, original: float, estimated: float, removed: float):
        self._stats_panel.update_stats(original, estimated, removed)

    # ── Progress (delegated to ProgressPanel) ─────────────────────

    def update_progress(self, percent: float, message: str = ""):
        self._progress_panel.update_progress(percent, message)

    def reset_progress(self):
        self._progress_panel.reset_progress()

    # ── Loading (delegated to ProgressPanel) ──────────────────────

    def show_loading(self, message: str = "Analisando..."):
        self._progress_panel.show_loading(message)

    def hide_loading(self):
        self._progress_panel.hide_loading()

    # ── Batch Progress (delegated to ProgressPanel) ───────────────

    def show_batch_progress(self, current: int, total: int):
        self._progress_panel.show_batch_progress(current, total)

    def hide_batch_progress(self):
        self._progress_panel.hide_batch_progress()

    def update_batch_progress(self, current: int, total: int):
        self._progress_panel.update_batch_progress(current, total)

    # ── Log (delegated to LogPanel) ───────────────────────────────

    def append_log(self, line: str, level: str = "INFO"):
        self._log_panel.append_log(line, level)

    def clear_log(self):
        self._log_panel.clear_log()

    # ── Result (delegated to ResultPanel) ─────────────────────────

    def show_result(self, output_path: str):
        self._result_panel.show_result(output_path)
        self._result_panel.grid(row=5, column=0, padx=16, pady=(4, 16), sticky="ew")

    def hide_result(self):
        self._result_panel.hide_result()
        self._result_panel.grid_forget()

    # ── Helpers ───────────────────────────────────────────────────

    @staticmethod
    def _fmt_time(seconds: float) -> str:
        """Format seconds as time string."""
        return StatsPanel._fmt_time(seconds)
