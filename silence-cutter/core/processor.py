import os
import re
import subprocess
import threading
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Optional


@dataclass
class ProcessorSettings:
    input_path: str
    threshold_db: int = -24
    margin: float = 0.2


class SilenceCutterProcessor:
    def __init__(self):
        self._process: Optional[subprocess.Popen] = None
        self._cancelled = False

    def _resolve_binary_path(self) -> str:
        app_dir = Path(__file__).resolve().parent.parent
        binary = app_dir / "bin" / "auto-editor.exe"
        if binary.exists():
            return str(binary)

        # Fallback: check if auto-editor is on PATH
        import shutil
        path_binary = shutil.which("auto-editor")
        if path_binary:
            return path_binary

        raise FileNotFoundError(
            "auto-editor.exe não encontrado na pasta bin/ nem no PATH do sistema."
        )

    def _build_output_path(self, input_path: str) -> str:
        p = Path(input_path)
        return str(p.parent / f"{p.stem}_cut{p.suffix}")

    def _build_command(self, settings: ProcessorSettings, output_path: str) -> list[str]:
        binary = self._resolve_binary_path()
        cmd = [
            binary,
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
    ) -> None:
        self._cancelled = False
        output_path = self._build_output_path(settings.input_path)

        try:
            cmd = self._build_command(settings, output_path)
        except FileNotFoundError as e:
            if on_output:
                on_output(f"[ERROR] {e}")
            if on_complete:
                on_complete(False, "")
            return

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

                buf = ""
                while True:
                    ch = self._process.stdout.read(1)
                    if not ch:
                        break
                    if ch in ("\n", "\r"):
                        line = buf.strip()
                        buf = ""
                        if not line:
                            continue

                        percent = self._parse_progress(line)
                        if percent is not None:
                            if on_progress:
                                on_progress(percent)
                        else:
                            if on_output:
                                on_output(line)
                    else:
                        buf += ch

                if buf.strip():
                    if on_output:
                        on_output(buf.strip())

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
        if self._process:
            self._process.terminate()
