# Regenerate read-aloud audio (TTS)

This ADT bundle ships a small script that regenerates its read-aloud audio after
you edit the book's text — for example when a coding agent changes a line in
`content/i18n/<lang>/texts.json`.

It is **dependency-free**: it only needs **Node.js 20+**. No `npm install`.

## How it works

Audio is content-addressed. Each spoken unit's cache key is a hash of its
*text + voice + model + instructions + provider*. This bundle records the
baseline key for every unit's current audio in `regen/manifest.json`. When you
run the script it recomputes each unit's key from the **current** text:

- key unchanged (you didn't touch that line) → kept as-is, **no API call**
- key changed (you edited that line) → re-synthesized via the TTS API

So editing one line costs exactly one TTS call; everything else is free. No audio
is duplicated — the audio already in `content/i18n/<lang>/audio/` is the source
of truth for lines you didn't change.

## Steps

1. Edit the text in `content/i18n/<lang>/texts.json`. The reader renders text
   from this file at runtime, so this is the source of truth for what is spoken.
2. Set your API key:

   ```sh
   export OPENAI_API_KEY=sk-...
   ```

3. Preview what would change (no API calls, no cost):

   ```sh
   node tools/regenerate-tts.mjs --dry-run
   ```

4. Regenerate:

   ```sh
   node tools/regenerate-tts.mjs
   ```

   Limit to one language with `--lang es-uy`, or a single unit with
   `--id pg001_n0001`. Add `--force` to re-record even when the text is
   unchanged (e.g. to re-roll one line you didn't like: `--force --id <id>`).

## What it does and doesn't touch

- **Only changed lines** are re-recorded. Unchanged audio is left byte-for-byte
  identical.
- **Word highlighting**: if this book uses highlighting, the script re-runs
  alignment (OpenAI Whisper) for the lines it re-recorded, and also **backfills**
  timings for any line that has audio but no timings yet — so turning highlighting
  on (see below) fills in the whole book. Updates
  `content/i18n/<lang>/timecode/timecode_output.json`; needs `OPENAI_API_KEY`.
- **Manually recorded audio is never overwritten.** If you edited the text of a
  manually recorded line, the script warns you (the recording can't be
  auto-updated) — re-record it in ADT Studio if needed.

## Configuration

`tools/tts.config.json` holds the per-language voice/model/instructions this book
was built with. Change a value there to re-record a whole language in a different
voice, or set `wordHighlighting` to `true` to enable highlighting (the next run
backfills timings for every line). API keys are read from the environment
variables named in that file (never store keys in the file).

## Excluding parts of the book

The `exclude` block controls what is read aloud, book-wide:

```json
"exclude": { "categories": ["answers"], "textIds": [] }
```

- **categories**: `text`, `captions`, `answers` (activity answers), `glossary`,
  `easy-read`. Add one to mute every unit of that type.
- **textIds**: mute individual units (also mutes their `_easy_read` variant).

Add an entry and re-run to remove that audio; remove an entry to generate it
again. (Muted audio files are left on disk but dropped from `audios.json`, so the
reader stops playing them.)

## Provider support

Regenerates **OpenAI** and **Gemini** voices (each language uses whatever
provider the book was built with — see `tools/tts.config.json`).

- **Gemini** uses `GEMINI_API_KEY` for synthesis. Word highlighting still uses
  `OPENAI_API_KEY` (Whisper), so a Gemini book with highlighting needs **both**
  keys set.
- Gemini books built with page-batched synthesis (one request per page, for tone
  consistency) are re-recorded line-by-line here, so a re-recorded line's tone may
  differ slightly from its unedited page neighbours; the script warns when this
  applies. Regenerate the page/book in ADT Studio for exact parity.
- **Azure** languages are recognized but not yet regeneratable here — regenerate
  those from within ADT Studio.

## Notes

- Regenerated files are not re-compressed the way ADT Studio compresses its
  output, so a re-recorded line may differ slightly in size/encoding from the
  originals. This does not affect playback.
