import customtkinter as ctk


class LogPanel(ctk.CTkFrame):
    """Painel de log com cores por nível."""

    _LOG_COLORS = {"INFO": "#6c5ce7", "WARN": "#e8a838", "ERROR": "#e74c3c"}

    def __init__(self, master):
        super().__init__(master, fg_color="transparent")

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self._build_log()

    def _build_log(self):
        self._log = ctk.CTkTextbox(
            self, fg_color="#0a0a18", text_color="#aaa",
            font=ctk.CTkFont(family="Consolas", size=12),
            state="disabled", corner_radius=8,
        )
        self._log.grid(row=0, column=0, sticky="nsew")

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
