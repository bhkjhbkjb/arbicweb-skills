---
name: arabic-sentence-card
description: >-
  Author new Arabic sentence cards (例句/句卡) for the 阿拉伯语研究舱 app and append them to data.js.
  Use this whenever the user wants to add example sentences, generate practice sentences for a
  grammar point or vocabulary word, expand the 核心句库/sentence corpus, or create cards
  demonstrating a feature like 宾格/将来时/否定. Each card carries a full word-by-word breakdown
  (POS coloring), syntax explanation, and triliteral-root derivations — this skill encodes that
  structure, the POS color buckets, the word-key format, and the audio convention so new cards
  match the existing 300 and render correctly. Trigger even when the user just says "make a few
  sentences for لقاء" or "add a card about the dual".
---

# Arabic sentence card authoring

A sentence card is a richly annotated example: one Arabic sentence, broken down word-by-word with
parts of speech, explained grammatically for a beginner, and tied to a triliteral root with its
derivations. The app turns this into the colored "拆句" (sentence-dissection) view.

Your job is the **linguistics** — compose correct Modern Standard Arabic, segment it, explain why
each piece is shaped the way it is. The bundled script handles the mechanical fields (id, word
keys, audio path, defaults) and the data.js injection.

## Workflow

1. **Decide the target.** A theme, a vocabulary word, or a grammar feature to demonstrate. If
   building several, vary structure (verbal vs. nominal sentence, different features) rather than
   trivial word-swaps — the corpus teaches *patterns*.

2. **Compose the sentence.** Fully voweled MSA (all harakat, including case endings — the app
   teaches 变尾/inflection, so endings must be correct and visible). Keep it natural and at the
   stated level. Read `references/schema.md` for every field's contract and a fully annotated
   example before your first card.

3. **Break it down.** Produce `words[]` — one entry per word *or* tightly-bound phrase. For each:
   `w` (the surface as it appears in the sentence), `pos`, `desc` (why it's shaped this way), and
   `role` (its job in the sentence). The script fills `surface`/`lemma`/`gloss`/`key`.
   - **`pos` drives coloring.** The view colors exactly four buckets: `名词` (blue), `动词` (rose),
     `虚词` (emerald), `组合` (purple, for a multi-word chunk like a preposition + its noun).
     Use these four. A preposition fused with its noun (`إِلَى الْمَكْتَبَةِ`) is `组合`.

4. **Explain the syntax.** `syntax.overview` (one-line plain-Chinese gist), `pattern` (e.g. 动词句),
   `beginnerTip` (the one thing that unlocks the sentence — reassuring, concrete), and `details[]`
   (`{t, c}` pairs zooming into specific choices: why this ending, why this order). Write like
   you're talking a nervous beginner through it, not like a grammar reference.

5. **Add the root.** Pick the sentence's key word, give its triliteral `root.core` (spaced letters
   like `ذ ه ب`), `mean`, and 3–5 `derivations` (`{ar, type, zh}`) showing the root's family.

6. **Assemble & inject.** `--print` first, review, then `--inject`:
   ```bash
   python .claude/skills/arabic-sentence-card/scripts/assemble_card.py card.json --print
   python .claude/skills/arabic-sentence-card/scripts/assemble_card.py card.json --inject
   ```
   It assigns the next `id`, computes each word `key`, sets the audio path, and appends to data.js.

7. **Generate audio.** The script prints the exact command with the new ids:
   ```bash
   python generate_sentence_audio.py --ids 301 302
   ```

8. **Verify.** Confirm data.js still parses, the new card renders in the 拆句 view, every word is
   colored (no word left uncolored = a `pos` outside the four buckets), and the audio plays.

## What makes a good card (the bar)

The existing 300 are the standard. A card earns its place when:
- The Arabic is **correct and idiomatic**, with accurate case endings — wrong 变尾 in a grammar
  product is worse than no card.
- The breakdown **explains the surprising part**. Beginners get stuck on why a noun is accusative
  or where a سَ came from; the `desc`/`details` should resolve exactly that.
- The `beginnerTip` removes one specific fear ("看到词首的 سَ 别慌，它只是加上'将要'").
- The root derivations are **real** and useful, not padded.

## Why the script, not free-form JSON

`key` (`surface__pos__desc`) identifies words for favorites and cross-card linking; `id` and the
zero-padded audio path must be exact; field order mirrors the existing cards. One small drift
(a stray key format, a missing `schemaVersion`) and word-favorites or audio silently break. The
script makes those impossible to get wrong, so you can focus entirely on the Arabic.

Never invent Arabic you're unsure of. If a case ending or a root derivation is uncertain, flag it
to the user rather than committing a confident-looking error into a paid corpus.
