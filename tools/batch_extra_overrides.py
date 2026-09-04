#!/usr/bin/env python3
"""One-off manual audio overrides found via whisper spot-checks (item 6/7):
- pg044_n0040 / pg049_n0042: repeated dash characters get mangled by the TTS
  (e.g. "574, -, -, -, -, -, -, 581." -> "574-I-I-781."); the word "dash"
  must be spoken instead, even though the visible text keeps the dash glyphs.
- pg046_n0037: same issue with em-dashes.
- pg045_n0015: "(c)" was misheard as "comma" (same class of issue as item 9).
"""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from tools.manual_override import load_context, apply_override, save_context  # noqa: E402

OVERRIDES = {
    "pg044_n0040": "574, dash, dash, dash, dash, dash, dash, 581.",
    "pg044_n0040_easy_read": "574, dash, dash, dash, dash, dash, dash, 581.",
    "pg049_n0042": "31, dash, dash, dash, 47.",
    "pg049_n0042_easy_read": "31, dash, dash, dash, 47.",
    "pg046_n0037": "Write only missing odd numbers in the following pattern: 1003, 1006, 1009, dash, dash, dash, dash.",
    "pg046_n0037_easy_read": "Write only the missing odd numbers in this pattern: 1003, 1006, 1009, dash, dash, dash, dash.",
    "pg045_n0015": "Part c. 92, 97, 96, 98, 99.",
    "pg045_n0015_easy_read": "Part c. 92, 97, 96, 98, 99.",
}


def main():
    ctx = load_context("en-GB")
    for text_id, spoken in OVERRIDES.items():
        apply_override(ctx, text_id, spoken)
        print(f"OK {text_id}: {spoken!r}", flush=True)
    save_context(ctx)
    print("Done.")


if __name__ == "__main__":
    main()
