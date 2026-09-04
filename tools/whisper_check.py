#!/usr/bin/env python3
"""Transcribe existing audio for a list of text ids via OpenAI Whisper and
print it next to the expected text, so a human/agent can spot hallucinated
or missing content (item 7 in the evaluation comments)."""
import json
import os
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from tools.manual_override import load_env  # noqa: E402


def transcribe(mp3_path, api_key):
    result = subprocess.run(
        [
            "curl", "-sS", "https://api.openai.com/v1/audio/transcriptions",
            "-H", f"Authorization: Bearer {api_key}",
            "-F", f"file=@{mp3_path}",
            "-F", "model=whisper-1",
        ],
        capture_output=True, text=True,
    )
    try:
        return json.loads(result.stdout).get("text", f"<ERROR: {result.stdout[:200]}>")
    except Exception:
        return f"<ERROR: {result.stdout[:200]}>"


def main():
    load_env()
    api_key = os.environ["OPENAI_API_KEY"]
    lang = "en-GB"
    texts = json.load(open(os.path.join(ROOT, "content", "i18n", lang, "texts.json")))
    audios = json.load(open(os.path.join(ROOT, "content", "i18n", lang, "audios.json")))
    audio_dir = os.path.join(ROOT, "content", "i18n", lang, "audio")

    ids = sys.argv[1:]
    for tid in ids:
        expected = texts.get(tid, "<no text>")
        fname = audios.get(tid)
        if not fname:
            print(f"{tid}: NO AUDIO MAPPED")
            continue
        path = os.path.join(audio_dir, fname)
        if not os.path.exists(path):
            print(f"{tid}: AUDIO FILE MISSING ({fname})")
            continue
        heard = transcribe(path, api_key)
        print(f"=== {tid} ===")
        print(f"  EXPECTED: {expected}")
        print(f"  HEARD:    {heard}")
        print(flush=True)


if __name__ == "__main__":
    main()
