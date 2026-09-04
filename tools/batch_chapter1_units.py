#!/usr/bin/env python3
"""
Batch-apply manual audio overrides expanding metric-unit abbreviations
(km, kg, mm, mL, ...) to full words, for every text id that appears in
Chapter One's pages (item 2 in the evaluation comments: pages 7-20, i.e.
pg007_sec001.html through pg018_sec002.html). Visible text/HTML is left
untouched; only the read-aloud audio changes.

Skips ids already marked manual, so it's safe to re-run/resume. Saves
audios.json + regen/manifest.json every 10 ids.
"""
import glob
import json
import os
import re
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from tools.unit_speech import expand_units  # noqa: E402
from tools.normalize_speech import normalize_regen_speech_text  # noqa: E402
from tools.manual_override import load_context, apply_override, save_context  # noqa: E402

CHAPTER1_FILES = [
    "pg007_sec001.html", "pg008_sec001.html", "pg009_sec001.html", "pg010_sec001.html",
    "pg011_sec001.html", "pg012_sec001.html", "pg013_sec001.html", "pg014_sec001.html",
    "pg015_sec001.html", "pg015_sec002.html", "pg016_sec001.html", "pg017_sec001.html",
    "pg018_sec001.html", "pg018_sec002.html",
]

DATA_ID_RE = re.compile(r'data-id="([a-zA-Z0-9_\-]+)"')


def collect_ids():
    ids = set()
    for fname in CHAPTER1_FILES:
        path = os.path.join(ROOT, fname)
        if not os.path.exists(path):
            print(f"WARNING: {fname} missing")
            continue
        s = open(path, encoding="utf-8").read()
        for m in DATA_ID_RE.finditer(s):
            ids.add(m.group(1))
    return ids


def main():
    lang = "en-GB"
    ctx = load_context(lang)
    texts = ctx["texts"]
    manual_ids = set(ctx["lang_m"].get("manualTextIds", []))

    page_ids = collect_ids()
    candidates = []
    for base_id in sorted(page_ids):
        for tid in (base_id, base_id + "_easy_read"):
            if tid in manual_ids:
                continue
            raw = texts.get(tid)
            if raw is None or not isinstance(raw, str):
                continue
            spoken_base = normalize_regen_speech_text(raw)
            spoken = expand_units(spoken_base)
            if spoken != spoken_base:
                candidates.append((tid, spoken))

    print(f"Chapter 1 candidates needing unit-abbreviation overrides: {len(candidates)}", flush=True)

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
