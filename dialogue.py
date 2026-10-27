"""Render a dialogue script into one conversation WAV. Run with --help for options.

  python dialogue.py --script dialogues/deploy.txt
"""
import sys

from vtuber_tts.cli import dialogue_main

if __name__ == "__main__":
    sys.exit(dialogue_main())
