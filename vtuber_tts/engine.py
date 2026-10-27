"""VoiceEngine: loads one model at a time and turns text (or a dialogue) into audio."""
import numpy as np

from .backends import get_backend_class
from .config import load_config
from .models import find_model
from .text import apply_pronunciations, fix_typing
from .voices import list_voices


class VoiceEngine:
    def __init__(self, model=None):
        """model: id or name from config/models.json (default from settings)."""
        self.backend = None
        self.model_info = None
        self.model_name = None
        self.load(model or load_config()["model"])

    @property
    def device(self):
        try:
            import torch
            return "GPU" if torch.cuda.is_available() else "CPU"
        except ImportError:
            return "CPU"

    def load(self, model):
        """Switch to another model (downloads it the first time). Returns its display name."""
        name, info = find_model(model)
        if not info:
            raise ValueError(f"ไม่พบโมเดล '{model}'")
        if self.model_info and self.model_info["id"] == info["id"]:
            return name
        if self.backend:  # free the old model first: only one fits in a 4 GB GPU
            self.backend.close()
            self.backend = None
        self.backend = get_backend_class(info.get("type", "f5"))(info)
        self.model_info, self.model_name = info, name
        return name

    def prepare_text(self, text):
        """What the model will actually read (pronunciation dictionary applied if the backend wants it)."""
        return apply_pronunciations(text) if self.backend.uses_pronunciations else fix_typing(text)

    def speak(self, text, voice, speed=None, nfe=None, seed=None, remove_silence=None):
        """voice: dict from voices.list_voices() (or a display name / id).

        Returns (sample_rate, float32 wave, seed used). Options left as None use saved settings.
        """
        cfg = load_config()
        if isinstance(voice, str):
            voice = list_voices().get(voice) or next(
                (v for v in list_voices().values() if v["id"] == voice), None)
            if voice is None:
                raise ValueError("ไม่พบเสียงที่เลือก")
        sr, wave, used_seed = self.backend.speak(
            self.prepare_text(text), voice,
            speed=cfg["speed"] if speed is None else speed,
            nfe=cfg["nfe"] if nfe is None else nfe,
            seed=cfg["seed"] if seed is None else seed,
            remove_silence=cfg["remove_silence"] if remove_silence is None else remove_silence,
        )
        return sr, np.asarray(wave, dtype=np.float32), used_seed

    def speak_dialogue(self, lines, pause=0.4, speed=None, nfe=None, seed=None, progress=None):
        """Render parsed script lines [(speaker, voice name, text), ...] into one conversation.

        Returns (sample_rate, combined wave, [(speaker, voice name, text, wave), ...]).
        progress(i, total, line) is called before each line if given.
        """
        voices = list_voices()
        parts, sr = [], 24000
        for i, (speaker, name, text) in enumerate(lines):
            if progress:
                progress(i, len(lines), (speaker, name, text))
            sr, wave, _ = self.speak(text, voices[name], speed=speed, nfe=nfe, seed=seed)
            parts.append((speaker, name, text, wave))
        gap = np.zeros(int(sr * float(pause)), dtype=np.float32)
        combined = []
        for i, p in enumerate(parts):
            if i:
                combined.append(gap)
            combined.append(p[3])
        return sr, (np.concatenate(combined) if combined else np.zeros(0, np.float32)), parts
