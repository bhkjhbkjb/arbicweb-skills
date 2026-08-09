# Word library schema

## Word entry

Every entry in a library's `words: [...]` array has these fields, in this order:

| field     | required | meaning |
|-----------|----------|---------|
| `surface` | yes | The word **as displayed**, fully diacritized (with harakat). This is what the learner sees big on the card. |
| `lemma`   | yes | Dictionary/base form. For most textbook entries it equals `surface`; differs only when you deliberately list an inflected surface but want the lemma for lookup. |
| `pos`     | yes | Chinese part of speech, from the fixed taxonomy below. The app **colors and filters on these exact strings** — never use an out-of-set value. |
| `gloss`   | yes | Short Chinese meaning. Keep it tight (the headline definition); put nuance in `desc`. |
| `desc`    | yes | One-sentence Chinese usage note. Auto-generated from `pos`+`gloss` if you don't supply it. |
| `role`    | yes | A coarse tag (教材名词 / 教材动词 / ...). Auto-inferred from `pos`. |
| `lesson`  | optional | Lesson heading the word belongs to, e.g. `"第三课 在图书馆"`. Drives lesson grouping in the UI. Omit for thematic (non-textbook) libraries. |

### POS taxonomy (exactly these 10)

`名词` `动词` `形容词` `副词` `代词` `介词` `连词` `数词` `短语` `虚词`

Mapping rules the script applies (so your extracted `pos` is normalized):
- `组合` → `短语`
- `主动分词` / `被动分词` / `分词` → `形容词`
- empty/unknown → looked up in a built-in function-word table (هل→虚词, في→介词, و→连词, هذا→代词, ...);
  multi-word surface → `短语`; otherwise defaults to `名词`.

### role inference (from pos)

| pos | role |
|-----|------|
| 动词 | 教材动词 |
| 形容词 | 教材描述词 |
| 虚词 / 介词 / 连词 / 副词 | 教材功能词 |
| 代词 | 教材基础词 |
| 短语 | 教材短语 |
| 名词 / 数词 / (default) | 教材名词 |

### desc generation (from pos + gloss core)

If you don't supply `desc`, the script generates it. The "gloss core" is the gloss with
parentheticals removed and split on the first separator. Templates:
- 名词 → `常作名词使用，表示“{core}”这类人、事物或概念。`
- 动词 → `表示“{core}”这一动作或状态，句中常作谓语。`
- 形容词 → `常用来描述人或事物的性质、状态或特点，表示“{core}”。`
- 介词 → `常和后面的名词或代词连用，表达与“{core}”相关的关系。`
- 虚词 → `多放在句中起提问、连接、否定、强调等作用，结合上下文理解“{core}”。`
- 代词 → `用来指代或提问与“{core}”相关的人、事物或内容。`
- 短语 → `这是一个固定说法，通常整组使用，整体表示“{core}”。`
- person name (gloss contains 人名/男人名/女人名) → `专有名词，多作人名使用。`

Supply your own `desc` when the source gives richer usage info worth keeping; otherwise let the
template handle it for consistency.

## Library object

```js
{
    id: "library-textbook-xinbian-3",   // unique, kebab; textbooks: library-textbook-xinbian-<n>
    title: "教材词库·新编阿拉伯语第3册",   // shown as the library name
    description: "...，共 N 条。",          // auto-filled if omitted
    sourceType: "external_library",       // keep as-is
    sourceLabel: "教材词库",               // 教材词库 (textbook) | 主题词库 (thematic)
    moduleName: "教材词库",                // groups libraries; textbooks share 教材词库
    words: [ ... ]
}
```

## Input JSON for build_library.py

```json
{
  "library": {
    "id": "library-textbook-xinbian-3",
    "title": "教材词库·新编阿拉伯语第3册",
    "description": "基于新编阿拉伯语第3册整理，共 {n} 条。",
    "sourceLabel": "教材词库",
    "moduleName": "教材词库"
  },
  "words": [
    { "raw": "مَكْتَبَة", "pos": "名词", "gloss": "图书馆", "lesson": "第三课 在图书馆" },
    { "raw": "استعار", "pos": "动词", "gloss": "借（书）", "lesson": "第三课 在图书馆" },
    { "surface": "بِجِدٍّ", "pos": "副词", "gloss": "努力地", "desc": "用来修饰动作，表示“认真、努力地”做某事。", "lesson": "第三课 在图书馆" }
  ]
}
```

- Each word: `raw` **or** `surface` is required (provide `surface` to lock in source harakat).
- `pos`, `gloss`, `lesson`, `lemma`, `desc`, `role` are all optional per-row; the script fills the
  blanks from the rules above.
- `description` may contain `{n}`, replaced with the final word count; if omitted entirely it
  becomes `"<title>，共 N 条。"`.

## Real reference entry (from the live file)

```js
{ surface: "طَالِبٌ", lemma: "طَالِبٌ", pos: "名词", gloss: "学生（男）", desc: "常作名词使用，表示“学生”这类人、事物或概念。", role: "教材名词", lesson: "第四课 艾敏是一个学生" }
```
Match this exactly. The existing `library-textbook-xinbian-1` / `-2` blocks are the gold standard —
open them when in doubt.
