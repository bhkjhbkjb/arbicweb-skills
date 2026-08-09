---
name: arabic-vocab-ingest
description: >-
  Turn raw Arabic vocabulary material (PDF textbooks, xlsx word lists, plain-text glossaries,
  screenshots) into properly formatted word libraries inside word_libraries.js for the
  阿拉伯语研究舱 app. Use this whenever the user wants to add vocabulary, build a new 词库/word
  library, expand the 教材词库, ingest a 新编阿拉伯语 textbook volume, or process a vocab list/PDF/
  Excel into the app — even if they just drop a file in material_uploads/ and say "add these
  words". Handles Arabic diacritization (tashkeel), Chinese POS tagging, and the exact JS entry
  format so new words match existing ones.
---

# Arabic vocabulary ingest

Convert source vocabulary into entries in `word_libraries.js`. Your job is the **extraction and
judgement** (read the source, pull out each word + Chinese meaning + which lesson it belongs to,
decide part of speech when it's ambiguous). The bundled script does the **deterministic
formatting** (diacritization, role, usage text, JS shape, injection) so output is consistent
across every run.

## The data shape

`word_libraries.js` is `window.wordLibraries = [ <library objects> ];`. Each library:

```js
{
    id: "library-textbook-xinbian-3",
    title: "教材词库·新编阿拉伯语第3册",
    description: "...，共 N 条。",
    sourceType: "external_library",
    sourceLabel: "教材词库",      // 教材词库 for textbooks, 主题词库 for thematic sets
    moduleName: "教材词库",
    words: [ { surface, lemma, pos, gloss, desc, role, lesson? }, ... ]
}
```

Field meanings and the full POS/role tables are in `references/schema.md` — read it before your
first ingest so the `pos`/`gloss`/`lesson` values you extract line up with the taxonomy.

## Workflow

1. **Locate the source.** Textbooks/material usually live in `material_uploads/`. Confirm the
   filename and which volume/book it is.

2. **Extract structured rows.** Read the source and produce one row per word. For each, capture:
   - `raw` (the Arabic word as written — diacritics optional) **or** `surface` (if it already
     carries full harakat you want to keep verbatim)
   - `gloss` — the concise Chinese meaning from the source
   - `pos` — Chinese part of speech if you can tell (名词/动词/形容词/...); omit if unsure and the
     script will infer it
   - `lesson` — the lesson heading, e.g. `"第三课 在图书馆"`, so words stay grouped by lesson
   See `references/extraction.md` for handling PDFs (RTL order, ligatures, scanned pages → OCR)
   and xlsx.

3. **Write the rows JSON** in the shape `references/schema.md` documents:
   ```json
   { "library": { "id": "...", "title": "...", "moduleName": "教材词库" },
     "words": [ { "raw": "كتاب", "pos": "名词", "gloss": "书", "lesson": "第一课 ..." } ] }
   ```
   Leave `description` out (auto-filled as "<title>，共 N 条。") or include `{n}` as a placeholder
   for the count.

4. **Build / inject.** Always `--print` first and eyeball a sample, then `--inject`:
   ```bash
   python .claude/skills/arabic-vocab-ingest/scripts/build_library.py rows.json --print
   python .claude/skills/arabic-vocab-ingest/scripts/build_library.py rows.json --inject
   ```
   `--inject` replaces the library in place if `id` already exists, otherwise appends a new one.
   It diacritizes any bare surface via mishkal, normalizes POS, infers `role`, and generates the
   usage `desc` — pass `--no-diacritics` only if the source is already fully vocalized and correct.

5. **Generate audio** for the new words (the word view plays pre-generated MP3s):
   ```bash
   python generate_word_audio.py
   ```

6. **Verify.** Re-open `word_libraries.js`, check the new block parses (no trailing-comma issues),
   spot-check 5–10 entries for correct diacritics and sensible glosses, and confirm the word count
   in `description` matches.

## Conventions that matter

- **Respect source diacritics.** If a `surface` already has harakat, the script keeps it. Only
  bare words get auto-vocalized. Textbook diacritics beat machine guesses — prefer extracting them.
- **One library per volume.** Don't merge two textbook volumes into one library; match the
  existing `library-textbook-xinbian-1` / `-2` pattern (`-3`, `-4`, ...).
- **Dedup within a lesson but keep cross-lesson repeats.** A word that genuinely recurs in a later
  lesson can appear again with that lesson tag; true duplicates in the same lesson should be merged.
- **Don't invent glosses.** If the source has no meaning for a word, leave `gloss` empty rather
  than guessing — a flagged gap is better than a wrong definition in a paid product.

## Why it's built this way

The deterministic script exists because three things must be *identical* across thousands of
entries or the app's filters, dedup, and search break: the JS field order/shape, the POS
vocabulary (the app colors and filters on exactly 名词/动词/.../短语/虚词), and the diacritization
source. Letting the model free-format each entry drifts; centralizing it in one script doesn't.
