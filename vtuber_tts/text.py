"""Text helpers: pronunciation dictionary and dialogue script parsing."""
import json
import os
import re

from .paths import PRONUNCIATIONS_JSON
from .voices import find_voice, find_voice_by_gender, list_voices

# ---------- Pronunciation dictionary (English words -> Thai reading) ----------


def load_pronunciations():
    if os.path.isfile(PRONUNCIATIONS_JSON):
        try:
            with open(PRONUNCIATIONS_JSON, encoding="utf-8") as f:
                return {str(k): str(v) for k, v in json.load(f).items() if str(k).strip()}
        except (OSError, ValueError):
            pass
    return {}


def save_pronunciations(mapping):
    clean = {k.strip(): v.strip() for k, v in mapping.items() if k and k.strip() and v and v.strip()}
    with open(PRONUNCIATIONS_JSON, "w", encoding="utf-8") as f:
        json.dump(dict(sorted(clean.items())), f, ensure_ascii=False, indent=2)
    return clean


def fix_typing(text):
    """Common Thai typing habits: two เ instead of แ."""
    return text.replace("เเ", "แ")


def apply_pronunciations(text, mapping=None):
    """Replace words like "Deploy" with their Thai reading ("ดีพลอย").

    Case-insensitive, whole words only, longest entries first (so "rest api" wins over "api").
    """
    mapping = load_pronunciations() if mapping is None else mapping
    text = fix_typing(text)
    for word in sorted(mapping, key=len, reverse=True):
        pattern = r"(?<![A-Za-z0-9])" + re.escape(word) + r"(?![A-Za-z0-9])"
        text = re.sub(pattern, lambda m, r=mapping[word]: r, text, flags=re.IGNORECASE)
    return text


# ---------- Dialogue scripts ----------

# Speaker labels that always mean a gender
SPEAKER_ALIASES = {
    "ผช": "male", "ชาย": "male", "ผู้ชาย": "male", "m": "male", "male": "male",
    "ผญ": "female", "หญิง": "female", "ผู้หญิง": "female", "f": "female", "female": "female",
}

_LABEL_RE = re.compile(r"^\s*([^\s:：\d]{1,15})\s*[:：]\s*(.+)$")


def parse_script(script, voice_a, voice_b):
    """Split a dialogue script into [(speaker, voice display name, text), ...].

    - "ผช: ..." / "ผญ: ..." / "male: ..." pick a voice of that gender ("male"/"female" folder first).
    - A voice id or name as label ("female: ...", "สาวน่ารัก: ...") picks that voice.
    - Any other label ("เบน: ...") gets voice A for the first new name, B for the second, and so on.
    - Lines without a label alternate between voice A and voice B.
    """
    voices = list_voices()
    order = [voice_a, voice_b]
    label_voice = {}
    lines = []
    last = None  # index into order of the previous speaker
    for raw in script.splitlines():
        line = raw.strip()
        if not line:
            continue
        m = _LABEL_RE.match(line)
        if m:
            label, text = m.group(1), m.group(2).strip()
            key = label.lower()
            name = None
            if find_voice(label)[0]:
                name, _ = find_voice(label)
            elif key in SPEAKER_ALIASES:
                name, _ = find_voice_by_gender(SPEAKER_ALIASES[key])
            if not name:
                if key not in label_voice:
                    label_voice[key] = order[len(label_voice) % 2]
                name = label_voice[key]
            speaker = label
            last = order.index(name) if name in order else last
        else:
            last = 0 if last is None else 1 - last
            name, text = order[last], line
            speaker = "A" if last == 0 else "B"
        if name not in voices:
            raise ValueError(f"ไม่พบเสียง '{name}'")
        lines.append((speaker, name, text))
    return lines
