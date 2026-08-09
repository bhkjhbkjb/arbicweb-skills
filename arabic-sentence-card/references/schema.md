# Sentence card schema (data.js)

`data.js` is `window.db = [ <card objects> ];`. Field order below is the order the script emits and
the existing cards use.

## Top-level fields

| field | type | meaning |
|-------|------|---------|
| `id` | int | Unique, sequential. **Script-assigned** (max+1) — don't set it yourself. |
| `theme` | string | Short Chinese topic label, e.g. `"夏天我们将去海边"`. The card's title. |
| `ar` | string | The Arabic sentence, **fully voweled** including case endings. The headline. |
| `py` | string | Transliteration (Latin), sentence-cased, ends with a period. e.g. `"Sanadhhabu ila al-bahri fi as-sayfi."` |
| `zh` | string | Chinese translation, ends with `。`. |
| `type` | string | Sentence type: `动词句` (verbal), `名词句` (nominal), etc. Used as a filter facet. |
| `features` | string[] | 2–4 grammar tags, e.g. `["将来时 Sa","地点状语","时间状语"]`. Power the feature radar + future grammar-topic nav, so reuse existing tag wording where you can. |
| `words` | object[] | Word-by-word breakdown — see below. |
| `syntax` | object | Explanation — see below. |
| `root` | object | Triliteral root + derivations — see below. |
| `module` | string | One of: `基础起步` `句法进阶` `复杂表达` `日常场景` `校园与工作`. |
| `level` | string | One of: `入门` `初级` `中级` `进阶`. |
| `audio` | string | **Script-assigned**: `assets/audio/sentences/<id:04d>.mp3`. |
| `schemaVersion` | int | `2`. Script defaults it. |
| `learningNotes` | object | `{ difficulty, module, summary }`. Script defaults it from level/module/zh. |

## words[] entry

You provide `w`, `pos`, `desc`, `role`. The script adds `surface` (=`w`), `lemma` (=`surface`),
`gloss` (=`desc`), and `key` (=`<surface>__<pos>__<desc>`).

| field | meaning |
|-------|---------|
| `w` | The word/phrase exactly as it appears in `ar` (with its harakat). |
| `pos` | **Coloring bucket — use one of four:** `名词` (blue) · `动词` (rose) · `虚词` (emerald) · `组合` (purple). `组合` = a bound multi-word chunk (preposition+noun, future-prefix+verb, إضافة pair). |
| `desc` | Why this word is shaped/placed this way — the teaching content. One or two sentences, beginner-facing. |
| `role` | Its grammatical job, short: `谓语动词` `主语` `宾语` `地点状语` `时间状语` `否定标记` `介词结构` ... |

Segmentation guidance: split so each colored chunk is a *teachable unit*. A standalone verb/noun is
its own entry. A preposition glued to its object, or a future سَ glued to its verb, is one `组合`
entry — splitting them would teach the wrong boundary.

## syntax object

```json
{
  "overview": "动词先说\"将去\"，后面连续补出地点和时间，是非常常见的基础表达。",
  "pattern": "动词句",
  "beginnerTip": "看到词首的 سَ，先别慌，它只是给动词加上\"将要\"的意思，整句主干仍然是\"我们去海边\"。",
  "details": [
    { "t": "将来时的最短标记", "c": "سَ 直接黏在未完成体前面，通常表示较近的将来。" },
    { "t": "地点先于时间", "c": "这句先说去哪儿，再说什么时候去。" }
  ]
}
```
- `overview`: one plain-Chinese sentence — the gist of how the sentence is built.
- `pattern`: usually mirrors `type`.
- `beginnerTip`: the single most reassuring/unlocking observation. Concrete, not generic.
- `details`: 2–4 `{t (short title), c (explanation)}` zooming into specific grammatical choices.

## root object

```json
{
  "core": "ذ ه ب",
  "mean": "前往、离开",
  "derivations": [
    { "ar": "ذَهَبَ / يَذْهَبُ", "type": "动词 (F1)", "zh": "去、前往" },
    { "ar": "ذِهَاب",            "type": "动名词",     "zh": "前往（动作）" }
  ]
}
```
- `core`: the triliteral (or quadriliteral) root, letters **space-separated**.
- `mean`: the root's core idea in Chinese.
- `derivations`: 3–5 members of the root family. `type` uses forms like `动词 (F1)`..`(F10)`,
  `动名词`, `主动分词 (F4)`, `名词`, `形容词`. Keep them real — this feeds the future 词根词典.

## Input contract for assemble_card.py

Provide a single card object, or `{ "cards": [ <card>, ... ] }` for a batch (ids stay sequential).
Omit `id`, `audio`, `key`, `schemaVersion`, `learningNotes` — the script fills them. You may
include `learningNotes` to override the default summary.

## Gold-standard reference

The first ~10 cards in `data.js` (ids 1–10) are the model. Open them and match their depth,
tone, and segmentation. Card id 1 (`لَا أُحِبُّ الشَّايَ بِالسُّكَّرِ`) and id 2
(`سَنَذْهَبُ إِلَى الْبَحْرِ فِي الصَّيْفِ`) are good templates for verbal sentences.
