import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from core.processor import SilenceCutterProcessor


@dataclass
class AnalysisResult:
    original_duration: float  # seconds
    estimated_duration: float  # seconds
    silence_removed: float  # seconds


class SilenceCutterAnalyzer:
    def __init__(self):
        self._processor_helper = SilenceCutterProcessor()

    def analyze(
        self,
        input_path: str,
        threshold_db: int = -24,
        margin: float = 0.2,
    ) -> AnalysisResult:
        binary = self._processor_helper._resolve_binary_path()
        cmd = [
            binary,
            input_path,
            "--edit", f"audio:{threshold_db}dB",
            "--margin", f"{margin}s",
            "--stats",
        ]

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            creationflags=subprocess.CREATE_NO_WINDOW,
        )

        output = result.stdout + "\n" + result.stderr
        return self._parse_stats(output)

    def _parse_stats(self, output: str) -> AnalysisResult:
        original = self._extract_duration(output, r"-\s*input:\s+(\S+)", r"(?:input|source)\s+duration[:\s]+(\S+)")
        estimated = self._extract_duration(output, r"-\s*output:\s+(\S+)", r"(?:output|new)\s+duration[:\s]+(\S+)")

        # Fallback: parse speed-up ratio
        if original is None or estimated is None:
            original, estimated = self._parse_from_speed_ratio(output, original, estimated)

        # Fallback: try to extract any two durations from the output
        if original is None or estimated is None:
            durations = self._extract_all_durations(output)
            if len(durations) >= 2:
                original = original or durations[0]
                estimated = estimated or durations[1]

        original = original or 0.0
        estimated = estimated or 0.0
        silence = max(0.0, original - estimated)

        return AnalysisResult(
            original_duration=original,
            estimated_duration=estimated,
            silence_removed=silence,
        )

    def _extract_duration(self, output: str, *patterns: str) -> Optional[float]:
        for pattern in patterns:
            match = re.search(pattern, output, re.IGNORECASE)
            if match:
                return self._time_to_seconds(match.group(1))
        return None

    def _parse_from_speed_ratio(
        self, output: str, original: Optional[float], estimated: Optional[float]
    ) -> tuple[Optional[float], Optional[float]]:
        match = re.search(r"speed[- ]?up[:\s]+(\d+(?:\.\d+)?)x", output, re.IGNORECASE)
        if match and original and not estimated:
            ratio = float(match.group(1))
            if ratio > 0:
                estimated = original / ratio
        return original, estimated

    def _extract_all_durations(self, output: str) -> list[float]:
        pattern = r"(\d{1,2}:\d{2}:\d{2}(?:\.\d+)?|\d{1,2}:\d{2}(?:\.\d+)?)"
        matches = re.findall(pattern, output)
        durations = []
        for m in matches:
            secs = self._time_to_seconds(m)
            if secs is not None and secs > 0:
                durations.append(secs)
        return durations

    def _time_to_seconds(self, time_str: str) -> Optional[float]:
        try:
            return float(time_str)
        except ValueError:
            pass

        # HH:MM:SS.ms or MM:SS.ms
        match = re.match(r"(?:(\d+):)?(\d+):(\d+(?:\.\d+)?)", time_str)
        if match:
            hours = int(match.group(1) or 0)
            minutes = int(match.group(2))
            seconds = float(match.group(3))
            return hours * 3600 + minutes * 60 + seconds

        return None
