"""Speech to text with faster-whisper.

Uses the local copy in models/whisper/faster-whisper-medium/ if present, otherwise downloads
the "medium" model automatically (~1.5 GB) on first use.
"""
import gc
import os

from .paths import WHISPER_DIR


def transcribe(audio_path, language="th"):
    """Return the words spoken in an audio file.

    Loads the model, transcribes, then frees it so it does not hold GPU memory TTS needs.
    """
    from faster_whisper import WhisperModel

    source = WHISPER_DIR if os.path.isdir(WHISPER_DIR) else "medium"
    model = None
    try:
        try:
            model = WhisperModel(source, device="cuda", compute_type="int8_float16")
            segments, _ = model.transcribe(audio_path, language=language, beam_size=5)
            text = " ".join(s.text.strip() for s in segments)
        except Exception:
            # No GPU or GPU busy: CPU is fine for short clips
            model = WhisperModel(source, device="cpu", compute_type="int8")
            segments, _ = model.transcribe(audio_path, language=language, beam_size=5)
            text = " ".join(s.text.strip() for s in segments)
    finally:
        del model
        gc.collect()
        try:
            import torch
            torch.cuda.empty_cache()
        except Exception:
            pass
    return text.strip()
