"""All folder and file locations in one place."""
import os
import shutil

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

CONFIG_DIR = os.path.join(ROOT, "config")
MODELS_JSON = os.path.join(CONFIG_DIR, "models.json")              # model registry (committed)
PRONUNCIATIONS_JSON = os.path.join(CONFIG_DIR, "pronunciations.json")  # English -> Thai reading (committed)
SETTINGS_JSON = os.path.join(CONFIG_DIR, "settings.json")          # your saved defaults (not committed)

VOCAB_DIR = os.path.join(ROOT, "assets", "vocab")                  # F5-TTS-THAI vocab files
VOICES_DIR = os.path.join(ROOT, "voices")                          # one folder per voice
DIALOGUES_DIR = os.path.join(ROOT, "dialogues")                    # dialogue scripts
OUTPUTS_DIR = os.path.join(ROOT, "outputs")                        # generated audio

MODELS_DIR = os.path.join(ROOT, "models")
DOWNLOADED_DIR = os.path.join(MODELS_DIR, "downloaded")            # models fetched from Hugging Face
CUSTOM_DIR = os.path.join(MODELS_DIR, "custom")                    # your own trained checkpoints
WHISPER_DIR = os.path.join(MODELS_DIR, "whisper", "faster-whisper-medium")

_BIN_DIR = os.path.join(ROOT, ".bin")


def ensure_ffmpeg():
    """Put an ffmpeg on PATH if there is none (some audio formats need it).

    Uses the binary from the imageio-ffmpeg package, copied as .bin/ffmpeg.exe.
    """
    if os.path.isdir(_BIN_DIR) and _BIN_DIR not in os.environ.get("PATH", ""):
        os.environ["PATH"] = _BIN_DIR + os.pathsep + os.environ.get("PATH", "")
    if shutil.which("ffmpeg"):
        return
    try:
        import imageio_ffmpeg

        os.makedirs(_BIN_DIR, exist_ok=True)
        exe = "ffmpeg.exe" if os.name == "nt" else "ffmpeg"
        target = os.path.join(_BIN_DIR, exe)
        if not os.path.isfile(target):
            shutil.copy(imageio_ffmpeg.get_ffmpeg_exe(), target)
        os.environ["PATH"] = _BIN_DIR + os.pathsep + os.environ.get("PATH", "")
    except Exception:
        pass  # optional: WAV files work without ffmpeg


ensure_ffmpeg()
