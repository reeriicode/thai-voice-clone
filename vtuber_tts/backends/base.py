"""Base class for TTS backends.

To add a new TTS engine (e.g. another model or an online API):
  1. Create backends/<name>.py with a subclass of Backend.
  2. Register it in BACKENDS in backends/__init__.py.
  3. Add an entry to config/models.json with "type": "<name>".
See docs/EXTENDING.md for a full example.
"""


class Backend:
    #: Matches "type" in config/models.json
    type = "base"
    #: True if the backend wants the pronunciation dictionary applied (English -> Thai reading)
    uses_pronunciations = False

    def __init__(self, info):
        """info: the model entry from config/models.json. Load the model here."""
        self.info = info

    def speak(self, text, voice, speed=1.0, nfe=32, seed=-1, remove_silence=True):
        """Generate speech.

        text:  text to say (already cleaned by the engine)
        voice: dict from voices.list_voices(): id, ref_audio, ref_text, gender, edge_voice
        Returns (sample_rate, numpy float32 mono wave, seed used or "-").
        """
        raise NotImplementedError

    def close(self):
        """Free memory (GPU) before another backend is loaded."""
