import customtkinter as ctk


class StatsPanel(ctk.CTkFrame):
    """Painel de estatísticas de duração do vídeo."""

    def __init__(self, master):
        super().__init__(master, fg_color="#151528", corner_radius=8)

        self.grid_columnconfigure((0, 1, 2), weight=1)

        self._stat_original = self._stat_column(0, "Original", "#ffffff")
        self._stat_estimated = self._stat_column(1, "Após corte", "#6c5ce7")
        self._stat_removed = self._stat_column(2, "Silêncio removido", "#e74c3c")

    def _stat_column(self, col, label, color):
        frame = ctk.CTkFrame(self, fg_color="transparent")
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

    @staticmethod
    def _fmt_time(seconds: float) -> str:
        if seconds <= 0:
            return "0:00"
        m, s = divmod(int(seconds), 60)
        h, m = divmod(m, 60)
        if h > 0:
            return f"{h}:{m:02d}:{s:02d}"
        return f"{m}:{s:02d}"
