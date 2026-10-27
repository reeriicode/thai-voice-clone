"""Command-line tools (run through speak.py and dialogue.py in the project root)."""
import argparse
import os
import sys
import time

from .config import load_config
from .models import find_model, is_downloaded, list_models
from .paths import OUTPUTS_DIR
from .text import parse_script
from .voices import EDGE_DEFAULT_VOICES, find_voice, list_voices


def _play(path):
    if sys.platform == "win32":
        import winsound
        winsound.PlaySound(path, winsound.SND_FILENAME)  # waits until playback ends


def _check_model(p, model):
    if model and not find_model(model)[1]:
        p.error(f"unknown model '{model}' (see speak.py --list-models)")


def speak_main(argv=None):
    p = argparse.ArgumentParser(description="Text to speech in a chosen voice.")
    p.add_argument("--text", help="text to say")
    p.add_argument("--voice", help="voice id in voices/ (default from settings)")
    p.add_argument("--ref", help="use any clip as the voice instead of --voice")
    p.add_argument("--ref-text", default="", help="words spoken in --ref (empty = auto transcribe)")
    p.add_argument("--model", help="model id from config/models.json (default from settings)")
    p.add_argument("--out", help="output WAV (default outputs/<time>.wav)")
    p.add_argument("--speed", type=float, help="0.5-1.5; 0.8-0.9 can reduce skipped words")
    p.add_argument("--nfe", type=int, help="F5 quality steps; lower = faster")
    p.add_argument("--seed", type=int, help="-1 = random")
    p.add_argument("--play", action="store_true", help="play the result on the speakers")
    p.add_argument("--list", action="store_true", help="show voices")
    p.add_argument("--list-models", action="store_true", help="show models")
    a = p.parse_args(argv)
    cfg = load_config()

    if a.list_models:
        for name, m in list_models().items():
            flags = "ready" if is_downloaded(m) else f"not downloaded, {m.get('size_mb', 0) / 1000:.1f} GB"
            flags += ", default" if m["id"] == cfg["model"] else ""
            print(f"{m['id']:12s} {name}  ({flags})")
        return 0
    if a.list:
        for name, v in list_voices().items():
            print(f"{v['id']:24s} {name}{'  (default)' if v['id'] == cfg['voice'] else ''}")
        return 0
    _check_model(p, a.model)
    if not a.text:
        p.error("--text is required")

    if a.ref:
        voice = {"id": "ref", "ref_audio": a.ref, "ref_text": a.ref_text, "gender": "male",
                 "edge_voice": EDGE_DEFAULT_VOICES["male"]}
    else:
        _, voice = find_voice(a.voice or cfg["voice"])
        if not voice:
            p.error(f"unknown voice '{a.voice or cfg['voice']}' (see --list)")

    from .engine import VoiceEngine
    import soundfile as sf

    t0 = time.time()
    engine = VoiceEngine(a.model)
    print(f"Model {engine.model_name} loaded in {time.time() - t0:.1f}s on {engine.device}")
    t1 = time.time()
    sr, wave, seed = engine.speak(a.text, voice, speed=a.speed, nfe=a.nfe, seed=a.seed)
    out = a.out or os.path.join(OUTPUTS_DIR, f"{time.strftime('%Y%m%d-%H%M%S')}_{voice['id']}.wav")
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    sf.write(out, wave, sr, subtype="PCM_16")
    print(f"Saved {os.path.abspath(out)}: {len(wave) / sr:.1f}s of audio in {time.time() - t1:.1f}s (seed {seed})")
    if a.play:
        _play(out)
    return 0


def dialogue_main(argv=None):
    p = argparse.ArgumentParser(description="Render a dialogue script into one conversation WAV.")
    p.add_argument("--script", required=True, help="UTF-8 text file, one line per turn (see dialogues/)")
    p.add_argument("--out", help="output WAV (default outputs/dialogue_<time>.wav)")
    p.add_argument("--a", help="voice A (default from settings)")
    p.add_argument("--b", help="voice B (default: the next voice)")
    p.add_argument("--model", help="model id from config/models.json (default from settings)")
    p.add_argument("--pause", type=float, default=0.4, help="seconds of silence between lines")
    p.add_argument("--speed", type=float, help="0.5-1.5")
    p.add_argument("--nfe", type=int, help="F5 quality steps")
    p.add_argument("--check", action="store_true", help="only show how the script is split")
    p.add_argument("--play", action="store_true", help="play the result on the speakers")
    a = p.parse_args(argv)
    _check_model(p, a.model)

    names = list(list_voices())
    name_a, _ = find_voice(a.a or load_config()["voice"])
    if not name_a:
        name_a = names[0] if names else None
    if not name_a:
        p.error("no voices found in voices/")
    if a.b:
        name_b, _ = find_voice(a.b)
        if not name_b:
            p.error(f"unknown voice B '{a.b}'")
    else:
        name_b = next((n for n in names if n != name_a), name_a)

    with open(a.script, encoding="utf-8-sig") as f:
        lines = parse_script(f.read(), name_a, name_b)
    if not lines:
        p.error("script is empty")

    from .engine import VoiceEngine
    import soundfile as sf

    t0 = time.time()
    engine = VoiceEngine(a.model)
    print(f"Model {engine.model_name} loaded in {time.time() - t0:.1f}s on {engine.device}")
    for i, (sp, name, text) in enumerate(lines, 1):
        print(f"{i:2d}. [{sp} -> {name}] {engine.prepare_text(text)}")
    if a.check:
        return 0

    t1 = time.time()
    sr, combined, parts = engine.speak_dialogue(
        lines, pause=a.pause, speed=a.speed, nfe=a.nfe,
        progress=lambda i, n, line: print(f"  generating line {i + 1}/{n} ({line[0]})", flush=True))
    out = a.out or os.path.join(OUTPUTS_DIR, f"dialogue_{time.strftime('%Y%m%d-%H%M%S')}.wav")
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    sf.write(out, combined, sr, subtype="PCM_16")
    line_dir = os.path.splitext(out)[0] + "_lines"
    os.makedirs(line_dir, exist_ok=True)
    voices = list_voices()
    for i, (_, name, _, wave) in enumerate(parts, 1):
        sf.write(os.path.join(line_dir, f"{i:02d}_{voices[name]['id']}.wav"), wave, sr, subtype="PCM_16")
    print(f"Saved {os.path.abspath(out)}: {len(combined) / sr:.1f}s, {len(parts)} lines in "
          f"{time.time() - t1:.1f}s (per-line files in {os.path.abspath(line_dir)})")
    if a.play:
        _play(out)
    return 0
