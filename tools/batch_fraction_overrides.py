#!/usr/bin/env python3
"""
Batch-apply manual audio overrides for every texts.json entry containing a
MathML <mfrac>, using tools/mathml_speech.convert_mixed_text to produce
speech with "over" inserted for fractions (item 8 in the evaluation
comments). Skips ids already marked manual, so it's safe to re-run/resume
after an interruption. Saves audios.json + regen/manifest.json every 10 ids.
"""
import json
import os
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from tools.mathml_speech import convert_mixed_text  # noqa: E402
from tools.manual_override import load_context, apply_override, save_context  # noqa: E402


def main():
    lang = "en-GB"
    ctx = load_context(lang)
    texts = ctx["texts"]
    manual_ids = set(ctx["lang_m"].get("manualTextIds", []))

    ids = sorted(k for k, v in texts.items() if isinstance(v, str) and "<mfrac>" in v)
    todo = [k for k in ids if k not in manual_ids]
    print(f"Total fraction ids: {len(ids)}; already manual: {len(ids) - len(todo)}; to do: {len(todo)}", flush=True)

    done = 0
    failed = []
    for i, text_id in enumerate(todo, start=1):
        raw = texts[text_id]
        try:
            spoken = convert_mixed_text(raw)
        except Exception as e:
            print(f"SKIP {text_id}: convert error: {e}", flush=True)
            failed.append(text_id)
            continue

        attempts = 0
        while True:
            attempts += 1
            try:
                apply_override(ctx, text_id, spoken)
                done += 1
                print(f"OK [{i}/{len(todo)}] {text_id}: {spoken[:80]!r}", flush=True)
                break
            except Exception as e:
                if attempts >= 3:
                    print(f"FAIL {text_id} after {attempts} attempts: {e}", flush=True)
                    failed.append(text_id)
                    break
                time.sleep(2 * attempts)

        if i % 10 == 0:
            save_context(ctx)

    save_context(ctx)
    print(f"Done. {done} succeeded, {len(failed)} failed.", flush=True)
    if failed:
        print("Failed ids:", failed, flush=True)


if __name__ == "__main__":
    main()
