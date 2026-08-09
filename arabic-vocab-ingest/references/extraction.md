# Extracting vocabulary from source material

The goal of extraction is one clean row per word: the Arabic form, its Chinese gloss, its part of
speech (if knowable), and the lesson it sits under. Quality here determines everything downstream —
the formatting script trusts what you hand it.

## PDF textbooks (the common case)

新编阿拉伯语 volumes are usually text-based PDFs. Read them, but watch for Arabic-specific traps.

1. **Try text extraction first.** Use the `anthropic-skills:pdf` skill, or `pdfplumber` /
   `pdftotext -layout`. Read the actual file before assuming — a scanned PDF needs OCR instead.
2. **RTL ordering.** Extracted Arabic often comes out **visually reversed** or with words in
   logical-vs-visual order swapped. Sanity-check a few words against what you can read on the page.
   If a word looks mirrored or letters are detached wrongly, the extractor mangled it — prefer
   re-typing that word from what you see rather than shipping garbage.
3. **Ligatures & detached forms.** PDF text layers sometimes split a word into presentation-form
   glyphs (ﻻ, ﻤ ...). Normalize to standard Arabic letters; if unsure, re-read the glyph.
4. **Vocab lists vs. prose.** Textbook vocab is usually a two-column table (Arabic ｜ Chinese) per
   lesson, often near the end of each lesson (单词表/الكلمات). Target those tables, not the reading
   passages. Capture the lesson title/number as you go so every row gets a `lesson`.
5. **Diacritics.** Textbook vocab is typically fully voweled. **Keep those harakat** — put the
   voweled form in `surface` so the script doesn't re-guess. Only leave a word bare (`raw`) when
   the source itself is bare.
6. **Scanned pages → OCR.** If there's no text layer, use the pdf skill's OCR path. Arabic OCR is
   imperfect; verify diacritics especially, and flag low-confidence words for the user rather than
   silently committing them.

Work **one lesson at a time** for long volumes — extract a lesson, build/inject, spot-check, move
on. This keeps errors local and reviewable instead of dumping 800 words at once.

## xlsx word lists

`openpyxl` may not be installed. Two options:
- Install it (`python -m pip install openpyxl`) and read normally, **or**
- Parse the raw XML the way `rebuild_xinbian_libraries.py:read_xlsx` does (unzip the .xlsx, read
  `xl/sharedStrings.xml` + `xl/worksheets/sheet1.xml`). That function is a working reference for
  shared-string resolution and column mapping.

Identify which columns hold Arabic, gloss, POS, and lesson, then emit rows.

## Plain text / screenshots

- **Text**: split into rows; infer the Arabic↔Chinese pairing from layout.
- **Images/screenshots**: read them directly (you are multimodal). Transcribe Arabic carefully,
  preserving harakat, and pair with the Chinese gloss beside each word.

## After extraction

Hand the rows to `scripts/build_library.py` (see SKILL.md step 4). Don't hand-format JS entries —
routing through the script is what guarantees the diacritization, POS normalization, and field
shape stay identical to the existing libraries.
