"""Default settings. Saved values live in config/settings.json (per user, not committed)."""
import json
import os

from .paths import SETTINGS_JSON

DEFAULTS = {
    "model": "th_v1",         # id in config/models.json
    "voice": "male",          # folder name in voices/
    "speed": 1.0,             # 0.8-0.9 can reduce skipped words
    "nfe": 32,                # F5 quality steps; lower = faster
    "seed": -1,               # -1 = random
    "remove_silence": True,
}


def load_config():
    cfg = dict(DEFAULTS)
    if os.path.isfile(SETTINGS_JSON):
        try:
            with open(SETTINGS_JSON, encoding="utf-8") as f:
                cfg.update({k: v for k, v in json.load(f).items() if k in DEFAULTS})
        except (OSError, ValueError):
            pass
    return cfg


def save_config(**values):
    cfg = load_config()
    cfg.update({k: v for k, v in values.items() if k in DEFAULTS and v is not None})
    os.makedirs(os.path.dirname(SETTINGS_JSON), exist_ok=True)
    with open(SETTINGS_JSON, "w", encoding="utf-8") as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)
    return cfg
