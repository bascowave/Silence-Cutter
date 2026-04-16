import logging
import os
import queue
import threading
from dataclasses import dataclass
from enum import Enum

import customtkinter as ctk

from core.analyzer import SilenceCutterAnalyzer, get_video_info
from core.errors import BinaryNotFoundError, AnalysisError, SilenceCutterError
from core.processor import SilenceCutterProcessor, ProcessorSettings
from core.settings import AppSettings
from gui.sidebar import Sidebar
from gui.preview import PreviewPanel


def _format_size(size_bytes: int) -> str:
    if size_bytes >= 1_073_741_824:
        return f"{size_bytes / 1_073_741_824:.2f} GB"
    elif size_bytes >= 1_048_576:
        return f"{size_bytes / 1_048_576:.1f} MB"
    else:
        return f"{size_bytes / 1024:.0f} KB"

# Try to import drag-and-drop support
try:
    from tkinterdnd2 import DND_FILES, TkinterDnD
    _DND_AVAILABLE = True
except ImportError:
    _DND_AVAILABLE = False

_SUPPORTED_FORMATS = {".mp4", ".mkv", ".mov", ".avi", ".webm"}


class AppState(Enum):
    IDLE = "idle"
    ANALYZING = "analyzing"
    PROCESSING = "processing"
    CANCELLING = "cancelling"


@dataclass
class LogMessage:
    text: str
    level: str = "INFO"


@dataclass
class ProgressMessage:
    percent: float
    message: str = ""


@dataclass
class CompleteMessage:
    success: bool
    output_path: str
    is_analysis: bool = False
    analysis_result: object = None  # AnalysisResult when is_analysis=True


@dataclass
class ErrorMessage:
    text: str
    is_analysis: bool = False


@dataclass
class BatchProgressMessage:
    current: int
    total: int


@dataclass
class BatchCompleteMessage:
    successes: list
    failures: list
    total_time: float


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

        self._state = AppState.IDLE
        self._msg_queue = queue.Queue()
        self._worker_thread: threading.Thread | None = None

        # Load settings
        self._settings = AppSettings.load()

        # Resolve binary once and pass to both components
        binary_path = self._resolve_binary_once()
        self._binary_available = binary_path is not None

        self._analyzer = SilenceCutterAnalyzer(binary_path=binary_path)
        self._processor = SilenceCutterProcessor(binary_path=binary_path)

        self.sidebar = Sidebar(
            self,
            on_file_selected=self.on_file_selected,
            on_settings_changed=self.on_settings_changed,
            on_preview_click=self.on_preview_click,
            on_process_click=self.on_process_click,
            on_cancel_click=self.on_cancel_click,
        )
        self.sidebar.grid(row=0, column=0, sticky="ns")

        # Apply saved settings to sidebar
        self.sidebar.apply_settings(self._settings.threshold_db, self._settings.margin)
        if self._settings.last_directory:
            self.sidebar.last_directory = self._settings.last_directory
        self.sidebar.set_preset(self._settings.preset)
        self.sidebar.set_output_format(self._settings.output_format)

        self.preview = PreviewPanel(self)
        self.preview.grid(row=0, column=1, sticky="nsew", padx=(0, 8),
                          pady=8)

        # Setup drag-and-drop
        self._setup_drag_and_drop()

        # Setup keyboard shortcuts
        self._setup_keyboard_shortcuts()

        # Setup close handler
        self.protocol("WM_DELETE_WINDOW", self._on_close)

        # Start queue polling
        self._poll_queue()

        # Show warning if binary not available
        if not self._binary_available:
            self._show_binary_warning()

    # ── Binary check ────────────────────────────────────────────────

    def _resolve_binary_once(self) -> str | None:
        try:
            return SilenceCutterProcessor._resolve_binary_path()
        except BinaryNotFoundError:
            return None

    def _show_binary_warning(self):
        self.preview.append_log(
            "auto-editor não encontrado! Coloque auto-editor.exe "
            "na pasta bin/ ou instale via pip.", "ERROR")
        self.sidebar.set_buttons_state("disabled")

    # ── State Machine ───────────────────────────────────────────────

    def _set_state(self, new_state: AppState):
        self._state = new_state
        if new_state == AppState.IDLE:
            self.sidebar.set_file_select_state("normal")
            if self.sidebar.file_path:
                self.sidebar.set_buttons_state("normal")
            self.sidebar.hide_cancel_button()
        elif new_state == AppState.ANALYZING:
            self.sidebar.set_file_select_state("disabled")
            self.sidebar.set_buttons_state("disabled")
            self.sidebar.hide_cancel_button()
        elif new_state == AppState.PROCESSING:
            self.sidebar.set_file_select_state("disabled")
            self.sidebar.set_buttons_state("disabled")
            self.sidebar.show_cancel_button()
        elif new_state == AppState.CANCELLING:
            self.sidebar.set_file_select_state("disabled")
            self.sidebar.set_buttons_state("disabled")
            self.sidebar.hide_cancel_button()

    # ── Event Queue ─────────────────────────────────────────────────

    def _poll_queue(self):
        try:
            while True:
                msg = self._msg_queue.get_nowait()
                if isinstance(msg, LogMessage):
                    self.preview.append_log(msg.text, msg.level)
                elif isinstance(msg, ProgressMessage):
                    self.preview.update_progress(msg.percent, msg.message)
                elif isinstance(msg, BatchProgressMessage):
                    self.preview.update_batch_progress(msg.current, msg.total)
                elif isinstance(msg, BatchCompleteMessage):
                    self._on_batch_complete(msg.successes, msg.failures,
                                            msg.total_time)
                elif isinstance(msg, CompleteMessage):
                    if msg.is_analysis:
                        self._on_analysis_done(msg.analysis_result)
                    else:
                        self._on_process_complete(msg.success, msg.output_path)
                elif isinstance(msg, ErrorMessage):
                    if msg.is_analysis:
                        self._on_analysis_error(msg.text)
                    else:
                        self.preview.append_log(msg.text, "ERROR")
        except queue.Empty:
            pass
        self.after(50, self._poll_queue)

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
        if self._state != AppState.IDLE:
            return
        self.preview.clear_log()
        self.preview.hide_result()
        self.preview.reset_progress()
        self.preview.append_log(f"Arquivo selecionado: {path}")

        # Show video file info
        try:
            info = get_video_info(path)
            self.preview.show_info(info.name, _format_size(info.size_bytes), info.format_ext)
        except Exception:
            pass  # Silently ignore if we can't get info

        # Save last directory
        self._settings.last_directory = os.path.dirname(path)
        self._settings.save()

        if not self._binary_available:
            self._show_binary_warning()

    def on_settings_changed(self):
        self._settings.threshold_db = self.sidebar.threshold_db
        self._settings.margin = self.sidebar.margin
        self._settings.preset = self.sidebar.preset
        self._settings.output_format = self.sidebar.output_format_name
        self._settings.save()

    # ── Preview (Analyzer) ────────────────────────────────────────

    def on_preview_click(self):
        if self._state != AppState.IDLE:
            return
        path = self.sidebar.file_path
        if not path or not self._validate_input(path):
            return

        self._set_state(AppState.ANALYZING)
        self.preview.show_loading("Analisando...")
        self.preview.append_log("Analisando...", "INFO")

        def _run():
            try:
                result = self._analyzer.analyze(
                    input_path=path,
                    threshold_db=self.sidebar.threshold_db,
                    margin=self.sidebar.margin,
                )
                self._msg_queue.put(CompleteMessage(
                    success=True, output_path="", is_analysis=True, analysis_result=result))
            except BinaryNotFoundError as e:
                self._msg_queue.put(ErrorMessage(
                    text="auto-editor não encontrado. Verifique a instalação.", is_analysis=True))
            except AnalysisError as e:
                self._msg_queue.put(ErrorMessage(
                    text=f"Falha ao analisar o vídeo: {e}", is_analysis=True))
            except SilenceCutterError as e:
                self._msg_queue.put(ErrorMessage(
                    text=f"Erro: {e}", is_analysis=True))
            except Exception as e:
                self._msg_queue.put(ErrorMessage(text=str(e), is_analysis=True))

        self._worker_thread = threading.Thread(target=_run, daemon=True)
        self._worker_thread.start()

    def _on_analysis_done(self, result):
        self.preview.hide_loading()
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
        self._set_state(AppState.IDLE)
        self._worker_thread = None

    def _on_analysis_error(self, msg: str):
        self.preview.hide_loading()
        self.preview.append_log(f"Erro na análise: {msg}", "ERROR")
        self._set_state(AppState.IDLE)
        self._worker_thread = None

    # ── Process ───────────────────────────────────────────────────

    def on_process_click(self):
        if self._state != AppState.IDLE:
            return

        files = self.sidebar.file_list
        if not files:
            return

        # Validate all files
        for path in files:
            if not self._validate_input(path):
                return

        self._set_state(AppState.PROCESSING)
        self.preview.hide_result()
        self.preview.clear_log()
        self.preview.reset_progress()

        if len(files) == 1:
            # Single file - use existing flow
            self.preview.append_log("Iniciando processamento...", "INFO")
            self._process_single_file(files[0])
        else:
            # Batch processing
            self.preview.append_log(
                f"Iniciando processamento em lote: {len(files)} arquivos",
                "INFO")
            self.preview.show_batch_progress(1, len(files))
            self._batch_start_time = os.times().elapsed
            self._worker_thread = threading.Thread(
                target=self._run_batch, args=(files,), daemon=True)
            self._worker_thread.start()

    def _process_single_file(self, path: str):
        """Process a single file using the processor."""
        settings = ProcessorSettings(
            input_path=path,
            threshold_db=self.sidebar.threshold_db,
            margin=self.sidebar.margin,
        )

        def on_output(line: str):
            self._msg_queue.put(LogMessage(text=line, level="INFO"))

        def on_progress(pct: float):
            self._msg_queue.put(ProgressMessage(
                percent=pct, message=f"{pct:.0f}% — Processando..."))

        def on_complete(ok: bool, out: str):
            self._msg_queue.put(CompleteMessage(
                success=ok, output_path=out, is_analysis=False))

        thread = self._processor.process(
            settings=settings,
            on_output=on_output,
            on_progress=on_progress,
            on_complete=on_complete,
            output_format=self.sidebar.output_format,
        )
        if thread is not None:
            self._worker_thread = thread

    def _run_batch(self, files: list[str]):
        """Run batch processing sequentially in worker thread."""
        import time
        total = len(files)
        successes = []
        failures = []
        start_time = time.time()

        for i, file_path in enumerate(files, 1):
            if self._state == AppState.CANCELLING:
                self._msg_queue.put(LogMessage(
                    text="Processamento em lote cancelado.", level="WARN"))
                break

            # Update batch progress
            self._msg_queue.put(BatchProgressMessage(current=i, total=total))
            self._msg_queue.put(LogMessage(
                text=f"Processando arquivo {i}/{total}: "
                     f"{os.path.basename(file_path)}",
                level="INFO"))

            # Process single file synchronously
            result = self._process_file_sync(file_path)

            if result["success"]:
                successes.append({
                    "input": file_path,
                    "output": result["output_path"],
                })
                self._msg_queue.put(LogMessage(
                    text=f"✓ Concluído: {os.path.basename(file_path)}",
                    level="INFO"))
            else:
                failures.append({
                    "input": file_path,
                    "error": result["error"],
                })
                self._msg_queue.put(LogMessage(
                    text=f"✗ Falhou: {os.path.basename(file_path)}",
                    level="ERROR"))

        total_time = time.time() - start_time
        self._msg_queue.put(BatchCompleteMessage(
            successes=successes, failures=failures, total_time=total_time))

    def _process_file_sync(self, file_path: str) -> dict:
        """Process a single file synchronously (blocking)."""
        settings = ProcessorSettings(
            input_path=file_path,
            threshold_db=self.sidebar.threshold_db,
            margin=self.sidebar.margin,
        )

        result = {"success": False, "output_path": "", "error": ""}
        event = threading.Event()

        def on_output(line: str):
            self._msg_queue.put(LogMessage(text=line, level="INFO"))

        def on_progress(pct: float):
            self._msg_queue.put(ProgressMessage(
                percent=pct, message=f"{pct:.0f}% — Processando..."))

        def on_complete(ok: bool, out: str):
            result["success"] = ok
            result["output_path"] = out
            event.set()

        thread = self._processor.process(
            settings=settings,
            on_output=on_output,
            on_progress=on_progress,
            on_complete=on_complete,
            output_format=self.sidebar.output_format,
        )

        if thread is None:
            result["error"] = "Falha ao iniciar processamento"
            return result

        # Wait for completion with cancel check
        while not event.is_set():
            if self._state == AppState.CANCELLING:
                self._processor.cancel()
                result["error"] = "Cancelado pelo usuário"
                return result
            event.wait(timeout=0.1)

        if not result["success"]:
            result["error"] = "Processamento falhou"

        return result

    def _on_process_complete(self, success: bool, output_path: str):
        if success:
            self.preview.update_progress(100, "100% — Concluído!")
            self.preview.append_log(f"Arquivo salvo: {output_path}", "INFO")
            self.preview.show_result(output_path)
        else:
            self.preview.append_log(
                "Processamento falhou. Verifique o log acima para detalhes.",
                "ERROR")
            self.preview.reset_progress()
        self._set_state(AppState.IDLE)
        self._worker_thread = None

    def _on_batch_complete(self, successes: list, failures: list,
                           total_time: float):
        """Handle batch completion."""
        self.preview.hide_batch_progress()
        self.preview.update_progress(100, "Concluído!")

        total = len(successes) + len(failures)
        success_count = len(successes)

        # Format time
        minutes = int(total_time // 60)
        seconds = int(total_time % 60)
        time_str = f"{minutes}m {seconds}s" if minutes > 0 else f"{seconds}s"

        self.preview.append_log(
            f"Lote concluído: {success_count}/{total} arquivos "
            f"processados com sucesso. Tempo total: {time_str}",
            "INFO")

        if failures:
            self.preview.append_log(
                f"{len(failures)} arquivo(s) falharam:", "ERROR")
            for fail in failures:
                self.preview.append_log(
                    f"  - {os.path.basename(fail['input'])}", "ERROR")

        self._set_state(AppState.IDLE)
        self._worker_thread = None

    # ── Cancel ────────────────────────────────────────────────────

    def on_cancel_click(self):
        if self._state != AppState.PROCESSING:
            return
        self._set_state(AppState.CANCELLING)
        self._processor.cancel()
        self.preview.append_log("Processamento cancelado pelo usuário.", "WARN")
        self.preview.reset_progress()

    # ── Drag and Drop ─────────────────────────────────────────────

    def _setup_drag_and_drop(self):
        if not _DND_AVAILABLE:
            return
        try:
            self.drop_target_register(DND_FILES)
            self.dnd_bind('<<Drop>>', self._on_drop)
            self.dnd_bind('<<DragEnter>>', self._on_drag_enter)
            self.dnd_bind('<<DragLeave>>', self._on_drag_leave)
        except Exception as e:
            logging.getLogger(__name__).warning(f"Drag-and-drop not available: {e}")

    def _on_drop(self, event):
        # Parse the dropped file path (may be wrapped in {})
        path = event.data.strip()
        if path.startswith('{') and path.endswith('}'):
            path = path[1:-1]
        # Take only the first file if multiple
        if ' ' in path and not os.path.exists(path):
            path = path.split()[0]

        ext = os.path.splitext(path)[1].lower()
        if ext in _SUPPORTED_FORMATS and os.path.isfile(path):
            self.sidebar._file_path = path
            name = os.path.basename(path)
            display = name if len(name) <= 28 else name[:25] + "..."
            self.sidebar._lbl_filename.configure(text=display, text_color="#ccc")
            self.sidebar._btn_preview.configure(state="normal")
            self.sidebar._btn_process.configure(state="normal")
            # Add to file list for batch support
            self.sidebar._add_single_file(path)
            self.on_file_selected(path)
        else:
            self.preview.append_log(f"Formato não suportado: {ext}", "ERROR")

        # Reset visual
        self._on_drag_leave(None)

    def _on_drag_enter(self, event):
        self.preview.configure(border_width=2, border_color="#6c5ce7")

    def _on_drag_leave(self, event):
        self.preview.configure(border_width=0)

    # ── Keyboard Shortcuts ────────────────────────────────────────

    def _setup_keyboard_shortcuts(self):
        """Register keyboard shortcuts."""
        self.bind("<Control-o>", lambda e: self._shortcut_open())
        self.bind("<Control-Return>", lambda e: self._shortcut_process())
        self.bind("<Escape>", lambda e: self._shortcut_cancel())
        self.bind("<Control-p>", lambda e: self._shortcut_preview())

    def _shortcut_open(self):
        """Ctrl+O: Select file."""
        if self._state == AppState.IDLE:
            self.sidebar._select_file()

    def _shortcut_process(self):
        """Ctrl+Enter: Process video."""
        if self._state == AppState.IDLE:
            self.on_process_click()

    def _shortcut_cancel(self):
        """Escape: Cancel processing."""
        if self._state == AppState.PROCESSING:
            self.on_cancel_click()

    def _shortcut_preview(self):
        """Ctrl+P: Preview analysis."""
        if self._state == AppState.IDLE:
            self.on_preview_click()

    # ── Close Handler ─────────────────────────────────────────────

    def _on_close(self):
        self._settings.save()
        self.destroy()
