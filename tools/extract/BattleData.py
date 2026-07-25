"""battledata.json — the lookup tables a trainer card and an encounter table render from.

trainers.json and encounters.json name SPECIES_*, MOVE_* and ITEM_* constants and nothing
else.  This module resolves those constants to display text.  Real sources, all read at the
pinned commit:

  moves      src/data/moves_info.h          (gMovesInfo)
  aliases    include/constants/moves.h      (enum Move — 21 legacy names alias real moves)
  types      src/data/types_info.h          (gTypesInfo) + include/constants/pokemon.h (enum Type)
  chart      src/data/types_info.h          (gTypeEffectivenessTable)
  abilities  src/data/abilities.h           (gAbilitiesInfo)
  species    data/generated/species.json, falling back to src/data/pokemon/species_info.h
  items      data/generated/items.json

Config ternaries (`.type = B_UPDATED_MOVE_TYPES >= GEN_2 ? … : …`) are resolved by the cpp
machinery in Species.py, not hand-evaluated.

The point of the module is the coverage assertion: every SPECIES_* and MOVE_* any party or
encounter slot names must resolve to a display NAME here, or the run fails.  A constant that
does not resolve renders as a raw `MOVE_HI_JUMP_KICK` on a published page.
"""

import functools, json, os, re, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import Common
from Common import read, source, gap
import Species as S

MOVES_H = "src/data/moves_info.h"
MOVE_ENUM_H = ("include", "constants", "moves.h")
TYPES_H = "src/data/types_info.h"
TYPE_ENUM_H = ("include", "constants", "pokemon.h")
ABILITIES_H = "src/data/abilities.h"
SPECIES_H = "src/data/pokemon/species_info.h"

CATEGORY = {
    "DAMAGE_CATEGORY_PHYSICAL": "physical",
    "DAMAGE_CATEGORY_SPECIAL": "special",
    "DAMAGE_CATEGORY_STATUS": "status",
}

_UQ = re.compile(r"UQ_4_12\(([0-9.]+)\)")


def generated(name):
    with open(os.path.join(Common.OUT, name), encoding="utf-8") as f:
        return json.load(f)


# --- moves -------------------------------------------------------------------


def aliases():
    """MOVE_X = MOVE_Y in enum Move. Chains resolved; 21 legacy names at this pin.

    .party files really do use them: MOVE_FAINT_ATTACK, MOVE_HI_JUMP_KICK and
    MOVE_VICE_GRIP are named by trainer parties and have no gMovesInfo entry of their own.
    """
    t = read(*MOVE_ENUM_H)
    out = {}
    for i, ln in enumerate(t.split("\n")):
        m = re.match(r"\s*(MOVE_\w+)\s*=\s*(MOVE_\w+)\s*,", ln)
        if m:
            out[m.group(1)] = (m.group(2), i + 1)
    for k in list(out):
        seen, tgt, line = {k}, out[k][0], out[k][1]
        while tgt in out and tgt not in seen:
            seen.add(tgt)
            tgt = out[tgt][0]
        out[k] = (tgt, line)
    return out


def moves():
    pp = S.Preprocessed(S.cpp(MOVES_H))
    out = {}
    for name, body, off in S.blocks(pp.text, "MOVE"):
        if name in out:
            raise ValueError("duplicate move entry %s" % name)
        f = S.fields(body)
        cat = S.resolve(f["category"])
        file, line = pp.where(off)
        out[name] = {
            "name": S.cstr(f["name"]),
            "type": S.resolve(f["type"]),
            "category": CATEGORY[cat],
            "power": S.num(f["power"]),
            "accuracy": S.num(f["accuracy"]),
            "pp": S.num(f["pp"]),
            "alias_of": None,
            "source": source(file, key=name, line=line),
        }
    for a, (tgt, line) in aliases().items():
        if a in out or tgt not in out:
            continue
        out[a] = dict(out[tgt], alias_of=tgt,
                      source=source("/".join(MOVE_ENUM_H), key=a, line=line))
    return out


# --- types -------------------------------------------------------------------


def type_order():
    """TYPE_* in enum order. Ordinals are the column index of the effectiveness table."""
    t = read(*TYPE_ENUM_H)
    body = t[t.index("enum __attribute__((packed)) Type"):]
    body = body[:body.index("};")]
    if "NUMBER_OF_MON_TYPES" not in body:
        raise ValueError("enum Type has no NUMBER_OF_MON_TYPES terminator")
    pairs = re.findall(r"^\s*(TYPE_\w+)\s*=\s*(\d+),", body, re.M)
    if [int(v) for _, v in pairs] != list(range(len(pairs))):
        raise ValueError("enum Type ordinals are not contiguous from 0")
    return [n for n, _ in pairs]


def types():
    """Returns (types, chart, problem). `chart` is None when it could not be parsed cleanly."""
    order = type_order()
    t = S.cpp(TYPES_H)
    cut = t.index("gTypesInfo")
    out = {}
    for name, body, off in S.blocks(t[cut:], "TYPE"):
        out[name] = {
            "name": S.cstr(S.fields(body)["name"]),
            "ordinal": order.index(name),
            "source": source(TYPES_H, key=name, line=None),
        }
    if sorted(out) != sorted(order):
        return out, None, "gTypesInfo entries do not match enum Type"
    return (out,) + chart(t[t.index("gTypeEffectivenessTable"):cut], order)


def chart(text, order):
    """attacker -> defender -> multiplier. Bail rather than emit a wrong multiplier."""
    rows = list(S.blocks(text, "TYPE"))
    if len(rows) != len(order):
        return None, "%d rows for %d types" % (len(rows), len(order))
    out = {}
    for name, body, _ in rows:
        cells = S.items(body)
        if len(cells) != len(order):
            return None, "%s has %d columns for %d types" % (name, len(cells), len(order))
        row = {}
        for i, c in enumerate(cells):
            m = _UQ.fullmatch(S.resolve(c).strip())
            if not m:
                return None, "unparsed cell %s -> %s: %r" % (name, order[i], c.strip())
            row[order[i]] = float(m.group(1))
        out[name] = row
    return out, None


# --- abilities ---------------------------------------------------------------


def abilities():
    pp = S.Preprocessed(S.cpp(ABILITIES_H))
    out = {}
    for name, body, off in S.blocks(pp.text, "ABILITY"):
        f = S.fields(body)
        d = Common.text_to_html(S.cstr(f["description"]))
        bad = Common.assert_decoded(d)
        if bad:
            raise ValueError("undecoded token(s) %r in %s description" % (bad, name))
        file, line = pp.where(off)
        out[name] = {
            "name": S.cstr(f["name"]),
            "description": d,
            "source": source(file, key=name, line=line),
        }
    return out


# --- species and items -------------------------------------------------------


@functools.lru_cache(maxsize=1)
def species_source():
    """species_info.h. Covers the two entries species.json drops for having no family guard:
    SPECIES_NONE (which 82 encounter slots really do name) and SPECIES_EGG."""
    pp = S.Preprocessed(S.cpp(SPECIES_H, extra_includes=["metaprogram.h", S._famforce()]))
    return pp, {n: (b, o) for n, b, o in S.blocks(pp.text, "SPECIES")}


def from_species_info(name):
    pp, blocks = species_source()
    if name not in blocks:
        return None
    body, off = blocks[name]
    f = S.fields(body)
    file, line = pp.where(off)
    r = {"name": None, "types": None, "base_stats": None, "gaps": [],
         "source": source(file, key=name, line=line)}
    if "speciesName" in f:
        r["name"] = S.cstr(f["speciesName"])
    else:
        r["gaps"].append(gap("name", "no .speciesName in %s" % SPECIES_H))
    if "types" in f:
        ts = [S.resolve(x) for x in S.items(f["types"].strip("{}"))]
        r["types"] = {"primary": ts[0], "secondary": ts[1] if ts[1] != ts[0] else None}
    else:
        r["gaps"].append(gap("types", "no .types in %s; C zero-init is not an authored value"
                             % SPECIES_H))
    keys = [("hp", "baseHP"), ("attack", "baseAttack"), ("defense", "baseDefense"),
            ("sp_attack", "baseSpAttack"), ("sp_defense", "baseSpDefense"), ("speed", "baseSpeed")]
    if all(k in f for _, k in keys):
        r["base_stats"] = {a: S.num(f[b]) for a, b in keys}
    else:
        r["gaps"].append(gap("base_stats", "base stat fields absent from %s" % SPECIES_H))
    return r


def species(extra):
    out = {}
    for r in generated("species.json")["species"]:
        out[r["id"]] = {
            "name": r["name"],
            "types": r["types"],
            "base_stats": r["base_stats"],
            "gaps": [],
            "source": r["source"],
        }
    for name in sorted(extra - set(out)):
        r = from_species_info(name)
        if r:
            out[name] = r
    return out


def items():
    return {
        r["id"]: {"name": r["name"], "source": r["source"]}
        for r in generated("items.json")["items"]
    }


# --- references --------------------------------------------------------------


def referenced():
    """SPECIES_*, MOVE_* and ITEM_* named by any party or encounter slot."""
    sp, mv, it = set(), set(), set()
    t = generated("trainers.json")
    for r in t["trainers"] + t["frontier_trainers"]:
        for i in r.get("items") or []:
            it.add(i)
        for p in r.get("party") or []:
            sp.add(p["species"])
            mv.update(p.get("moves") or [])
            if p.get("held_item"):
                it.add(p["held_item"])
    for r in generated("encounters.json")["encounters"]:
        for method in r["methods"].values():
            groups = list(method.get("rods", {}).values()) or [method]
            for grp in groups:
                for s in grp.get("slots") or []:
                    sp.add(s["species"])
    return sp, mv, it


# --- build -------------------------------------------------------------------


def build():
    ref_sp, ref_mv, ref_it = referenced()
    ty, ch, problem = types()
    payload = {
        **Common.header(),
        "abilities": abilities(),
        "items": items(),
        "moves": moves(),
        "species": species(ref_sp),
        "types": ty,
        "type_chart": ch,
        "table_sources": {
            "abilities": ABILITIES_H,
            "items": "data/generated/items.json",
            "moves": MOVES_H,
            "move_aliases": "/".join(MOVE_ENUM_H),
            "species": "data/generated/species.json",
            "species_fallback": SPECIES_H,
            "type_chart": TYPES_H,
            "types": TYPES_H,
        },
        "gaps": [],
    }
    if ch is None:
        payload["gaps"].append(gap("type_chart", "gTypeEffectivenessTable did not parse "
                                                 "cleanly (%s); omitted rather than guessed"
                                   % problem))
    payload["coverage"] = {
        "species_referenced": len(ref_sp),
        "moves_referenced": len(ref_mv),
        "items_referenced": len(ref_it),
        "species_total": len(payload["species"]),
        "moves_total": len(payload["moves"]),
        "items_total": len(payload["items"]),
        "abilities_total": len(payload["abilities"]),
        "types_total": len(payload["types"]),
    }
    return payload, (ref_sp, ref_mv, ref_it)


# --- verify ------------------------------------------------------------------


def unresolved(refs, table):
    """Referenced constants with no record, or a record with no display name."""
    return sorted(k for k in refs if not (table.get(k) or {}).get("name"))


def verify(payload, refs):
    ref_sp, ref_mv, ref_it = refs
    checks = []

    def ck(label, got, want):
        checks.append((label, got, want, got == want))

    miss_sp = unresolved(ref_sp, payload["species"])
    miss_mv = unresolved(ref_mv, payload["moves"])
    miss_it = unresolved(ref_it, payload["items"])
    if miss_sp or miss_mv or miss_it:
        raise SystemExit("FAIL: unresolved constants\n  species: %s\n  moves: %s\n  items: %s"
                         % (miss_sp, miss_mv, miss_it))

    alias = sum(1 for m in payload["moves"].values() if m["alias_of"])
    ck("gMovesInfo entries", len(payload["moves"]) - alias, 935)
    ck("move aliases", alias, 21)
    ck("ability records", len(payload["abilities"]), 319)
    ck("type records", len(payload["types"]), 21)
    ck("species records", len(payload["species"]), 1572)
    ck("item records", len(payload["items"]), 894)
    ck("type chart parsed", payload["type_chart"] is not None, True)
    if payload["type_chart"]:
        ck("chart rows", len(payload["type_chart"]), len(payload["types"]))
        ck("chart cells", sum(len(r) for r in payload["type_chart"].values()),
           len(payload["types"]) ** 2)
        ck("chart multipliers", sorted({v for r in payload["type_chart"].values()
                                        for v in r.values()}), [0.0, 0.5, 1.0, 2.0])

    ck("moves with a name", sum(1 for m in payload["moves"].values() if m["name"]),
       len(payload["moves"]))
    ck("moves with a category", sum(1 for m in payload["moves"].values()
                                    if m["category"] in CATEGORY.values()), len(payload["moves"]))
    ck("move types in the type table", sorted({m["type"] for m in payload["moves"].values()}
                                              - set(payload["types"])), [])
    ck("abilities with a description", sum(1 for a in payload["abilities"].values()
                                           if a["description"]), len(payload["abilities"]))
    ck("species types in the type table",
       sorted({t for s in payload["species"].values() if s["types"]
               for t in s["types"].values() if t} - set(payload["types"])), [])

    print("coverage: %d/%d species, %d/%d moves, %d/%d items referenced by parties and "
          "encounter slots all resolve to a display name"
          % (len(ref_sp), len(ref_sp), len(ref_mv), len(ref_mv), len(ref_it), len(ref_it)))
    for label, got, want, ok in checks:
        print("%-42s %-8s %s %s" % (label, got, "==" if ok else "!=", want))
    bad = [c for c in checks if not c[3]]
    if bad:
        raise SystemExit("FAIL: %d assertion(s)" % len(bad))


if __name__ == "__main__":
    payload, refs = build()
    verify(payload, refs)
    print(Common.write("battledata.json", payload))
