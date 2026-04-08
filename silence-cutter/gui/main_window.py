import os
import threading

import customtkinter as ctk

from core.analyzer import SilenceCutterAnalyzer
from core.processor import SilenceCutterProcessor, ProcessorSettings
from gui.sidebar import Sidebar
from gui.preview import PreviewPanel

_SUPPORTED_FORMATS = {".mp4", ".mkv", ".mov", ".avi", ".webm"}


class MainWindow(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Silence Cutter")
        self.geometry("900x550")
        self.minsize(800, 500)

        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("dark-blue")

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=0)  # sidebar fixed
        self.grid_columnconfigure(1, weight=1)   # main area expands

        self._analyzer = SilenceCutterAnalyzer()
        self._processor = SilenceCutterProcessor()
        self._binary_available = self._check_binary()

        self.sidebar = Sidebar(
            self,
            on_file_selected=self.on_file_selected,
            on_settings_changed=self.on_settings_changed,
            on_preview_click=self.on_preview_click,
            on_process_click=self.on_process_click,
            on_cancel_click=self.on_cancel_click,
        )
        self.sidebar.grid(row=0, column=0, sticky="ns")

        self.preview = PreviewPanel(self)
        self.preview.grid(row=0, column=1, sticky="nsew", padx=(0, 8),
                          pady=8)

    # ── Binary check ────────────────────────────────────────────────

    def _check_binary(self) -> bool:
        try:
            self._processor._resolve_binary_path()
            return True
        except FileNotFoundError:
            return False

    def _show_binary_warning(self):
        self.preview.append_log(
            "auto-editor não encontrado! Coloque auto-editor.exe "
            "na pasta bin/ ou instale via pip.", "ERROR")
        self.sidebar.set_buttons_state("disabled")

    # ── Validation ────────────────────────────────────────────────

    def _validate_input(self, path: str) -> bool:
        if not os.path.isfile(path):
            self.preview.append_log(
                f"Arquivo não encontrado: {path}", "ERROR")
            return False

        ext = os.path.splitext(path)[1].lower()
        if ext not in _SUPPORTED_FORMATS:
            self.preview.append_log(
                f"Formato não suportado: {ext} "
                f"(aceitos: {', '.join(sorted(_SUPPORTED_FORMATS))})", "ERROR")
            return False

        return True

    # ── Callbacks ─────────────────────────────────────────────────

    def on_file_selected(self, path: str):
        self.preview.clear_log()
        self.preview.hide_result()
        self.preview.reset_progress()
        self.preview.append_log(f"Arquivo selecionado: {path}")

        if not self._binary_available:
            self._show_binary_warning()

    def on_settings_changed(self):
        pass

    # ── Preview (Analyzer) ────────────────────────────────────────

    def on_preview_click(self):
        path = self.sidebar.file_path
        if not path or not self._validate_input(path):
            return

        self.sidebar.set_buttons_state("disabled")
        self.preview.append_log("Analisando...", "INFO")

        def _run():
            try:
                result = self._analyzer.analyze(
                    input_path=path,
                    threshold_db=self.sidebar.threshold_db,
                    margin=self.sidebar.margin,
                )
                self.after(0, lambda: self._on_analysis_done(result))
            except Exception as e:
                self.after(0, lambda: self._on_analysis_error(str(e)))

        threading.Thread(target=_run, daemon=True).start()

    def _on_analysis_done(self, result):
        self.preview.update_stats(
            result.original_duration,
            result.estimated_duration,
            result.silence_removed,
        )
        fmt = PreviewPanel._fmt_time
        self.preview.append_log(
            f"Original: {fmt(result.original_duration)} → "
            f"Estimado: {fmt(result.estimated_duration)} "
            f"(−{fmt(result.silence_removed)})", "INFO"
        )
        self.sidebar.set_buttons_state("normal")

    def _on_analysis_error(self, msg: str):
        self.preview.append_log(f"Erro na análise: {msg}", "ERROR")
        self.sidebar.set_buttons_state("normal")

    # ── Process ───────────────────────────────────────────────────

    def on_process_click(self):
        path = self.sidebar.file_path
        if not path or not self._validate_input(path):
            return

        self.preview.hide_result()
        self.preview.clear_log()
        self.preview.reset_progress()
        self.preview.append_log("Iniciando processamento...", "INFO")

        self.sidebar.show_cancel_button()

        settings = ProcessorSettings(
            input_path=path,
            threshold_db=self.sidebar.threshold_db,
            margin=self.sidebar.margin,
        )

        self._processor.process(
            settings=settings,
            on_output=lambda line: self.after(
                0, lambda l=line: self.preview.append_log(l)),
            on_progress=lambda pct: self.after(
                0, lambda p=pct: self.preview.update_progress(
                    p, f"{p:.0f}% — Processando...")),
            on_complete=lambda ok, out: self.after(
                0, lambda: self._on_process_complete(ok, out)),
        )

    def _on_process_complete(self, success: bool, output_path: str):
        self.sidebar.hide_cancel_button()
        if success:
            self.preview.update_progress(100, "100% — Concluído!")
            self.preview.append_log(f"Arquivo salvo: {output_path}", "INFO")
            self.preview.show_result(output_path)
        else:
            self.preview.append_log(
                "Processamento falhou. Verifique o log acima para detalhes.",
                "ERROR")
            self.preview.reset_progress()

    # ── Cancel ────────────────────────────────────────────────────

    def on_cancel_click(self):
        self._processor.cancel()
        self.preview.append_log("Processamento cancelado pelo usuário.", "WARN")
        self.preview.reset_progress()
        self.sidebar.hide_cancel_button()
