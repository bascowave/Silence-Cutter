import customtkinter as ctk
from tkinter import filedialog
from typing import Callable, Optional


class _Tooltip:
    """Tooltip simples para widgets CTk."""

    def __init__(self, widget, text: str):
        self._widget = widget
        self._text = text
        self._tw = None
        widget.bind("<Enter>", self._show)
        widget.bind("<Leave>", self._hide)

    def _show(self, event=None):
        x = self._widget.winfo_rootx() + self._widget.winfo_width() + 4
        y = self._widget.winfo_rooty()
        self._tw = tw = ctk.CTkToplevel(self._widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")
        tw.attributes("-topmost", True)
        label = ctk.CTkLabel(
            tw, text=self._text, fg_color="#2d2d44",
            corner_radius=6, text_color="#ccc",
            font=ctk.CTkFont(size=11),
            wraplength=200,
        )
        label.pack(padx=2, pady=2)

    def _hide(self, event=None):
        if self._tw:
            self._tw.destroy()
            self._tw = None


class Sidebar(ctk.CTkFrame):
    def __init__(self, master, on_file_selected: Callable[[str], None],
                 on_settings_changed: Callable[[], None],
                 on_preview_click: Callable[[], None],
                 on_process_click: Callable[[], None],
                 on_cancel_click: Callable[[], None] = lambda: None):
        super().__init__(master, width=240, corner_radius=0,
                         fg_color="#1a1a2e")

        self._on_file_selected = on_file_selected
        self._on_settings_changed = on_settings_changed
        self._on_preview_click = on_preview_click
        self._on_process_click = on_process_click
        self._on_cancel_click = on_cancel_click

        self._file_path: Optional[str] = None

        self.grid_rowconfigure(20, weight=1)  # spacer before buttons
        self.grid_columnconfigure(0, weight=1)

        self._build_file_section()
        self._build_threshold_section()
        self._build_margin_section()
        self._build_action_buttons()

    # ── File Section ──────────────────────────────────────────────

    def _build_file_section(self):
        row = 0
        self._section_label("ARQUIVO", row)
        row += 1

        self._btn_select = ctk.CTkButton(
            self, text="Selecionar Arquivo",
            fg_color="#6c5ce7", hover_color="#5a4bd1",
            command=self._select_file,
        )
        self._btn_select.grid(row=row, column=0, padx=16, pady=(4, 2),
                              sticky="ew")
        row += 1

        self._lbl_filename = ctk.CTkLabel(
            self, text="Nenhum arquivo", text_color="#888",
            font=ctk.CTkFont(size=11), wraplength=200, anchor="w",
        )
        self._lbl_filename.grid(row=row, column=0, padx=16, pady=(0, 12),
                                sticky="w")

    def _select_file(self):
        path = filedialog.askopenfilename(
            title="Selecionar Vídeo",
            filetypes=[
                ("Vídeos", "*.mp4 *.mkv *.mov *.avi *.webm"),
                ("Todos", "*.*"),
            ],
        )
        if path:
            self._file_path = path
            name = path.rsplit("/", 1)[-1].rsplit("\\", 1)[-1]
            display = name if len(name) <= 28 else name[:25] + "..."
            self._lbl_filename.configure(text=display, text_color="#ccc")
            self._btn_preview.configure(state="normal")
            self._btn_process.configure(state="normal")
            self._on_file_selected(path)

    # ── Threshold ─────────────────────────────────────────────────

    def _build_threshold_section(self):
        row = 3
        self._section_label("THRESHOLD", row)
        row += 1

        frame = ctk.CTkFrame(self, fg_color="transparent")
        frame.grid(row=row, column=0, padx=16, pady=(2, 12), sticky="ew")
        frame.grid_columnconfigure(0, weight=1)

        self._threshold_var = ctk.IntVar(value=-24)

        self._slider_threshold = ctk.CTkSlider(
            frame, from_=-60, to=0, number_of_steps=60,
            variable=self._threshold_var,
            fg_color="#2d2d44", progress_color="#6c5ce7",
            button_color="#6c5ce7", button_hover_color="#5a4bd1",
            command=lambda v: self._sync_slider_to_entry(
                v, self._entry_threshold, "dB", is_int=True),
        )
        self._slider_threshold.grid(row=0, column=0, sticky="ew", padx=(0, 8))
        _Tooltip(self._slider_threshold,
                 "Volume abaixo do qual o áudio é considerado silêncio (dB)")

        self._entry_threshold = ctk.CTkEntry(
            frame, width=70, justify="center",
            fg_color="#2d2d44", border_color="#3d3d55",
        )
        self._entry_threshold.grid(row=0, column=1)
        self._entry_threshold.insert(0, "-24 dB")
        self._entry_threshold.bind("<Return>",
            lambda e: self._sync_entry_to_slider(
                self._entry_threshold, self._slider_threshold,
                self._threshold_var, "dB", -60, 0, is_int=True))
        self._entry_threshold.bind("<FocusOut>",
            lambda e: self._sync_entry_to_slider(
                self._entry_threshold, self._slider_threshold,
                self._threshold_var, "dB", -60, 0, is_int=True))

    # ── Margin ────────────────────────────────────────────────────

    def _build_margin_section(self):
        row = 5
        self._section_label("MARGEM", row)
        row += 1

        frame = ctk.CTkFrame(self, fg_color="transparent")
        frame.grid(row=row, column=0, padx=16, pady=(2, 12), sticky="ew")
        frame.grid_columnconfigure(0, weight=1)

        self._margin_var = ctk.DoubleVar(value=0.2)

        self._slider_margin = ctk.CTkSlider(
            frame, from_=0.0, to=2.0, number_of_steps=40,
            variable=self._margin_var,
            fg_color="#2d2d44", progress_color="#6c5ce7",
            button_color="#6c5ce7", button_hover_color="#5a4bd1",
            command=lambda v: self._sync_slider_to_entry(
                v, self._entry_margin, "s"),
        )
        self._slider_margin.grid(row=0, column=0, sticky="ew", padx=(0, 8))
        _Tooltip(self._slider_margin,
                 "Tempo extra mantido antes e depois de cada trecho com áudio")

        self._entry_margin = ctk.CTkEntry(
            frame, width=70, justify="center",
            fg_color="#2d2d44", border_color="#3d3d55",
        )
        self._entry_margin.grid(row=0, column=1)
        self._entry_margin.insert(0, "0.20 s")
        self._entry_margin.bind("<Return>",
            lambda e: self._sync_entry_to_slider(
                self._entry_margin, self._slider_margin,
                self._margin_var, "s", 0.0, 2.0))
        self._entry_margin.bind("<FocusOut>",
            lambda e: self._sync_entry_to_slider(
                self._entry_margin, self._slider_margin,
                self._margin_var, "s", 0.0, 2.0))

    # ── Action Buttons ────────────────────────────────────────────

    def _build_action_buttons(self):
        row = 21  # after spacer row 20

        self._btn_preview = ctk.CTkButton(
            self, text="Pré-visualizar",
            fg_color="transparent", border_width=2,
            border_color="#6c5ce7", hover_color="#2d2d44",
            text_color="#6c5ce7", state="disabled",
            command=self._on_preview_click,
        )
        self._btn_preview.grid(row=row, column=0, padx=16, pady=(0, 8),
                               sticky="ew")
        row += 1

        self._btn_process = ctk.CTkButton(
            self, text="Processar Vídeo",
            fg_color="#6c5ce7", hover_color="#5a4bd1",
            font=ctk.CTkFont(weight="bold"), state="disabled",
            command=self._on_process_click,
        )
        self._btn_process.grid(row=22, column=0, padx=16, pady=(0, 16),
                               sticky="ew")

        self._btn_cancel = ctk.CTkButton(
            self, text="Cancelar",
            fg_color="#e74c3c", hover_color="#c0392b",
            font=ctk.CTkFont(weight="bold"),
            command=self._on_cancel_click,
        )
        # initially hidden

    # ── Helpers ───────────────────────────────────────────────────

    def _section_label(self, text: str, row: int):
        lbl = ctk.CTkLabel(
            self, text=text, text_color="#666",
            font=ctk.CTkFont(size=11, weight="bold"),
            anchor="w",
        )
        lbl.grid(row=row, column=0, padx=16, pady=(12, 0), sticky="w")

    def _sync_slider_to_entry(self, value, entry, suffix, is_int=False):
        entry.delete(0, "end")
        if is_int:
            entry.insert(0, f"{int(float(value))} {suffix}")
        else:
            entry.insert(0, f"{float(value):.2f} {suffix}")
        self._on_settings_changed()

    def _sync_entry_to_slider(self, entry, slider, var, suffix,
                               min_val, max_val, is_int=False):
        text = entry.get().replace(suffix, "").strip()
        try:
            val = int(text) if is_int else float(text)
            val = max(min_val, min(max_val, val))
            var.set(val)
            entry.delete(0, "end")
            if is_int:
                entry.insert(0, f"{int(val)} {suffix}")
            else:
                entry.insert(0, f"{val:.2f} {suffix}")
            self._on_settings_changed()
        except ValueError:
            # Restore from current var value
            current = var.get()
            entry.delete(0, "end")
            if is_int:
                entry.insert(0, f"{int(current)} {suffix}")
            else:
                entry.insert(0, f"{current:.2f} {suffix}")

    # ── Public API ────────────────────────────────────────────────

    @property
    def file_path(self) -> Optional[str]:
        return self._file_path

    @property
    def threshold_db(self) -> int:
        return int(self._threshold_var.get())

    @property
    def margin(self) -> float:
        return self._margin_var.get()

    def set_buttons_state(self, state: str):
        self._btn_preview.configure(state=state)
        self._btn_process.configure(state=state)

    def show_cancel_button(self):
        self._btn_preview.configure(state="disabled")
        self._btn_process.grid_forget()
        self._btn_cancel.grid(row=22, column=0, padx=16, pady=(0, 16),
                              sticky="ew")

    def hide_cancel_button(self):
        self._btn_cancel.grid_forget()
        self._btn_process.grid(row=22, column=0, padx=16, pady=(0, 16),
                               sticky="ew")
        if self._file_path:
            self.set_buttons_state("normal")
