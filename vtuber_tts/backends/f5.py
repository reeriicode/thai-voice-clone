"""F5-TTS backend (F5-TTS-THAI): clones the voice from voices/<id>/ref.wav."""
import os
import random
import sys
import tempfile

from ..models import model_files
from .base import Backend

# Model architectures (v1 = Thai v1 / original Base, v2 = Thai v2 / original F5-TTS v1)
ARCH = {
    "v1": dict(dim=1024, depth=22, heads=16, ff_mult=2, text_dim=512,
               text_mask_padding=False, conv_layers=4, pe_attn_head=1),
    "v2": dict(dim=1024, depth=22, heads=16, ff_mult=2, text_dim=512,
               text_mask_padding=True, conv_layers=4, pe_attn_head=None),
}

_vocoder = None  # shared across F5 models, loaded once


def _get_vocoder():
    global _vocoder
    if _vocoder is None:
        from f5_tts.infer.utils_infer import load_vocoder
        _vocoder = load_vocoder()
    return _vocoder


class F5Backend(Backend):
    type = "f5"

    def __init__(self, info):
        super().__init__(info)
        from f5_tts.infer.utils_infer import load_model
        from f5_tts.model import DiT

        self.uses_pronunciations = bool(info.get("thai", True))
        ckpt, vocab = model_files(info)
        self.vocoder = _get_vocoder()
        self.model = load_model(DiT, ARCH[info.get("arch", "v1")], ckpt, vocab_file=vocab, use_ema=True)

    def speak(self, text, voice, speed=1.0, nfe=32, seed=-1, remove_silence=True):
        import soundfile as sf
        import torchaudio
        from f5_tts.cleantext.th_normalize import normalize_text
        from f5_tts.infer.utils_infer import (infer_process, preprocess_ref_audio_text,
                                              remove_silence_for_generated_wav)
        from f5_tts.model.utils import seed_everything

        from ..stt import transcribe

        if seed is None or seed < 0:
            seed = random.randint(0, sys.maxsize)
        seed_everything(seed)

        ref_text = voice.get("ref_text") or ""
        if not ref_text.strip():
            ref_text = transcribe(voice["ref_audio"])
        if self.info.get("thai", True):
            text = normalize_text(text)
        ref_audio, ref_text = preprocess_ref_audio_text(voice["ref_audio"], ref_text)
        wave, sr, _ = infer_process(
            ref_audio, ref_text, text, self.model, self.vocoder,
            nfe_step=int(nfe), speed=float(speed), cfg_strength=2.0, cross_fade_duration=0.15,
            use_ipa=bool(self.info.get("ipa", False)),
        )
        if remove_silence:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as f:
                tmp = f.name
            sf.write(tmp, wave, sr)
            remove_silence_for_generated_wav(tmp)
            w, _ = torchaudio.load(tmp)
            wave = w.squeeze().cpu().numpy()
            os.remove(tmp)
        return sr, wave, seed

    def close(self):
        import gc

        self.model = None
        gc.collect()
        try:
            import torch
            torch.cuda.empty_cache()
        except Exception:
            pass
