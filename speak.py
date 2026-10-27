"""Text to speech from the command line. Run with --help for options.

  python speak.py --text "สวัสดีครับ"
  python speak.py --voice female --model edge --text "สวัสดีค่ะ" --play
"""
import sys

from vtuber_tts.cli import speak_main

if __name__ == "__main__":
    sys.exit(speak_main())
