"""TTS backends. The "type" of a model in config/models.json picks the class here.

Imports are lazy so an online backend does not have to load torch/F5.
"""
import importlib

# type -> "module:Class" (relative to this package)
BACKENDS = {
    "f5": "f5:F5Backend",
    "edge": "edge:EdgeBackend",
}


def get_backend_class(type_name):
    if type_name not in BACKENDS:
        raise ValueError(f"Unknown backend type '{type_name}'. Known: {', '.join(BACKENDS)}")
    module, cls = BACKENDS[type_name].split(":")
    return getattr(importlib.import_module(f"{__name__}.{module}"), cls)
