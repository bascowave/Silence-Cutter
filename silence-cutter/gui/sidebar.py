import customtkinter as ctk
from tkinter import filedialog
from typing import Callable, Optional
import os


_PRESETS = {
    "Personalizado": None,  # no auto-set
    "Podcast": {"threshold_db": -30, "margin": 0.3},
    "Vlog": {"threshold_db": -24, "margin": 0.2},
    "Short": {"threshold_db": -20, "margin": 0.1},
}

_OUTPUT_FORMATS = ["Mesmo do original", "MP4", "MKV", "MOV"]


class _Tooltip:
    """Tooltip simples para widgets CTk."""

    def __init__(self, widget, text: str):
        self._widget = widget
        self._text = text
        self._tw = None
        self._after_id = None
        self._auto_hide_id = None
        self._hovering = False
        widget.bind("<Enter>", self._schedule_show)
        widget.bind("<Leave>", self._on_leave)
        # Esconde tooltip quando a janela principal é minimizada ou perde foco
        top = widget.winfo_toplevel()
        top.bind("<Unmap>", self._hide, add="+")
        top.bind("<FocusOut>", self._hide, add="+")

    def _schedule_show(self, event=None):
        self._cancel_schedule()
        self._hovering = True
        self._after_id = self._widget.after(400, self._show)

    def _cancel_schedule(self):
        if self._after_id:
            self._widget.after_cancel(self._after_id)
            self._after_id = None
        if self._auto_hide_id:
            self._widget.after_cancel(self._auto_hide_id)
            self._auto_hide_id = None

    def _on_leave(self, event=None):
        """Called when mouse leaves the widget."""
        self._hovering = False
        self._hide()

    def _show(self, event=None):
        self._after_id = None
        # Se o mouse já saiu, não mostrar
        if not self._hovering:
            return
        # Não mostra se a janela principal não estiver visível
        top = self._widget.winfo_toplevel()
        try:
            if top.state() != "normal" and top.state() != "zoomed":
                return
        except Exception:
            return
        # Se já existe, destruir o anterior
        self._hide_silent()
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
        # Auto-hide after 3 seconds to prevent stuck tooltips
        self._auto_hide_id = self._widget.after(3000, self._hide)

    def _hide(self, event=None):
        self._cancel_schedule()
        self._hovering = False
        self._hide_silent()

    def _hide_silent(self):
        """Hide tooltip without resetting hover state (for internal use)."""
        if self._tw is not None:
            try:
                self._tw.destroy()
            except Exception:
                pass
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
        self._file_list: list[str] = []
        self._last_directory = ""
        self._updating_from_preset = False

        self.grid_rowconfigure(20, weight=1)  # spacer before buttons
        self.grid_columnconfigure(0, weight=1)

        self._build_file_section()
        self._build_threshold_section()
        self._build_margin_section()
        self._build_preset_section()
        self._build_output_format_section()
        self._build_file_list_section()
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
            initialdir=self._last_directory or None,
            filetypes=[
                ("Vídeos", "*.mp4 *.mkv *.mov *.avi *.webm"),
                ("Todos", "*.*"),
            ],
        )
        if path:
            self._file_path = path
            name = os.path.basename(path)
            display = name if len(name) <= 28 else name[:25] + "..."
            self._lbl_filename.configure(text=display, text_color="#ccc")
            # Add tooltip with full filename
            _Tooltip(self._lbl_filename, name)
            self._btn_preview.configure(state="normal")
            self._btn_process.configure(state="normal")
            # Add to file list (or replace if empty for backward compatibility)
            self._add_single_file(path)
            self._on_file_selected(path)

    # ── Threshold ─────────────────────────────────────────────────

    def _build_threshold_section(self):
        row = 3
        self._section_label("THRESHOLD", row, "Volume abaixo do qual o áudio é considerado silêncio (dB)")
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
        self._section_label("MARGEM", row, "Tempo extra mantido antes e depois de cada trecho com áudio")
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

    # ── Preset ────────────────────────────────────────────────────

    def _build_preset_section(self):
        row = 7
        self._section_label("PRESET", row, "Configurações pré-definidas para diferentes tipos de conteúdo")
        row += 1

        self._preset_var = ctk.StringVar(value="Personalizado")

        self._preset_menu = ctk.CTkOptionMenu(
            self, values=list(_PRESETS.keys()),
            variable=self._preset_var,
            fg_color="#2d2d44", button_color="#6c5ce7",
            dropdown_fg_color="#2d2d44",
            dropdown_hover_color="#6c5ce7",
            command=self._on_preset_selected,
        )
        self._preset_menu.grid(row=row, column=0, padx=16, pady=(2, 12),
                               sticky="ew")

    def _on_preset_selected(self, preset_name: str):
        """Handle preset selection."""
        preset = _PRESETS.get(preset_name)
        if preset is not None:
            self._updating_from_preset = True
            # Update threshold
            self._threshold_var.set(preset["threshold_db"])
            self._entry_threshold.delete(0, "end")
            self._entry_threshold.insert(0, f"{preset['threshold_db']} dB")
            # Update margin
            self._margin_var.set(preset["margin"])
            self._entry_margin.delete(0, "end")
            self._entry_margin.insert(0, f"{preset['margin']:.2f} s")
            self._updating_from_preset = False
            self._on_settings_changed()

    # ── Output Format ─────────────────────────────────────────────

    def _build_output_format_section(self):
        row = 9
        self._section_label("FORMATO DE SAÍDA", row, "Formato do arquivo de vídeo processado")
        row += 1

        self._output_format_var = ctk.StringVar(value="Mesmo do original")

        self._output_format_menu = ctk.CTkOptionMenu(
            self, values=_OUTPUT_FORMATS,
            variable=self._output_format_var,
            fg_color="#2d2d44", button_color="#6c5ce7",
            dropdown_fg_color="#2d2d44",
            dropdown_hover_color="#6c5ce7",
            command=lambda _: self._on_settings_changed(),
        )
        self._output_format_menu.grid(row=row, column=0, padx=16, pady=(2, 12),
                                      sticky="ew")

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

    def _section_label(self, text: str, row: int, tooltip_text: str = ""):
        frame = ctk.CTkFrame(self, fg_color="transparent")
        frame.grid(row=row, column=0, padx=16, pady=(12, 0), sticky="w")
        frame.grid_columnconfigure(0, weight=0)

        lbl = ctk.CTkLabel(
            frame, text=text, text_color="#666",
            font=ctk.CTkFont(size=11, weight="bold"),
            anchor="w",
        )
        lbl.grid(row=0, column=0, sticky="w")

        if tooltip_text:
            info_btn = ctk.CTkLabel(
                frame, text="ⓘ", text_color="#6c5ce7",
                font=ctk.CTkFont(size=12, weight="bold"),
                cursor="hand2",
            )
            info_btn.grid(row=0, column=1, padx=(4, 0))
            _Tooltip(info_btn, tooltip_text)

    def _sync_slider_to_entry(self, value, entry, suffix, is_int=False):
        entry.delete(0, "end")
        if is_int:
            entry.insert(0, f"{int(float(value))} {suffix}")
        else:
            entry.insert(0, f"{float(value):.2f} {suffix}")
        # Change preset to "Personalizado" when slider is manually moved
        if not self._updating_from_preset:
            self._preset_var.set("Personalizado")
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

    # ── File List Section (Batch) ─────────────────────────────────

    def _build_file_list_section(self):
        """Build the file list section for batch processing."""
        row = 11
        self._section_label("ARQUIVOS (LOTE)", row, "Adicione múltiplos arquivos para processamento em lote")
        row += 1

        # Add files button
        self._btn_add_files = ctk.CTkButton(
            self, text="Adicionar Arquivos",
            fg_color="#6c5ce7", hover_color="#5a4bd1",
            command=self._add_files,
        )
        self._btn_add_files.grid(row=row, column=0, padx=16, pady=(4, 2),
                                 sticky="ew")
        row += 1

        # Scrollable file list frame
        self._file_list_frame = ctk.CTkScrollableFrame(
            self, fg_color="#151528", corner_radius=8,
            height=120, label_text="",
        )
        self._file_list_frame.grid(row=row, column=0, padx=16, pady=(4, 4),
                                   sticky="ew")
        self._file_list_frame.grid_columnconfigure(0, weight=1)
        row += 1

        # Clear list button
        self._btn_clear_list = ctk.CTkButton(
            self, text="Limpar Lista",
            fg_color="transparent", border_width=1,
            border_color="#e74c3c", hover_color="#2d2d44",
            text_color="#e74c3c",
            command=self._clear_file_list,
        )
        self._btn_clear_list.grid(row=row, column=0, padx=16, pady=(2, 12),
                                  sticky="ew")
        row += 1

        # File count label
        self._lbl_file_count = ctk.CTkLabel(
            self, text="0 arquivo(s) selecionado(s)",
            text_color="#888", font=ctk.CTkFont(size=10),
        )
        self._lbl_file_count.grid(row=row, column=0, padx=16, pady=(0, 8),
                                  sticky="w")

        self._file_list_widgets = [
            self._file_list_frame, self._btn_clear_list, self._lbl_file_count
        ]

    def _add_files(self):
        """Open dialog to select multiple files."""
        paths = filedialog.askopenfilenames(
            title="Selecionar Vídeos",
            initialdir=self._last_directory or None,
            filetypes=[
                ("Vídeos", "*.mp4 *.mkv *.mov *.avi *.webm"),
                ("Todos", "*.*"),
            ],
        )
        if paths:
            for path in paths:
                if path not in self._file_list:
                    self._file_list.append(path)
            self._last_directory = os.path.dirname(paths[0])
            self._refresh_file_list()
            self._update_buttons_state()
            # Notify first file for preview compatibility
            if len(self._file_list) == 1:
                self._on_file_selected(self._file_list[0])

    def _add_single_file(self, path: str):
        """Add a single file (from the select file button)."""
        if path not in self._file_list:
            self._file_list.append(path)
            self._refresh_file_list()
            self._update_buttons_state()

    def _remove_file(self, index: int):
        """Remove a file from the list."""
        if 0 <= index < len(self._file_list):
            self._file_list.pop(index)
            self._refresh_file_list()
            self._update_buttons_state()
            # Update single file path for compatibility
            if self._file_list:
                self._file_path = self._file_list[0]
                name = os.path.basename(self._file_path)
                display = name if len(name) <= 28 else name[:25] + "..."
                self._lbl_filename.configure(text=display, text_color="#ccc")
            else:
                self._file_path = None
                self._lbl_filename.configure(text="Nenhum arquivo",
                                              text_color="#888")

    def _clear_file_list(self):
        """Clear all files from the list."""
        self._file_list.clear()
        self._refresh_file_list()
        self._update_buttons_state()
        self._file_path = None
        self._lbl_filename.configure(text="Nenhum arquivo", text_color="#888")

    def _refresh_file_list(self):
        """Refresh the file list display."""
        # Clear existing widgets
        for widget in self._file_list_frame.winfo_children():
            widget.destroy()

        # Add file entries
        for i, path in enumerate(self._file_list):
            self._create_file_entry(i, path)

        # Update count label
        count = len(self._file_list)
        self._lbl_file_count.configure(
            text=f"{count} arquivo(s) selecionado(s)"
        )

    def _create_file_entry(self, index: int, path: str):
        """Create a single file entry in the list."""
        frame = ctk.CTkFrame(self._file_list_frame, fg_color="transparent")
        frame.grid(row=index, column=0, padx=4, pady=2, sticky="ew")
        frame.grid_columnconfigure(0, weight=1)

        name = os.path.basename(path)
        display = name if len(name) <= 24 else name[:21] + "..."

        lbl = ctk.CTkLabel(
            frame, text=display,
            font=ctk.CTkFont(size=11),
            text_color="#ccc",
            anchor="w",
        )
        lbl.grid(row=0, column=0, sticky="w")

        # Tooltip with full path
        _Tooltip(lbl, path)

        btn_remove = ctk.CTkButton(
            frame, text="×",
            width=24, height=24,
            fg_color="transparent",
            hover_color="#e74c3c",
            text_color="#888",
            font=ctk.CTkFont(size=14, weight="bold"),
            command=lambda idx=index: self._remove_file(idx),
        )
        btn_remove.grid(row=0, column=1, padx=(4, 0))

    def _update_buttons_state(self):
        """Update button states based on file list."""
        has_files = len(self._file_list) > 0
        if has_files:
            self._btn_preview.configure(state="normal")
            self._btn_process.configure(state="normal")
        else:
            self._btn_preview.configure(state="disabled")
            self._btn_process.configure(state="disabled")

    # ── Public API ────────────────────────────────────────────────

    @property
    def file_path(self) -> Optional[str]:
        return self._file_path

    @property
    def file_list(self) -> list[str]:
        """Return the list of selected file paths."""
        return self._file_list.copy()

    @property
    def threshold_db(self) -> int:
        return int(self._threshold_var.get())

    @property
    def margin(self) -> float:
        return self._margin_var.get()

    @property
    def preset(self) -> str:
        """Return the current preset name."""
        return self._preset_var.get()

    @property
    def output_format(self) -> str | None:
        """Return the selected output format, or None for 'same as original'."""
        fmt = self._output_format_var.get()
        return None if fmt == "Mesmo do original" else fmt

    @property
    def output_format_name(self) -> str:
        """Return the raw output format selection (for persistence)."""
        return self._output_format_var.get()

    @property
    def last_directory(self) -> str:
        return self._last_directory

    @last_directory.setter
    def last_directory(self, value: str):
        self._last_directory = value

    def apply_settings(self, threshold_db: int, margin: float):
        self._threshold_var.set(threshold_db)
        self._entry_threshold.delete(0, "end")
        self._entry_threshold.insert(0, f"{threshold_db} dB")
        self._margin_var.set(margin)
        self._entry_margin.delete(0, "end")
        self._entry_margin.insert(0, f"{margin:.2f} s")

    def set_preset(self, name: str):
        """Set the preset dropdown to the specified name."""
        if name in _PRESETS:
            self._preset_var.set(name)
            # Apply preset values if not "Personalizado"
            preset = _PRESETS[name]
            if preset is not None:
                self._updating_from_preset = True
                self._threshold_var.set(preset["threshold_db"])
                self._entry_threshold.delete(0, "end")
                self._entry_threshold.insert(0, f"{preset['threshold_db']} dB")
                self._margin_var.set(preset["margin"])
                self._entry_margin.delete(0, "end")
                self._entry_margin.insert(0, f"{preset['margin']:.2f} s")
                self._updating_from_preset = False

    def set_output_format(self, fmt: str):
        """Set the output format dropdown."""
        if fmt in _OUTPUT_FORMATS:
            self._output_format_var.set(fmt)

    def set_buttons_state(self, state: str):
        self._btn_preview.configure(state=state)
        self._btn_process.configure(state=state)

    def set_file_select_state(self, state: str):
        self._btn_select.configure(state=state)
        self._btn_add_files.configure(state=state)
        self._btn_clear_list.configure(state=state)

    def show_cancel_button(self):
        self._btn_preview.configure(state="disabled")
        self._btn_process.grid_forget()
        self._btn_cancel.grid(row=22, column=0, padx=16, pady=(0, 16),
                              sticky="ew")

    def hide_cancel_button(self):
        self._btn_cancel.grid_forget()
        self._btn_process.grid(row=22, column=0, padx=16, pady=(0, 16),
                               sticky="ew")
        if self._file_list:
            self.set_buttons_state("normal")
