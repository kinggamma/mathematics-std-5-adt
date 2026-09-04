#!/usr/bin/env python3
"""
Batch-apply manual audio overrides for Chapter Seven (item 11): "@" read as
"each" (or "at" when the text is actually naming the symbol), and "shs"/"sh"
read as "shillings". Scope: every text id belonging to pg130_sec001.html
through pg143_sec001.html (Chapter Seven, financial mathematics).

Skips ids already marked manual, so it's safe to re-run/resume. Saves
audios.json + regen/manifest.json every 10 ids.
"""
import os
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from tools.normalize_speech import normalize_regen_speech_text  # noqa: E402
from tools.chapter7_speech import expand_chapter7  # noqa: E402
from tools.manual_override import load_context, apply_override, save_context  # noqa: E402

# Chapter Seven text ids are prefixed pg130_ through pg143_ (some of those
# page numbers, e.g. pg136/pg140/pg141, have no dedicated HTML file of their
# own — their content lives inside a neighbouring page's file — so match by
# texts.json id prefix rather than by scanning specific filenames).
CHAPTER7_PREFIXES = tuple(f"pg{n:03d}_" for n in range(130, 144))


def collect_ids(texts):
    return {k for k in texts if k.startswith(CHAPTER7_PREFIXES)}


def main():
    lang = "en-GB"
    ctx = load_context(lang)
    texts = ctx["texts"]
    manual_ids = set(ctx["lang_m"].get("manualTextIds", []))

    page_ids = collect_ids(texts)
    candidates = []
    for tid in sorted(page_ids):
        if tid in manual_ids:
            continue
        raw = texts.get(tid)
        if raw is None or not isinstance(raw, str):
            continue
        spoken_base = normalize_regen_speech_text(raw)
        spoken = expand_chapter7(spoken_base)
        if spoken != spoken_base:
            candidates.append((tid, spoken))

    print(f"Chapter 7 candidates needing @/shs overrides: {len(candidates)}", flush=True)

    done = 0
    failed = []
    for i, (text_id, spoken) in enumerate(candidates, start=1):
        attempts = 0
        while True:
            attempts += 1
            try:
                apply_override(ctx, text_id, spoken)
                done += 1
                print(f"OK [{i}/{len(candidates)}] {text_id}: {spoken[:90]!r}", flush=True)
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
