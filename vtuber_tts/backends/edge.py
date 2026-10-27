"""Microsoft Edge TTS backend (online, stock voices, no GPU).

The voice comes from voices/<id>/voice.json "edge_voice" (default by gender:
male -> th-TH-NiwatNeural, female -> th-TH-PremwadeeNeural).
"""
import asyncio
import io
import re
import time

from .base import Backend


def edge_speak(text, voice_name, speed=1.0):
    """Synthesize with Edge TTS. Returns (24000, float32 wave). Needs internet.

    The service sometimes answers "No audio was received", randomly or for certain sentences
    (seen with the female voice on "...ล่ะ?"). So: retry, then try wordings that sound the same.
    """
    import edge_tts
    import numpy as np
    import soundfile as sf

    rate = f"{round((float(speed) - 1) * 100):+d}%"

    def variants(t):
        yield t
        yield t.rstrip("?!.。 ") + "."
        soft = re.sub(r"ล่ะ|หละ", "ละ", t)
        yield soft
        yield soft.rstrip("?!.。 ")
        yield re.sub(r"\s+", " ", re.sub(r"[?!]", " ", soft)).strip() + " "

    async def fetch(t):
        buf = b""
        async for chunk in edge_tts.Communicate(t, voice_name, rate=rate).stream():
            if chunk["type"] == "audio":
                buf += chunk["data"]
        return buf

    data, last_err, tried = b"", None, set()
    for candidate in variants(text):
        if candidate in tried:
            continue
        tried.add(candidate)
        for attempt in range(2):
            try:
                data = asyncio.run(fetch(candidate))
                if data:
                    break
            except Exception as e:
                last_err = e
            time.sleep(1.0 * (attempt + 1))
        if data:
            break
    if not data:
        raise RuntimeError(f"Edge TTS ไม่ส่งเสียงกลับมา (เช็กอินเทอร์เน็ต หรือลองเปลี่ยนคำในประโยค): {last_err}")

    wave, sr = sf.read(io.BytesIO(data), dtype="float32")
    if wave.ndim > 1:
        wave = wave.mean(axis=1)
    if sr != 24000:
        import librosa
        wave = librosa.resample(wave, orig_sr=sr, target_sr=24000)
    return 24000, np.asarray(wave, dtype=np.float32)


class EdgeBackend(Backend):
    type = "edge"
    uses_pronunciations = False  # Edge reads English words natively

    def speak(self, text, voice, speed=1.0, nfe=32, seed=-1, remove_silence=True):
        sr, wave = edge_speak(text, voice.get("edge_voice") or "th-TH-NiwatNeural", speed)
        return sr, wave, "-"
