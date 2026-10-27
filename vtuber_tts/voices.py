"""Voice presets: one folder per voice in voices/.

voices/<id>/ref.wav      5-8 s clean clip of the voice (used by F5 voice cloning)
voices/<id>/voice.json   {"name": "...", "ref_text": "words in ref.wav", "gender": "male|female",
                          "order": 1, "edge_voice": "th-TH-NiwatNeural" (optional)}
"""
import json
import os
import re
import time

from .config import load_config
from .paths import VOICES_DIR

EDGE_DEFAULT_VOICES = {"male": "th-TH-NiwatNeural", "female": "th-TH-PremwadeeNeural"}


def list_voices():
    """Return {display name: info} sorted by "order". info has id, ref_audio, ref_text, gender, edge_voice."""
    voices = []
    if os.path.isdir(VOICES_DIR):
        for vid in os.listdir(VOICES_DIR):
            folder = os.path.join(VOICES_DIR, vid)
            ref = os.path.join(folder, "ref.wav")
            if not os.path.isfile(ref):
                continue
            meta = {}
            meta_path = os.path.join(folder, "voice.json")
            if os.path.isfile(meta_path):
                with open(meta_path, encoding="utf-8") as f:
                    meta = json.load(f)
            gender = meta.get("gender") or ("female" if "female" in vid else "male")
            voices.append((meta.get("order", 99), meta.get("name", vid), {
                "id": vid, "ref_audio": ref, "ref_text": meta.get("ref_text", ""), "gender": gender,
                "edge_voice": meta.get("edge_voice") or EDGE_DEFAULT_VOICES.get(gender, EDGE_DEFAULT_VOICES["male"]),
            }))
    voices.sort(key=lambda v: (v[0], v[1]))
    return {name: info for _, name, info in voices}


def find_voice(key):
    """Look up a voice by folder id (e.g. "female") or display name. Returns (name, info) or (None, None)."""
    voices = list_voices()
    if key in voices:
        return key, voices[key]
    for name, info in voices.items():
        if info["id"] == key:
            return name, info
    return None, None


def find_voice_by_gender(gender):
    """The voice whose id equals the gender, else the first voice with that gender."""
    name, info = find_voice(gender)
    if name:
        return name, info
    for name, info in list_voices().items():
        if info["gender"] == gender:
            return name, info
    return None, None


def default_voice_name():
    """Display name of the configured default voice (or the first voice)."""
    name, _ = find_voice(load_config()["voice"])
    if name:
        return name
    names = list(list_voices())
    return names[0] if names else None


def add_voice(audio_path, name, ref_text, gender="male"):
    """Create a new voice folder from an audio clip. Returns (voice id, clip duration in seconds)."""
    import librosa
    import numpy as np
    import soundfile as sf

    wave, sr = librosa.load(audio_path, sr=24000, mono=True)
    duration = len(wave) / sr
    slug = re.sub(r"[^a-z0-9_]+", "_", name.strip().lower()).strip("_") or "voice"
    vid = f"{slug}_{time.strftime('%m%d%H%M%S')}"
    folder = os.path.join(VOICES_DIR, vid)
    os.makedirs(folder, exist_ok=True)
    sf.write(os.path.join(folder, "ref.wav"), np.asarray(wave, dtype=np.float32), sr, subtype="PCM_16")
    meta = {"name": name.strip(), "ref_text": ref_text.strip(), "order": 50, "gender": gender}
    with open(os.path.join(folder, "voice.json"), "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)
    return vid, duration
