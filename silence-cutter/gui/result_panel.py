import customtkinter as ctk


class ResultPanel(ctk.CTkFrame):
    """Painel de resultado com botão para abrir pasta."""

    def __init__(self, master):
        super().__init__(master, fg_color="#1a3a1a", border_color="#2d6b2d",
                         border_width=1, corner_radius=8)

        self._lbl_result = ctk.CTkLabel(
            self, text="",
            font=ctk.CTkFont(size=13), text_color="#4ade80",
            wraplength=400,
        )
        self._lbl_result.pack(padx=16, pady=(12, 4))

        self._btn_open_folder = ctk.CTkButton(
            self, text="Abrir Pasta",
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

    def hide_result(self):
        self._lbl_result.configure(text="")
