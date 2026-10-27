"""Model registry: config/models.json plus checkpoints you drop into models/custom/.

Each entry has an "id", a "name", and a "type" that picks the backend (see backends/).
F5 entries also have "repo"/"file" on Hugging Face, "arch" (v1/v2), "vocab", "ipa", "thai".
"""
import json
import os

from .config import load_config
from .paths import CUSTOM_DIR, DOWNLOADED_DIR, MODELS_JSON, ROOT, VOCAB_DIR

LOCAL_VOCABS = {
    "thai": os.path.join(VOCAB_DIR, "vocab.txt"),
    "thai_ipa": os.path.join(VOCAB_DIR, "vocab_ipa.txt"),
}


def _scan_custom_models():
    """Checkpoints in models/custom/ (e.g. fine-tuned on your own voice).

    An optional <name>.json next to the file can override "name", "arch", "vocab", "ipa", "thai".
    Defaults are Thai v1 settings, which match fine-tuning from the Thai v1 model.
    """
    found = []
    if not os.path.isdir(CUSTOM_DIR):
        return found
    for fname in sorted(os.listdir(CUSTOM_DIR)):
        stem, ext = os.path.splitext(fname)
        if ext.lower() not in (".pt", ".safetensors"):
            continue
        path = os.path.join(CUSTOM_DIR, fname)
        info = {"id": f"custom_{stem}", "name": f"🎙️ {stem} (โมเดลในเครื่อง)", "type": "f5",
                "note": "โมเดลที่คุณวางไว้ใน models/custom/", "path": path,
                "arch": "v1", "vocab": "thai", "ipa": False, "thai": True,
                "size_mb": int(os.path.getsize(path) / 1e6)}
        side = os.path.join(CUSTOM_DIR, stem + ".json")
        if os.path.isfile(side):
            try:
                with open(side, encoding="utf-8") as f:
                    info.update(json.load(f))
            except (OSError, ValueError):
                pass
        found.append(info)
    return found


def list_models(downloaded_only=False):
    """Return {display name: info}, registry order, custom models last."""
    with open(MODELS_JSON, encoding="utf-8") as f:
        models = json.load(f)
    for m in models:
        m.setdefault("type", "f5")
    models += _scan_custom_models()
    if downloaded_only:
        models = [m for m in models if is_downloaded(m)]
    return {m["name"]: m for m in models}


def find_model(key):
    """Look up a model by id (e.g. "th_v2") or display name. Returns (name, info) or (None, None)."""
    models = list_models()
    if key in models:
        return key, models[key]
    for name, info in models.items():
        if info["id"] == key:
            return name, info
    return None, None


def default_model_name():
    name, _ = find_model(load_config()["model"])
    return name or next(iter(list_models()))


def checkpoint_path(info):
    """Where this model's checkpoint lives (or will live once downloaded)."""
    if info.get("path"):
        return info["path"] if os.path.isabs(info["path"]) else os.path.join(ROOT, info["path"])
    return os.path.join(DOWNLOADED_DIR, info["id"], info["file"])


def is_downloaded(info):
    if info.get("type", "f5") != "f5":  # online backends need no files
        return True
    return os.path.isfile(checkpoint_path(info))


def model_files(info):
    """Return (checkpoint path, vocab path) for an F5 model, downloading from Hugging Face if needed."""
    from huggingface_hub import hf_hub_download

    ckpt = checkpoint_path(info)
    if not os.path.isfile(ckpt):
        ckpt = hf_hub_download(info["repo"], info["file"], local_dir=os.path.join(DOWNLOADED_DIR, info["id"]))
    vocab = info["vocab"]
    if isinstance(vocab, dict):  # {"repo": ..., "file": ...} on Hugging Face
        vocab = hf_hub_download(vocab["repo"], vocab["file"], local_dir=os.path.join(DOWNLOADED_DIR, info["id"]))
    elif vocab in LOCAL_VOCABS:
        vocab = LOCAL_VOCABS[vocab]
    else:  # a path to a custom vocab.txt
        vocab = vocab if os.path.isabs(vocab) else os.path.join(ROOT, vocab)
    return ckpt, vocab
