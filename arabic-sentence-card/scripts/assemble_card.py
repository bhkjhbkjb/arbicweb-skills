#!/usr/bin/env python3
"""Assemble one or more sentence cards and append them to data.js (window.db).

You (the model) write the linguistic content — the Arabic sentence, translation, word breakdown,
syntax explanation, root. This script fills in the *mechanical* fields so cards stay consistent
with the existing 300:

  - id            -> max existing id + 1 (sequential for a batch)
  - each word.key -> "<surface>__<pos>__<desc>"   (the app's word-identity key)
  - word.surface  -> defaults to word.w; word.lemma -> defaults to surface; word.gloss -> desc
  - audio         -> "assets/audio/sentences/<id:04d>.mp3"
  - schemaVersion -> 2 (if absent)
  - learningNotes -> { difficulty: level, module: module, summary: zh } (if absent)

then appends the card(s) to data.js, matching the file's 4-space indentation.

Input JSON: a single card object, or { "cards": [ <card>, ... ] }.
See references/schema.md for the full card contract.

Usage:
  python assemble_card.py card.json --print     # show the assembled card(s), change nothing
  python assemble_card.py card.json --inject     # append to data.js
After --inject it prints the new ids so you can generate audio:
  python generate_sentence_audio.py --ids <id> [<id> ...]
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
DATA_FILE = BASE_DIR / "data.js"
DATA_PATTERN = re.compile(r"window\.db\s*=\s*(\[.*\])\s*;?\s*$", re.S)

# Field order to mirror the existing cards exactly.
CARD_KEYS = ["id", "theme", "ar", "py", "zh", "type", "features", "words",
             "syntax", "root", "module", "level", "audio", "schemaVersion", "learningNotes"]
WORD_KEYS = ["w", "pos", "desc", "role", "surface", "lemma", "gloss", "key"]


def load_db():
    source = DATA_FILE.read_text(encoding="utf-8")
    match = DATA_PATTERN.search(source.strip())
    if not match:
        raise SystemExit("Cannot parse window.db from data.js.")
    return json.loads(match.group(1)), source


def order_keys(d: dict, order: list) -> dict:
    out = {k: d[k] for k in order if k in d}
    for k, v in d.items():  # keep any extra keys at the end rather than dropping them
        if k not in out:
            out[k] = v
    return out


def assemble_word(word: dict) -> dict:
    w = dict(word)
    surface = w.get("surface") or w.get("w") or ""
    w.setdefault("surface", surface)
    w.setdefault("lemma", surface)
    desc = w.get("desc", "")
    w.setdefault("gloss", desc)
    pos = w.get("pos", "")
    # Always recompute key from canonical parts so favorites/dedup stay stable.
    w["key"] = f"{surface}__{pos}__{desc}"
    return order_keys(w, WORD_KEYS)


def assemble_card(card: dict, new_id: int) -> dict:
    c = dict(card)
    c["id"] = new_id
    c["words"] = [assemble_word(w) for w in c.get("words", [])]
    c["audio"] = f"assets/audio/sentences/{new_id:04d}.mp3"
    c.setdefault("schemaVersion", 2)
    if "learningNotes" not in c:
        c["learningNotes"] = {
            "difficulty": c.get("level", ""),
            "module": c.get("module", ""),
            "summary": c.get("zh", ""),
        }
    return order_keys(c, CARD_KEYS)


def indent_block(text: str, spaces: int) -> str:
    pad = " " * spaces
    return "\n".join(pad + line if line else line for line in text.split("\n"))


def append_cards(source: str, cards: list) -> str:
    close = source.rfind("]")
    if close == -1:
        raise SystemExit("data.js: cannot locate closing ] of window.db.")
    head = source[:close].rstrip()
    blocks = []
    for card in cards:
        body = json.dumps(card, ensure_ascii=False, indent=4)
        blocks.append(indent_block(body, 4))
    insertion = ",\n" + ",\n".join(blocks) + "\n"
    return head + insertion + source[close:]


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("card_json", help="Path to the input card JSON (one card or {cards:[...]}).")
    parser.add_argument("--inject", action="store_true", help="Append assembled card(s) to data.js.")
    parser.add_argument("--print", dest="do_print", action="store_true", help="Print assembled card(s).")
    args = parser.parse_args()

    payload = json.loads(Path(args.card_json).read_text(encoding="utf-8"))
    raw_cards = payload["cards"] if isinstance(payload, dict) and "cards" in payload else [payload]

    db, source = load_db()
    next_id = max((int(c.get("id", 0)) for c in db), default=0) + 1

    assembled = []
    for i, card in enumerate(raw_cards):
        assembled.append(assemble_card(card, next_id + i))

    if args.do_print or not args.inject:
        print(json.dumps(assembled if len(assembled) > 1 else assembled[0], ensure_ascii=False, indent=4))

    if args.inject:
        new_source = append_cards(source, assembled)
        DATA_FILE.write_text(new_source, encoding="utf-8")
        ids = [c["id"] for c in assembled]
        print(f"[ok] appended {len(assembled)} card(s) to data.js: ids {ids}", file=sys.stderr)
        print(f"[next] python generate_sentence_audio.py --ids {' '.join(map(str, ids))}", file=sys.stderr)


if __name__ == "__main__":
    main()
