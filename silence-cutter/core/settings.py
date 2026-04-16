import json
import logging
import os
from dataclasses import dataclass, field, asdict
from pathlib import Path

logger = logging.getLogger(__name__)

_SETTINGS_DIR = Path(os.environ.get("APPDATA", Path.home())) / "SilenceCutter"
_SETTINGS_FILE = _SETTINGS_DIR / "settings.json"


@dataclass
class AppSettings:
    threshold_db: int = -24
    margin: float = 0.2
    last_directory: str = ""
    preset: str = "Personalizado"
    output_format: str = "Mesmo do original"

    def save(self) -> None:
        try:
            _SETTINGS_DIR.mkdir(parents=True, exist_ok=True)
            with open(_SETTINGS_FILE, "w", encoding="utf-8") as f:
                json.dump(asdict(self), f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.warning(f"Failed to save settings: {e}")

    @classmethod
    def load(cls) -> "AppSettings":
        try:
            if _SETTINGS_FILE.exists():
                with open(_SETTINGS_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})
        except Exception as e:
            logger.warning(f"Failed to load settings, using defaults: {e}")
        return cls()
