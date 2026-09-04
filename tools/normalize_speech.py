#!/usr/bin/env python3
"""Python port of normalizeRegenSpeechText from tools/regenerate-tts.mjs —
strips tags/entities the same way the real TTS pipeline does, so overrides
can be built from what would actually be spoken."""
import html
import re

TAG_RE = re.compile(r"</?[A-Za-z][^>]*>")


def normalize_regen_speech_text(text):
    if not text:
        return ""
    without_markup = TAG_RE.sub(" ", text)
    decoded = html.unescape(without_markup)
    return re.sub(r"\s+", " ", decoded).strip()
