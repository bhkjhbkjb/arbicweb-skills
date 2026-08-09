#!/usr/bin/env python3
"""Build or inject a word library into word_libraries.js using the project's conventions.

The model's job is the *extraction* (turn a PDF / xlsx / word list into structured rows).
This script handles the *deterministic* part so every entry comes out identical in shape to
the existing libraries:

  - Arabic diacritization via mishkal when a surface form has no harakat
  - Chinese POS normalized to the app's 10-category taxonomy
  - role inferred from POS (教材名词 / 教材动词 / 教材功能词 / ...)
  - usage `desc` generated from POS + gloss (skipped if the row supplies its own desc)
  - JS block formatted byte-for-byte like existing entries
  - injected into word_libraries.js (replace if the library id already exists, else append)

Input JSON (see references/schema.md for the full contract):

  {
    "library": {
      "id": "library-textbook-xinbian-3",
      "title": "教材词库·新编阿拉伯语第3册",
      "description": "...",            # optional; "共 N 条" auto-appended if it ends with 整理 etc.
      "sourceType": "external_library", # optional, default external_library
      "sourceLabel": "教材词库",        # optional, default 教材词库
      "moduleName": "教材词库"          # optional, default 教材词库
    },
    "words": [
      { "raw": "كتاب", "pos": "名词", "gloss": "书", "lesson": "第一课 ..." },
      { "surface": "مَدْرَسَة", "gloss": "学校", "lesson": "第一课 ..." }
    ]
  }

Usage:
  python build_library.py rows.json --print            # print the JS block, change nothing
  python build_library.py rows.json --inject           # write into word_libraries.js
  python build_library.py rows.json --inject --no-diacritics
"""
import argparse
import json
import re
import sys
from pathlib import Path

for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8")
    except Exception:
        pass

BASE_DIR = Path(__file__).resolve().parents[4]  # .../arbicweb
WORD_LIBRARIES_PATH = BASE_DIR / "word_libraries.js"

HARAKAT = set("ًٌٍَُِّْٰٕٓٔ")
KNOWN_POS = {"名词", "动词", "形容词", "副词", "代词", "介词", "连词", "数词", "短语", "虚词"}

# Common function words that gloss-based heuristics get wrong — keep them authoritative.
FUNCTION_WORD_POS = {
    "من": "代词", "أنت": "代词", "أنتِ": "代词", "أنا": "代词", "هو": "代词", "هي": "代词",
    "نحن": "代词", "هم": "代词", "هن": "代词", "هذا": "代词", "هذه": "代词", "ذلك": "代词",
    "تلك": "代词", "ماذا": "代词", "ما": "代词", "من فضلك": "短语", "كيف": "代词", "أين": "代词",
    "متى": "代词", "كم": "代词", "أي": "代词", "الذي": "代词", "التي": "代词",
    "هل": "虚词", "نعم": "虚词", "لا": "虚词", "يا": "虚词", "إن": "虚词", "أن": "虚词",
    "لم": "虚词", "لن": "虚词", "قد": "虚词", "سوف": "虚词", "كان": "动词",
    "في": "介词", "على": "介词", "إلى": "介词", "عن": "介词", "مع": "介词", "عند": "介词",
    "بين": "介词", "قرب": "介词", "أمام": "介词", "خلف": "介词", "من": "介词", "ب": "介词",
    "ل": "介词", "ك": "介词", "حتى": "介词", "منذ": "介词",
    "و": "连词", "ف": "连词", "ثم": "连词", "أو": "连词", "لكن": "连词", "لأن": "连词",
    "هنا": "副词", "هناك": "副词", "أيضا": "副词", "أيضاً": "副词", "كذلك": "副词", "جدا": "副词", "جداً": "副词",
}


def has_harakat(text: str) -> bool:
    return any(ch in HARAKAT for ch in str(text or ""))


def strip_diacritics(text: str) -> str:
    return "".join(ch for ch in str(text or "") if ch not in HARAKAT)


def normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", str(text or "")).strip()


def normalize_pos(value: str) -> str:
    raw = normalize_text(value)
    if not raw:
        return ""
    if raw in KNOWN_POS:
        return raw
    if raw == "组合":
        return "短语"
    if raw in {"主动分词", "被动分词", "分词"}:
        return "形容词"
    if raw in {"名", "n", "noun"}:
        return "名词"
    if raw in {"动", "v", "verb"}:
        return "动词"
    if raw in {"形", "adj"}:
        return "形容词"
    if raw in {"副", "adv"}:
        return "副词"
    return ""


def infer_role(pos: str) -> str:
    if pos == "动词":
        return "教材动词"
    if pos == "形容词":
        return "教材描述词"
    if pos in {"虚词", "介词", "连词", "副词"}:
        return "教材功能词"
    if pos == "代词":
        return "教材基础词"
    if pos == "短语":
        return "教材短语"
    return "教材名词"


def get_gloss_core(gloss: str) -> str:
    value = normalize_text(gloss)
    value = re.sub(r"（[^）]*）", "", value)
    value = re.sub(r"\([^)]*\)", "", value)
    value = re.split(r"[；;，,]", value)[0].strip()
    return value or normalize_text(gloss)


def build_generic_usage(pos: str, gloss: str) -> str:
    core = get_gloss_core(gloss)
    if "男人名" in gloss or "女人名" in gloss or "人名" in gloss:
        return "专有名词，多作人名使用。"
    if pos == "代词":
        return f"用来指代或提问与“{core}”相关的人、事物或内容。"
    if pos == "介词":
        return f"常和后面的名词或代词连用，表达与“{core}”相关的关系。"
    if pos == "虚词":
        return f"多放在句中起提问、连接、否定、强调等作用，结合上下文理解“{core}”。"
    if pos == "副词":
        return f"用来补充说明动作或状态，表达“{core}”这类语气、程度或时间信息。"
    if pos == "连词":
        return f"用来连接词语或句子，表达“{core}”这样的并列、转折或因果关系。"
    if pos == "数词":
        return f"用来表示数量或顺序，意思是“{core}”。"
    if pos == "短语":
        return f"这是一个固定说法，通常整组使用，整体表示“{core}”。"
    if pos == "动词":
        return f"表示“{core}”这一动作或状态，句中常作谓语。"
    if pos == "形容词":
        return f"常用来描述人或事物的性质、状态或特点，表示“{core}”。"
    return f"常作名词使用，表示“{core}”这类人、事物或概念。"


def resolve_pos(row: dict, surface_bare: str) -> str:
    pos = normalize_pos(row.get("pos"))
    if pos:
        return pos
    if surface_bare in FUNCTION_WORD_POS:
        return FUNCTION_WORD_POS[surface_bare]
    gloss = normalize_text(row.get("gloss"))
    if "人名" in gloss:
        return "名词"
    # Multi-word surface with no POS → most likely a set phrase.
    if " " in surface_bare:
        return "短语"
    return "名词"


def make_surface(row: dict, vocalizer) -> str:
    surface = normalize_text(row.get("surface"))
    raw = normalize_text(row.get("raw") or row.get("word"))
    if surface and has_harakat(surface):
        return surface
    base = surface or raw
    if not base:
        return ""
    if vocalizer is not None and not has_harakat(base):
        try:
            voc = str(vocalizer.tashkeel(base)).strip()
            if voc:
                return voc
        except Exception:
            pass
    return base


def build_word_entry(row: dict, vocalizer) -> dict:
    surface = make_surface(row, vocalizer)
    surface_bare = strip_diacritics(surface)
    pos = resolve_pos(row, surface_bare)
    gloss = normalize_text(row.get("gloss")) or "（待补充释义）"
    lemma = normalize_text(row.get("lemma")) or surface
    desc = normalize_text(row.get("desc")) or build_generic_usage(pos, gloss)
    role = normalize_text(row.get("role")) or infer_role(pos)
    entry = {
        "surface": surface,
        "lemma": lemma,
        "pos": pos,
        "gloss": gloss,
        "desc": desc,
        "role": role,
    }
    lesson = normalize_text(row.get("lesson"))
    if lesson:
        entry["lesson"] = lesson
    return entry


def js_string(value: str) -> str:
    return json.dumps(str(value), ensure_ascii=False)


def format_word_entry(word: dict) -> str:
    fields = [
        f"surface: {js_string(word['surface'])}",
        f"lemma: {js_string(word['lemma'])}",
        f"pos: {js_string(word['pos'])}",
        f"gloss: {js_string(word['gloss'])}",
        f"desc: {js_string(word['desc'])}",
        f"role: {js_string(word['role'])}",
    ]
    if word.get("lesson"):
        fields.append(f"lesson: {js_string(word['lesson'])}")
    return "            { " + ", ".join(fields) + " }"


def format_library_block(library: dict, words: list) -> str:
    word_lines = ",\n".join(format_word_entry(w) for w in words)
    return (
        "        {\n"
        f"        id: {js_string(library['id'])},\n"
        f"        title: {js_string(library['title'])},\n"
        f"        description: {js_string(library['description'])},\n"
        f"        sourceType: {js_string(library.get('sourceType', 'external_library'))},\n"
        f"        sourceLabel: {js_string(library.get('sourceLabel', '教材词库'))},\n"
        f"        moduleName: {js_string(library.get('moduleName', '教材词库'))},\n"
        "        words: [\n"
        f"{word_lines}\n"
        "        ]\n"
        "    }"
    )


def find_object_bounds(content: str, library_id: str):
    marker = f'id: "{library_id}"'
    idx = content.find(marker)
    if idx == -1:
        return None
    start = content.rfind("{", 0, idx)
    if start == -1:
        return None
    depth = 0
    in_string = False
    quote_char = ""
    escaped = False
    for pos in range(start, len(content)):
        ch = content[pos]
        if in_string:
            if escaped:
                escaped = False
            elif ch == "\\":
                escaped = True
            elif ch == quote_char:
                in_string = False
        else:
            if ch in {"'", '"'}:
                in_string = True
                quote_char = ch
            elif ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    return start, pos + 1
    return None


def inject(block: str, library_id: str) -> str:
    content = WORD_LIBRARIES_PATH.read_text(encoding="utf-8")
    bounds = find_object_bounds(content, library_id)
    if bounds:
        start, end = bounds
        new_content = content[:start] + block + content[end:]
        action = "replaced"
    else:
        close = content.rfind("]")
        if close == -1:
            raise SystemExit("word_libraries.js: cannot locate closing ] of the array.")
        head = content[:close].rstrip()
        new_content = head + ",\n" + block + "\n    " + content[close:]
        action = "appended"
    WORD_LIBRARIES_PATH.write_text(new_content, encoding="utf-8")
    return action


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("rows_json", help="Path to the input JSON (library + words).")
    parser.add_argument("--inject", action="store_true", help="Write the block into word_libraries.js.")
    parser.add_argument("--print", dest="do_print", action="store_true", help="Print the JS block to stdout.")
    parser.add_argument("--no-diacritics", action="store_true", help="Do not run mishkal on bare surfaces.")
    args = parser.parse_args()

    payload = json.loads(Path(args.rows_json).read_text(encoding="utf-8"))
    library = payload["library"]
    rows = payload["words"]
    if not library.get("id") or not library.get("title"):
        raise SystemExit("library must have at least id and title.")

    vocalizer = None
    if not args.no_diacritics:
        try:
            from mishkal.tashkeel import TashkeelClass
            vocalizer = TashkeelClass()
        except Exception as exc:
            print(f"[warn] mishkal unavailable ({exc}); keeping source forms.", file=sys.stderr)

    words = [build_word_entry(r, vocalizer) for r in rows]
    words = [w for w in words if w["surface"]]

    if not library.get("description"):
        library["description"] = f"{library['title']}，共 {len(words)} 条。"
    elif "{n}" in library["description"]:
        library["description"] = library["description"].replace("{n}", str(len(words)))

    block = format_library_block(library, words)

    if args.do_print or not args.inject:
        print(block)
    if args.inject:
        action = inject(block, library["id"])
        print(f"[ok] {action} library {library['id']} with {len(words)} words.", file=sys.stderr)


if __name__ == "__main__":
    main()
