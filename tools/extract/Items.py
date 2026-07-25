"""items.json — the item table.

`src/data/items.h` is single-source; there is no `_frlg` twin (DATA-AUDIT 9.3).
894 table entries, of which ITEM_NONE is the null slot, so 893 real items.

Prices are evaluated with `cpp`, not by hand (DATA-AUDIT Q14).  247 of them are C
ternaries on config macros — `(I_PRICE >= GEN_7) ? 200 : 300` — and three more hide
behind `#define APRICORN_PRICE` / `GEM_PRICE` / `TYPE_BOOSTING_PRICE` blocks that are
themselves conditional.  The whole header is preprocessed with the game Makefile's own
flags and `-Werror=undef`, so a config macro this extractor forgot to supply is a hard
error rather than a silent 0; what survives is pure arithmetic that Python evaluates.
Seven entries sit behind feature toggles (the six field-move tools and the Pokevial) and
are only in the output because those toggles are on at this pin — they would vanish, not
appear as disabled, if the toggles flipped.

Absent `.holdEffect` / `.flingPower` / `.sortType` are the C zero-initialiser, not
missing data, so they are emitted as HOLD_EFFECT_NONE / 0 / ITEM_TYPE_UNCATEGORIZED.
`.name`, `.price`, `.description`, `.pocket` and `.type` are present on all 894.

`locations` is emitted null.  It needs the three-mechanism ground-item resolver
(DATA-AUDIT 9.1 — Hoenn reads the item out of `trainer_sight_or_berry_tree_id`, Kanto
out of one central `item_ball_scripts_frlg.inc`, Johto out of 23 scattered per-map
scripts) plus the `giveitem_msg` handling in 9.2, and both need maps.json.  ItemLocations.py
is that pass and rewrites this file after Maps.py; a null here means it has not run.

Shares cpp/expression/aggregate helpers with Species.py — see the note in its docstring.
"""

import os, re, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import Common
import Species
from Common import source, gap
from Species import Preprocessed, blocks, cstr, fields, items, nomark, num, resolve

DEFAULTS = {"holdEffect": "HOLD_EFFECT_NONE", "holdEffectParam": "0",
            "flingPower": "0", "sortType": "ITEM_TYPE_UNCATEGORIZED"}


def item_ids():
    """ITEM_* -> numeric id from the enum, including the TM/HM alias block.

    Most entries are explicitly numbered but a few chain off a marker
    (`ITEM_ORANGE_MAIL = FIRST_MAIL_INDEX`) or run on implicitly, so the counter is
    tracked rather than assumed.
    """
    t = Common.read("include", "constants", "items.h")
    body = t[t.index("enum __attribute__((packed)) Item"):]
    body = body[:body.index("\n};")]
    body = re.sub(r"/\*.*?\*/", "", body, flags=re.S)
    body = re.sub(r"//.*", "", body)
    ids, nxt = {}, 0
    for line in body.split("\n"):
        m = re.match(r"\s*([A-Z_][A-Z_0-9]*)\s*(?:=\s*([^,]+?))?\s*,\s*$", line)
        if not m:
            continue
        name, val = m.group(1), m.group(2)
        n = nxt if val is None else (int(val) if val.isdigit() else ids[val])
        ids[name] = n
        nxt = n + 1
    # The RECURSIVELY(R_ZIP(...)) block below the literals aliases ITEM_TM_<MOVE> onto
    # ITEM_TM<n> in FOREACH_TM order. The item's own .name is "TM01", so the move can
    # only come from this index (DATA-AUDIT 9.4).
    tms, hms = Species.tm_hm_moves()
    for i, m in enumerate(tms):
        ids["ITEM_TM_" + m[5:]] = ids["ITEM_TM%02d" % (i + 1)]
    for i, m in enumerate(hms):
        ids["ITEM_HM_" + m[5:]] = ids["ITEM_HM%02d" % (i + 1)]
    return ids


def machines(ids):
    """item id -> {kind, number, move} for the 50 TMs and 8 HMs that bind to a move.

    Keyed by number because the table indexes them as ITEM_TM_FOCUS_PUNCH while the
    numbering lives on the ITEM_TM01 alias.
    """
    tms, hms = Species.tm_hm_moves()
    out = {}
    for kind, moves in (("TM", tms), ("HM", hms)):
        for i, m in enumerate(moves):
            item = "ITEM_%s%02d" % (kind, i + 1)
            out[ids[item]] = {"kind": kind, "number": i + 1, "move": m, "item": item}
    return out


def strings(text):
    """`const u8 sym[] = _("…")` pointers — the shared descriptions and item names."""
    out = {}
    for m in re.finditer(r"(?:static )?const u8 (\w+)\[\]\s*=\s*(.*?);", nomark(text), re.S):
        out[m.group(1)] = cstr(m.group(2))
    return out


def html(raw, item):
    h = Common.text_to_html(raw)
    bad = Common.assert_decoded(h)
    if bad:
        raise ValueError("undecoded token(s) %r in %s description" % (bad, item))
    return h


def build():
    pp = Preprocessed(Species.cpp("src/data/items.h"))
    ids = item_ids()
    tmhm, shared = machines(ids), strings(pp.text)

    def text(expr, item):
        v = cstr(expr)
        return v if v is not None else shared[expr.strip().rstrip(",")]

    out = []
    for name, body, off in blocks(pp.text, "ITEM"):
        f = fields(body)
        for k, v in DEFAULTS.items():
            f.setdefault(k, v)
        src_file, src_line = pp.where(off)
        out.append({
            "id": name,
            "number": ids[name],
            "name": text(f["name"], name),
            "price": num(f["price"]),
            "description": html(text(f["description"], name), name),
            "pocket": resolve(f["pocket"]),
            "hold_effect": resolve(f["holdEffect"]),
            "hold_effect_param": resolve(f["holdEffectParam"]),
            "fling_power": num(f["flingPower"]),
            "sort_type": resolve(f["sortType"]),
            "machine": tmhm.get(ids[name]),
            "locations": None,
            "gate": None,
            "severity": None,
            "gaps": [
                gap("locations", "filled by ItemLocations.py after Maps.py; null means that "
                                 "pass has not run", "9.1"),
                gap("gate", "progression.json does not exist yet", None),
            ],
            "source": source(src_file, key=name, line=src_line),
        })
    out.sort(key=lambda r: r["number"])
    return {**Common.header(), "items": out}


def verify(payload):
    rows = payload["items"]
    checks = []

    def ck(label, got, want):
        checks.append((label, got, want, got == want))

    ck("item records", len(rows), 894)
    ck("items excluding ITEM_NONE", len([r for r in rows if r["id"] != "ITEM_NONE"]), 893)
    ck("unique ids", len({r["id"] for r in rows}), len(rows))
    ck("unique numbers", len({r["number"] for r in rows}), len(rows))
    ck("machines bound to a move", len([r for r in rows if r["machine"]]), 58)

    # Pocket totals, ITEM_NONE excluded. DATA-AUDIT 9.3 reads 596/93 for ITEMS/KEY_ITEMS
    # because it counted the source text: the five fossils declare POCKET_KEY_ITEMS under
    # a config arm that resolves to POCKET_ITEMS at this pin. Everything else agrees.
    real = [r for r in rows if r["id"] != "ITEM_NONE"]
    for pocket, n in (("POCKET_ITEMS", 597), ("POCKET_TM_HM", 108), ("POCKET_KEY_ITEMS", 92),
                      ("POCKET_BERRIES", 68), ("POCKET_POKE_BALLS", 28)):
        ck(pocket, len([r for r in real if r["pocket"] == pocket]), n)

    ck("descriptions decoded", len([r for r in rows if r["description"]]), len(rows))
    residual = [r["id"] for r in rows if Common.assert_decoded(r["description"])]
    ck("residual escapes or tokens", len(residual), 0)
    ck("names decoded", len([r for r in rows if r["name"] is not None]), len(rows))
    ck("prices are ints", len([r for r in rows if isinstance(r["price"], int)]), len(rows))

    print("items: %d records, %d priced above zero, %d TM/HM" % (
        len(rows), len([r for r in rows if r["price"]]), len([r for r in rows if r["machine"]])))
    for label, got, want, ok in checks:
        print("%-42s %-8s %s %s" % (label, got, "==" if ok else "!=", want))
    bad = [c for c in checks if not c[3]]
    if bad:
        raise SystemExit("FAIL: %d assertion(s)" % len(bad))


if __name__ == "__main__":
    payload = build()
    verify(payload)
    print(Common.write("items.json", payload))
