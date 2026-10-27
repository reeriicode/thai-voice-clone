# VTuber Thai TTS

Thai text-to-speech: voice cloning with F5-TTS-THAI, multi-speaker dialogues, Microsoft Edge TTS.
When the user asks Claude to say something, make a voice line, or create a dialogue, call the
CLI directly (no MCP server, no web app needed). Python is `.venv/Scripts/python` (run setup.bat
if it does not exist). Run commands from the repo root with `PYTHONIOENCODING=utf-8`.

## Generate speech

```
PYTHONIOENCODING=utf-8 .venv/Scripts/python speak.py --text "<Thai text>" --out outputs/<name>.wav
```

- `--voice <id>`: folder in `voices/` (default from `config/settings.json`). `--list` shows voices.
  The repo ships `female` and `example_male` samples; users add their own (often `male` = their
  own voice) through the app's "เพิ่มเสียง" tab. Run `--list` instead of guessing ids.
- `--model <id>`: from `config/models.json` (default `th_v1`). `--list-models` shows them and
  whether each is downloaded. `edge` = Microsoft Edge TTS (online, stock voices, no GPU, fast).
  `th_v2` = Thai v2 IPA (fewer skipped words). `orig_*` = original F5-TTS, English only.
  A model that is not downloaded is fetched on first use (~1.35 GB), so tell the user before using one.
- `--speed 0.5-1.5` (0.8-0.9 if words get skipped), `--nfe 8-64` (F5 quality), `--seed N`.
- `--play` plays it on the PC speakers. Only add it when the user asks to hear it.

The last line prints the saved path. Send the WAV to the user with SendUserFile.

## Generate a dialogue

Write the script to `dialogues/<name>.txt` (UTF-8, one turn per line) and render it:

```
ผช: Deploy คือการเอาเว็บของเราไปวางไว้บน server ให้คนอื่นเข้ามาใช้งานได้
ผญ: แล้วทำไมต้อง Deploy ล่ะ?
```

```
PYTHONIOENCODING=utf-8 .venv/Scripts/python dialogue.py --script dialogues/<name>.txt --out outputs/<name>.wav
```

- Labels: `ผช:`/`male:` -> a male voice (`male` folder first), `ผญ:`/`female:` -> a female voice.
  A voice id/name as label picks that voice. Other names get voice A then B. Unlabelled lines alternate.
- `--a` / `--b` voices, `--pause 0.4`, `--model`, `--speed`, `--nfe`, `--play`, `--check` (split only).
- Output: one combined WAV plus each line in `<out>_lines/`.
- Keep lines short (one or two sentences) and natural spoken Thai.

## Code layout (see docs/EXTENDING.md)

- `vtuber_tts/engine.py` VoiceEngine (one model at a time), `backends/` (f5, edge; add new ones there),
  `models.py`, `voices.py`, `text.py` (pronunciations, script parsing), `stt.py` (faster-whisper),
  `app.py` (Gradio UI, `build_ui()`), `cli.py`.
- Config: `config/models.json` (registry), `config/pronunciations.json` (English -> Thai reading,
  applied for Thai F5 models; add mispronounced terms here), `config/settings.json` (user defaults).
- Heavy files: `models/downloaded/<id>/`, `models/custom/` (user checkpoints, auto-listed),
  `models/whisper/faster-whisper-medium/`.
- The user's own voices and recordings (`voices/*` except samples, `data/`) are private and
  git-ignored. Never add them to git.

## Environment notes

- The F5 model needs ~2 GB of GPU memory; do not run two copies at once on small GPUs (close
  start.bat if generation fails with out-of-memory).
- Package versions are pinned in `constraints.txt`. Always install with `-c constraints.txt`
  so torch, numpy, gradio and pydantic stay compatible. `torchcodec` must stay uninstalled.
