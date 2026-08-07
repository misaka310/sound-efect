"""Lazy, single-model Stable Audio 3 manager.

Only the selected model remains resident. A failed load records a short
diagnostic but does not poison future attempts: the next generate request can
retry after Hugging Face access or CUDA problems are corrected.
"""
import gc
import logging
import threading

import numpy as np
import torch

from app.config import settings

logger = logging.getLogger(__name__)

GATE_HINT = "Open the matching Hugging Face model page, accept its license, then run `huggingface-cli login`."


class AudioModelManager:
    def __init__(self):
        self.model = None
        self.sample_rate: int | None = None
        self.active_mode: str | None = None
        self.loading = False
        self.error: str | None = None
        self._lock = threading.RLock()
        self._infer_lock = threading.Lock()

    @property
    def loaded(self) -> bool:
        return self.model is not None

    def start(self):
        """Kept for lifecycle compatibility; models are intentionally lazy."""

    def _release_locked(self):
        self.model = None
        self.sample_rate = None
        self.active_mode = None
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()

    def ensure_loaded(self, mode: str):
        if mode not in settings.model_names:
            raise ValueError("mode must be 'sfx' or 'music'")
        with self._lock:
            if self.model is not None and self.active_mode == mode:
                return
            self.loading = True
            self.error = None
            self._release_locked()
            try:
                from stable_audio_3 import StableAudioModel

                model_name = settings.model_names[mode]
                model = StableAudioModel.from_pretrained(model_name, device=settings.device)
                self.model = model
                self.sample_rate = model.model.sample_rate
                self.active_mode = mode
                logger.info("model loaded: %s (%s Hz)", model_name, self.sample_rate)
            except Exception as exc:  # external model/download failures need a retry path
                message = str(exc)
                if type(exc).__name__ == "GatedRepoError" or "403" in message:
                    message = f"Model access was denied. {GATE_HINT}"
                self.error = message
                self._release_locked()
                logger.exception("model load failed")
                raise RuntimeError("Model could not be loaded. " + message) from exc
            finally:
                self.loading = False

    def generate(self, mode: str, prompt: str, duration: float, **kwargs) -> tuple[np.ndarray, int, int]:
        self.ensure_loaded(mode)
        seed = kwargs.pop("seed", None)
        seed_used = seed if seed is not None and seed >= 0 else int(np.random.randint(0, 2**31 - 1))
        generation_kwargs = {key: value for key, value in kwargs.items() if value is not None}
        with self._infer_lock:
            result = self.model.generate(prompt=prompt, duration=duration, seed=seed_used, **generation_kwargs)
        audio = np.ascontiguousarray(result[0].to(torch.float32).cpu().numpy().T)
        return audio, self.sample_rate, seed_used

    def status(self) -> dict:
        return {
            "loaded": self.loaded,
            "loading": self.loading,
            "error": self.error,
            "active_mode": self.active_mode,
            "models": {mode: {"name": name, "loaded": self.active_mode == mode and self.loaded}
                       for mode, name in settings.model_names.items()},
        }


# Existing imports continue to work.
sfx_model = AudioModelManager()
