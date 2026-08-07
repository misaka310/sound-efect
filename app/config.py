"""Application settings, overridable via environment variables."""
import os
from pathlib import Path


class Settings:
    host: str = os.getenv("SFX_HOST", "127.0.0.1")
    port: int = int(os.getenv("SFX_PORT", "8600"))
    device: str = os.getenv("SFX_DEVICE", "cuda")
    data_dir: Path = Path(os.getenv("SFX_DATA_DIR", "./generated"))
    llm_url: str = os.getenv("SFX_LLM_URL", "http://127.0.0.1:64652/v1")
    llm_model: str = os.getenv("SFX_LLM_MODEL", "unsloth/gemma-4-E4B-it-GGUF")

    # Stable Audio 3 model aliases. Do not eagerly load both: each can use a
    # substantial amount of VRAM/RAM.
    model_names = {"sfx": "small-sfx", "music": "small-music"}
    default_durations = {"sfx": 5.0, "music": 30.0}


settings = Settings()
settings.data_dir.mkdir(parents=True, exist_ok=True)
