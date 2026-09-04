#!/usr/bin/env python3
"""
Generate a "manual" read-aloud audio override: keeps the visible text/HTML
unchanged (e.g. an abbreviation like "km", or a MathML formula) but makes the
book speak different words for that unit, and marks it in regen/manifest.json
so tools/regenerate-tts.mjs never overwrites it back.

CLI usage (single id):
    python3 tools/manual_override.py <textId> "<spoken text>" [--lang en-GB]

Batch usage (many ids without re-reading/writing JSON every call):
    ctx = load_context("en-GB")
    apply_override(ctx, "pg031_n0001", "Pi is equal to ...")
    apply_override(ctx, "pg032_n0014", "Where, pi equals 22 over 7.")
    save_context(ctx)

Reads OPENAI_API_KEY from .env in the project root (or the environment).
"""
import json
import os
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def load_env():
    env_path = os.path.join(ROOT, ".env")
    if os.path.exists(env_path):
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())


def synthesize(text, voice, model, instructions, api_key):
    url = "https://api.openai.com/v1/audio/speech"
    payload = json.dumps({
        "model": model,
        "voice": voice,
        "input": text,
        "instructions": instructions,
        "response_format": "mp3",
    })
    with tempfile.NamedTemporaryFile(suffix=".json", mode="w", delete=False) as pf:
        pf.write(payload)
        payload_path = pf.name
    with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as of:
        out_path = of.name
    try:
        result = subprocess.run(
            [
                "curl", "-sS", "-X", "POST", url,
                "-H", f"Authorization: Bearer {api_key}",
                "-H", "Content-Type: application/json",
                "--data-binary", f"@{payload_path}",
                "-o", out_path,
                "-w", "%{http_code}",
                "--max-time", "60",
            ],
            capture_output=True, text=True,
        )
        if result.returncode != 0:
            raise RuntimeError(f"curl failed: {result.stderr}")
        status = result.stdout.strip()
        with open(out_path, "rb") as f:
            data = f.read()
        if status != "200":
            raise RuntimeError(f"OpenAI TTS returned HTTP {status}: {data[:500]!r}")
        return data
    finally:
        os.unlink(payload_path)
        os.unlink(out_path)


def load_context(lang="en-GB"):
    load_env()
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY not set")

    manifest_path = os.path.join(ROOT, "regen", "manifest.json")
    with open(manifest_path) as f:
        manifest = json.load(f)
    lang_m = manifest["languages"][lang]
    defaults = lang_m.get("defaults", {})

    texts_path = os.path.join(ROOT, "content", "i18n", lang, "texts.json")
    audios_path = os.path.join(ROOT, "content", "i18n", lang, "audios.json")
    audio_dir = os.path.join(ROOT, "content", "i18n", lang, "audio")

    with open(texts_path) as f:
        texts = json.load(f)
    with open(audios_path) as f:
        audios = json.load(f)

    return {
        "lang": lang,
        "api_key": api_key,
        "voice": defaults.get("voice", "alloy"),
        "model": defaults.get("model", "gpt-4o-mini-tts"),
        "instructions": defaults.get("instructions", ""),
        "manifest": manifest,
        "lang_m": lang_m,
        "texts": texts,
        "audios": audios,
        "audio_dir": audio_dir,
        "texts_path": texts_path,
        "audios_path": audios_path,
        "manifest_path": manifest_path,
        "audios_dirty": False,
        "manifest_dirty": False,
    }


def apply_override(ctx, text_id, spoken_text):
    """Synthesize + write audio for text_id, mark it manual in ctx (in memory).
    Call save_context(ctx) periodically / at the end to persist audios.json
    and regen/manifest.json."""
    texts = ctx["texts"]
    audios = ctx["audios"]
    lang_m = ctx["lang_m"]

    if text_id not in texts:
        print(f"WARNING: {text_id} not found in texts.json — proceeding anyway")

    raw_text = texts.get(text_id, "")
    filename = f"{text_id}.mp3"

    audio_bytes = synthesize(spoken_text, ctx["voice"], ctx["model"], ctx["instructions"], ctx["api_key"])
    out_path = os.path.join(ctx["audio_dir"], filename)
    with open(out_path, "wb") as f:
        f.write(audio_bytes)

    audios[text_id] = filename
    ctx["audios_dirty"] = True

    manual_ids = set(lang_m.get("manualTextIds", []))
    manual_ids.add(text_id)
    lang_m["manualTextIds"] = sorted(manual_ids)
    lang_m.setdefault("manualTexts", {})[text_id] = raw_text
    lang_m.setdefault("manualFiles", {})[text_id] = filename
    lang_m.get("entries", {}).pop(text_id, None)
    lang_m.get("entrySettings", {}).pop(text_id, None)
    lang_m.get("entryConfigBaselines", {}).pop(text_id, None)
    ctx["manifest_dirty"] = True

    return len(audio_bytes)


def save_context(ctx):
    if ctx["audios_dirty"]:
        with open(ctx["audios_path"], "w") as f:
            json.dump(ctx["audios"], f, ensure_ascii=False, indent=2)
            f.write("\n")
        ctx["audios_dirty"] = False
    if ctx["manifest_dirty"]:
        with open(ctx["manifest_path"], "w") as f:
            json.dump(ctx["manifest"], f, ensure_ascii=False, indent=2)
            f.write("\n")
        ctx["manifest_dirty"] = False


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(1)
    text_id = sys.argv[1]
    spoken_text = sys.argv[2]
    lang = "en-GB"
    if "--lang" in sys.argv:
        lang = sys.argv[sys.argv.index("--lang") + 1]

    ctx = load_context(lang)
    print(f"Synthesizing {text_id}: {spoken_text!r}")
    size = apply_override(ctx, text_id, spoken_text)
    print(f"Wrote {size} bytes")
    save_context(ctx)
    print(f"Marked {text_id} as manual in regen/manifest.json")


if __name__ == "__main__":
    main()
