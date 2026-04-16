import os
import re
import subprocess
import threading
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Optional

from core.errors import BinaryNotFoundError


@dataclass
class ProcessorSettings:
    input_path: str
    threshold_db: int = -24
    margin: float = 0.2


class SilenceCutterProcessor:
    def __init__(self, binary_path: str | None = None):
        self._process: Optional[subprocess.Popen] = None
        self._cancelled = False
        self._cancel_event = threading.Event()
        if binary_path:
            self._binary_path = binary_path
        else:
            self._binary_path = self._resolve_binary_path()

    @staticmethod
    def _resolve_binary_path() -> str:
        app_dir = Path(__file__).resolve().parent.parent
        binary = app_dir / "bin" / "auto-editor.exe"
        if binary.exists():
            return str(binary)

        # Fallback: check if auto-editor is on PATH
        import shutil
        path_binary = shutil.which("auto-editor")
        if path_binary:
            return path_binary

        raise BinaryNotFoundError(
            "auto-editor.exe não encontrado na pasta bin/ nem no PATH do sistema."
        )

    def _build_output_path(self, input_path: str, output_format: str | None = None) -> str:
        p = Path(input_path)
        ext = f".{output_format.lower()}" if output_format else p.suffix
        return str(p.parent / f"{p.stem}_cut{ext}")

    def _build_command(self, settings: ProcessorSettings, output_path: str) -> list[str]:
        cmd = [
            self._binary_path,
            settings.input_path,
            "--edit", f"audio:{settings.threshold_db}dB",
            "--margin", f"{settings.margin}s",
            "--output", output_path,
            "--progress", "machine",
        ]
        return cmd

    def process(
        self,
        settings: ProcessorSettings,
        on_output: Optional[Callable[[str], None]] = None,
        on_progress: Optional[Callable[[float], None]] = None,
        on_complete: Optional[Callable[[bool, str], None]] = None,
        output_format: str | None = None,
    ) -> threading.Thread | None:
        self._cancelled = False
        self._cancel_event.clear()
        output_path = self._build_output_path(settings.input_path, output_format)

        try:
            cmd = self._build_command(settings, output_path)
        except FileNotFoundError as e:
            if on_output:
                on_output(f"[ERROR] {e}")
            if on_complete:
                on_complete(False, "")
            return None

        def _run():
            try:
                self._process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    encoding="utf-8",
                    errors="replace",
                    creationflags=subprocess.CREATE_NO_WINDOW,
                )

                timeout_timer = threading.Timer(300.0, self._kill_process)
                timeout_timer.daemon = True
                timeout_timer.start()

                for raw_line in iter(self._process.stdout.readline, ''):
                    if self._cancelled or self._cancel_event.is_set():
                        break
                    # Handle \r for progress lines (no \n)
                    parts = raw_line.split('\r')
                    for part in parts:
                        line = part.strip()
                        if not line:
                            continue
                        percent = self._parse_progress(line)
                        if percent is not None:
                            if on_progress:
                                on_progress(percent)
                        else:
                            if on_output:
                                on_output(line)

                timeout_timer.cancel()

                self._process.wait()
                success = self._process.returncode == 0 and not self._cancelled

                if self._cancelled and os.path.exists(output_path):
                    try:
                        os.remove(output_path)
                    except OSError:
                        pass

                if on_complete:
                    on_complete(success, output_path if success else "")

            except Exception as e:
                if on_output:
                    on_output(f"[ERROR] {e}")
                if on_complete:
                    on_complete(False, "")
            finally:
                self._process = None

        thread = threading.Thread(target=_run, daemon=True)
        thread.start()
        return thread

    def _parse_progress(self, line: str) -> Optional[float]:
        # Machine format: "(mp4) h264+aac~current~total~eta"
        match = re.search(r"~(\d+(?:\.\d+)?)~(\d+(?:\.\d+)?)~", line)
        if match:
            current, total = float(match.group(1)), float(match.group(2))
            if total > 0:
                return min((current / total) * 100, 100.0)

        # Fallback: percentage format "50%"
        match = re.search(r"(\d+(?:\.\d+)?)%", line)
        if match:
            return float(match.group(1))

        return None

    def cancel(self) -> None:
        self._cancelled = True
        self._cancel_event.set()
        if self._process:
            self._process.terminate()
            try:
                self._process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self._process.kill()

    def _kill_process(self):
        """Kill process on timeout."""
        self._cancelled = True
        if self._process:
            self._process.kill()
