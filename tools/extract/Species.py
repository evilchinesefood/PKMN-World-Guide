"""species.json — the species roster, enablement, evolutions and learnsets.

Enablement (DATA-AUDIT 5A): a species is enabled iff the innermost `#if P_FAMILY_*`
enclosing its `[SPECIES_X] = {` is not `#define`d FALSE in config/species_enabled.h.
The guard stack below mirrors game/Testing/ValidateGen13.py, which is run as a
cross-check.  At pin 9ee61fbd: 539 families, 339 disabled, 200 enabled, 1571 species.

Config-dependent values (`#if` arms inside EVOLUTION(...), `?:` in .types, the
level-up-learnset generation selector) are resolved by shelling out to `cpp` with the
game Makefile's own flags and `-Werror=undef`, so an unsupplied config macro is a hard
error rather than a silent 0.  Family guards are forced TRUE for that pass only, so
disabled species still land in the output carrying `enabled: false`; enablement itself
never comes from cpp.

`src/data/pokemon/teachable_learnsets.h` is a gitignored build artifact.  The TM and
tutor columns are rebuilt here from the tracked inputs make_teachables.py uses:
all_learnables.json, constants/tms_hms.h, special_movesets.json, the `.teachingType`
in species_info, and the three tutor scripts.

`obtainable_via` is null pending the encounter/trainer/script cross-reference that
separates evolution-only from unreachable (DATA-AUDIT 9.6).  `gate`/`severity` are
null pending progression.json.

NOTE: `cpp()`, `CONFIG`/`DEFINES`, `resolve`/`num`, `fields`/`items`, `cstr` and
`tm_hm_moves()` are shared machinery, imported by Items.py.  They live here per the
brief; hoist them to Common.py once the concurrent extractors have landed.
"""

import functools, glob, os, re, subprocess, sys, tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import Common
from Common import g, read, source, gap


# --- cpp ---------------------------------------------------------------------
# Flags mirror the game Makefile (ASFLAGS/CPPFLAGS, ~line 155-166).  constants/global.h
# supplies TRUE/FALSE, constants/flags.h is needed by config/item.h, metaprogram.h
# supplies DEFAULT() used by MON_TYPES.

DEFINES = ["MODERN=1", "TESTING=0", "EMERALD", "ALL_REGIONS=1"]
CONFIG = ["constants/global.h", "constants/flags.h"] + sorted(
    "config/" + os.path.basename(p) for p in glob.glob(g("include", "config", "*.h"))
) + ["metaprogram.h"]


def cpp(path, extra_includes=(), extra_defines=()):
    cmd = ["cpp", "-nostdinc", "-iquote", "include", "-I", "include", "-I", "src"]
    cmd += ["-Wundef", "-Werror=undef"]
    cmd += ["-D" + d for d in list(DEFINES) + list(extra_defines)]
    for h in list(CONFIG) + list(extra_includes):
        cmd += ["-include", h]
    cmd.append(path)
    r = subprocess.run(cmd, cwd=Common.GAME, capture_output=True, text=True)
    if r.returncode:
        raise RuntimeError("cpp failed on %s:\n%s" % (path, r.stderr))
    return r.stdout


class Preprocessed:
    """cpp output plus a map from any offset back to (source file, source line)."""

    def __init__(self, text):
        self.text = text
        self.starts = [0]
        for i, c in enumerate(text):
            if c == "\n":
                self.starts.append(i + 1)
        self.marks = []  # (output line index, file, source line at that point)
        for i, ln in enumerate(text.split("\n")):
            m = re.match(r'# (\d+) "([^"]+)"', ln)
            if m:
                self.marks.append((i, m.group(2), int(m.group(1))))

    def where(self, pos):
        lo, hi = 0, len(self.starts)
        while lo < hi - 1:
            mid = (lo + hi) // 2
            if self.starts[mid] <= pos:
                lo = mid
            else:
                hi = mid
        line = lo
        mark = None
        for m in self.marks:
            if m[0] <= line:
                mark = m
            else:
                break
        if not mark:
            return None, None
        return mark[1], mark[2] + (line - mark[0] - 1)


@functools.lru_cache(maxsize=1)
def _famforce():
    """A -include header forcing every P_FAMILY_* on, so cpp keeps disabled species."""
    fams = re.findall(r"^#define\s+(P_FAMILY_\w+)", read("include", "config", "species_enabled.h"), re.M)
    body = "".join("#undef %s\n#define %s 1\n" % (f, f) for f in sorted(set(fams)))
    fd, p = tempfile.mkstemp(suffix=".h", prefix="famforce")
    with os.fdopen(fd, "w") as f:
        f.write(body)
    return p


# --- C expression helpers ----------------------------------------------------
# After cpp every config macro is a literal, so ternaries reduce to a chosen branch.

_SAFE = re.compile(r"^[0-9\s()+\-*/%<>=!&|]+$")


def _scan(s, want, depth=0):
    """Index of the first `want` char at nesting depth 0, or -1. Skips strings."""
    d, q, i = depth, None, 0
    while i < len(s):
        c = s[i]
        if q:
            if c == "\\":
                i += 2
                continue
            if c == q:
                q = None
        elif c in "\"'":
            q = c
        elif d == 0 and c == want:  # before the depth update, so want=')' finds its own close
            return i
        elif c in "([{":
            d += 1
        elif c in ")]}":
            d -= 1
        i += 1
    return -1


def _stripped(s):
    s = s.strip()
    while s.startswith("(") and _scan(s[1:], ")") == len(s) - 2:
        s = s[1:-1].strip()
    return s


def resolve(s):
    """Collapse C ternaries whose condition is a pure numeric expression."""
    s = _stripped(s)
    q = _scan(s, "?")
    if q < 0:
        return s
    rest, depth, i = s[q + 1:], 0, 0
    while i < len(rest):  # the matching ':' is the first at ternary depth 0
        j = _scan(rest[i:], "?")
        k = _scan(rest[i:], ":")
        if k < 0:
            raise ValueError("unbalanced ternary: %r" % s)
        if 0 <= j < k:
            depth += 1
            i += j + 1
            continue
        if depth == 0:
            break
        depth -= 1
        i += k + 1
    colon = q + 1 + i + _scan(rest[i:], ":")
    return resolve(s[q + 1:colon]) if num(s[:q]) else resolve(s[colon + 1:])


def num(s):
    s = resolve(s)
    if not _SAFE.match(s):
        raise ValueError("not a numeric C expression: %r" % s)
    return eval(s.replace("&&", " and ").replace("||", " or ").replace("/", "//"), {"__builtins__": {}})


# --- C aggregate helpers -----------------------------------------------------


def _close(s, i):
    """Index just past the brace/paren group starting at s[i]. Skips strings."""
    pairs = {"{": "}", "(": ")", "[": "]"}
    d, q, j = 0, None, i
    while j < len(s):
        c = s[j]
        if q:
            if c == "\\":
                j += 2
                continue
            if c == q:
                q = None
        elif c in "\"'":
            q = c
        elif c in pairs:
            d += 1
        elif c in pairs.values():
            d -= 1
            if d == 0:
                return j + 1
        j += 1
    raise ValueError("unbalanced group at %d" % i)


def items(s):
    """Top-level comma-separated pieces of s."""
    out, start, i = [], 0, 0
    while True:
        j = _scan(s[i:], ",")
        if j < 0:
            break
        i += j
        out.append(s[start:i])
        i += 1
        start = i
    if s[start:].strip():
        out.append(s[start:])
    return [p.strip() for p in out if p.strip()]


def fields(body):
    """Designated initialisers of a struct body, as {name: value-text}."""
    out = {}
    for part in items(body):
        m = re.match(r"\.(\w+)\s*=\s*(.*)$", part, re.S)
        if m:
            out[m.group(1)] = m.group(2).strip()
    return out


def blocks(s, key):
    """Yield (name, body-text, offset) for every `[<key>_NAME] = { ... }` in s."""
    for m in re.finditer(r"\[(%s_\w+)\]\s*=\s*" % key, s):
        i = s.index("{", m.end())
        yield m.group(1), s[i + 1:_close(s, i) - 1], m.start()


_LIT = re.compile(r'"((?:[^"\\]|\\.)*)"')


def cstr(s):
    """Concatenate adjacent C string literals. \\n is the only escape in this repo."""
    parts = _LIT.findall(s)
    if not parts:
        return None
    t = "".join(parts)
    bad = [e for e in re.findall(r"\\(.)", t) if e != "n"]
    if bad:
        raise ValueError("unexpected C escape %r in %r" % (bad, t))
    return t


# --- family enablement -------------------------------------------------------
# Shared with Encounters.py: a disabled species must never be shown as catchable.

FAMILY_FILES = sorted(glob.glob(g("src", "data", "pokemon", "species_info", "gen_*_families.h")))


@functools.lru_cache(maxsize=1)
def family_enabled():
    """P_FAMILY_* -> bool. A literal FALSE is the world-strip marker."""
    t = read("include", "config", "species_enabled.h")
    return {m.group(1): m.group(2) != "FALSE" for m in re.finditer(r"^#define\s+(P_FAMILY_\w+)\s+(\S+)", t, re.M)}


@functools.lru_cache(maxsize=1)
def species_family():
    """SPECIES_* -> (family, teachingType) by stacking the #if guards in source order.

    Non-P_FAMILY conditionals push None; #else/#elif replaces the top of the stack with
    None because that arm is not guarded by the family above it; the innermost non-None
    entry wins. Mirrors Testing/ValidateGen13.py.
    """
    out = {}
    for path in FAMILY_FILES:
        stack, cur, teaching = [], None, "DEFAULT_LEARNING"
        with open(path, encoding="utf-8", errors="replace") as f:
            for line in f:
                m = re.match(r"\s*#if\s+(P_FAMILY_\w+)\s*$", line)
                if m:
                    stack.append(m.group(1))
                    continue
                if re.match(r"\s*#(if|ifdef|ifndef)\b", line):
                    stack.append(None)
                    continue
                if re.match(r"\s*#(else|elif)\b", line):
                    if stack:
                        stack[-1] = None
                    continue
                if re.match(r"\s*#endif", line):
                    if stack:
                        stack.pop()
                    continue
                fam = next((s for s in reversed(stack) if s), None)
                m = re.match(r"\s*\[(SPECIES_\w+)\]\s*=", line)
                if m and fam:
                    cur = m.group(1)
                    out[cur] = [fam, "DEFAULT_LEARNING"]
                    teaching = "DEFAULT_LEARNING"
                    continue
                m = re.match(r"\s*\.teachingType\s*=\s*([A-Z_]+),", line)
                if m:
                    teaching = m.group(1)
                    continue
                if cur and re.match(r"\s*\.teachableLearnset\s*=", line):
                    out[cur][1] = teaching
                    teaching = "DEFAULT_LEARNING"
    return {k: tuple(v) for k, v in out.items()}


# --- moves -------------------------------------------------------------------


@functools.lru_cache(maxsize=1)
def tm_hm_moves():
    """(tm_moves, hm_moves) in macro order. TM number is the 1-based index."""
    t = read("include", "constants", "tms_hms.h")
    cut = t.index("#define FOREACH_HM")
    pat = re.compile(r"F\((\w+)\)")
    return (
        ["MOVE_" + m for m in pat.findall(t[:cut])],
        ["MOVE_" + m for m in pat.findall(t[cut:t.index("#define FOREACH_TMHM")])],
    )


TUTOR_SCRIPTS = {
    "hoenn_johto": ["data/scripts/move_tutors.inc"],
    "kanto": ["data/scripts/move_tutors_frlg.inc"],
    "frontier": ["data/maps/BattleFrontier_Lounge7/scripts.inc"],
}
_TUTOR_MOVE = re.compile(r"setvar VAR_0x8005, (MOVE_[A-Z_0-9]*)|move_tutor (MOVE_[A-Z_0-9]*)")


@functools.lru_cache(maxsize=1)
def tutor_rosters():
    """roster -> sorted moves. Three rosters, only partly overlapping (AUDIT 9.4)."""
    out = {}
    for roster, paths in TUTOR_SCRIPTS.items():
        moves = set()
        for p in paths:
            for a, b in _TUTOR_MOVE.findall(read(*p.split("/"))):
                moves.add(a or b)
        out[roster] = sorted(moves)
    return out


@functools.lru_cache(maxsize=1)
def tutor_moves():
    """gTutorMoves[] as make_teachables.py builds it: script union + extraTutors."""
    extra = Common.load("src", "data", "pokemon", "special_movesets.json")["extraTutors"]
    return sorted(set(sum(tutor_rosters().values(), []) + extra))


@functools.lru_cache(maxsize=1)
def tm_literacy():
    m = re.search(r"^#define P_TM_LITERACY\s+GEN_(\S+)", read("include", "config", "pokemon.h"), re.M)
    return bool(m) and (m.group(1) == "LATEST" or int(m.group(1)) > 6)


_SNAKE = re.compile(r"(?!^)([A-Z]+)")


def teachables(learnset_symbol, teaching_type):
    """Rebuild one species' teachable set the way make_teachables.py does."""
    special = Common.load("src", "data", "pokemon", "special_movesets.json")
    tms, hms = tm_hm_moves()
    tmhm, tutors = tms + hms, tutor_moves()
    if teaching_type == "ALL_TEACHABLES":
        keep = [m for m in tmhm + tutors if m not in special["signatureTeachables"]]
        learnable = set(keep)
    else:
        key = _SNAKE.sub(r"_\1", learnset_symbol).upper()
        base = all_learnables().get(key)
        if base is None:
            return None
        learnable = set(base)
        if teaching_type == "TM_ILLITERATE":
            if not tm_literacy():
                learnable -= set(special["universalMoves"])
        else:
            learnable |= set(special["universalMoves"])
    return (
        [m for m in tmhm if m in learnable],
        [m for m in tutors if m in learnable],
    )


@functools.lru_cache(maxsize=1)
def all_learnables():
    return Common.load("src", "data", "pokemon", "all_learnables.json")


@functools.lru_cache(maxsize=1)
def learnsets():
    """Level-up and egg-move learnsets, with the gen selector cpp resolves for us."""
    src = read("src", "pokemon.c")
    i = src.index("#if P_LVL_UP_LEARNSETS")
    chunk = src[i:src.index("#endif", i) + len("#endif")]
    fd, p = tempfile.mkstemp(suffix=".c", prefix="learnsets")
    with os.fdopen(fd, "w") as f:
        f.write(chunk + '\n#include "data/pokemon/egg_moves.h"\n')
    t = cpp(p, extra_includes=[_famforce()])
    os.unlink(p)
    level, egg = {}, {}
    for m in re.finditer(r"s(\w+)LevelUpLearnset\[\]\s*=\s*", t):
        i = t.index("{", m.end())
        body = t[i + 1:_close(t, i) - 1]
        moves = []
        for e in items(body):
            f = fields(e.strip().lstrip("{").rstrip("}"))
            if f.get("move") and f["move"] != "LEVEL_UP_MOVE_END":
                moves.append({"level": int(f["level"]), "move": f["move"]})
        level[m.group(1)] = moves
    for m in re.finditer(r"s(\w+)EggMoveLearnset\[\]\s*=\s*", t):
        i = t.index("{", m.end())
        body = t[i + 1:_close(t, i) - 1]
        egg[m.group(1)] = [x for x in items(body) if x != "MOVE_UNAVAILABLE"]
    return level, egg


@functools.lru_cache(maxsize=1)
def dex_numbers():
    """NATIONAL_DEX_* -> ordinal. Plain sequential enum, NONE == 0."""
    t = read("include", "constants", "pokedex.h")
    body = t[t.index("enum NationalDexOrder"):]
    names = re.findall(r"^\s*(NATIONAL_DEX_\w+),", body[:body.index("\n};")], re.M)
    return {n: i for i, n in enumerate(names)}


# --- evolutions --------------------------------------------------------------


def evolutions(value):
    """Parse the cpp-flattened EVOLUTION(...) array. Returns (evolutions, breeding).

    EVO_NONE is a breeding-only link, not an evolution (AUDIT 9.5) — it is split out so
    the exclusion is visible rather than silent.  EVO_LEVEL with param 0 has no level
    gate at all; the CONDITIONS carry the trigger, so `level` stays null.
    """
    i = value.index("{")
    evos, breeding = [], []
    for entry in items(value[i + 1:_close(value, i) - 1]):
        entry = entry.strip()
        if not entry.startswith("{"):
            continue
        args = items(entry[1:_close(entry, 0) - 1])
        if not args or args[0] == "EVOLUTIONS_END":
            continue
        method, param, target = args[0], args[1], args[2]
        conds = []
        if len(args) > 3:
            c = args[3]
            j = c.index("{", c.index("EvolutionParam"))
            for one in items(c[j + 1:_close(c, j) - 1]):
                a = items(one.strip()[1:-1])
                if a and a[0] != "CONDITIONS_END":
                    conds.append({"type": a[0], "args": a[1:]})
        row = {
            "method": method,
            "param": int(param) if param.isdigit() else param,
            "level": int(param) if method == "EVO_LEVEL" and param.isdigit() and int(param) else None,
            "target_species": target,
            "conditions": conds,
        }
        (breeding if method == "EVO_NONE" else evos).append(row)
    return evos, breeding


# --- build -------------------------------------------------------------------


def build():
    fam = family_enabled()
    sf = species_family()
    level_up, egg = learnsets()
    dex = dex_numbers()
    tms, hms = tm_hm_moves()
    tm_no = {m: i + 1 for i, m in enumerate(tms)}
    hm_no = {m: i + 1 for i, m in enumerate(hms)}

    pp = Preprocessed(cpp("src/data/pokemon/species_info.h", extra_includes=[_famforce()]))
    out = []
    for name, body, off in blocks(pp.text, "SPECIES"):
        if name not in sf:
            continue  # SPECIES_NONE / SPECIES_EGG carry no family guard
        family, teaching = sf[name]
        f = fields(body)
        evos, breeding = evolutions(f["evolutions"]) if "evolutions" in f else ([], [])
        types = [resolve(t) for t in items(f["types"].strip("{}"))]
        abilities = [resolve(a) for a in items(f["abilities"].strip("{}"))]
        lset = re.search(r"s(\w+)LevelUpLearnset", f.get("levelUpLearnset", "") or "")
        eset = re.search(r"s(\w+)EggMoveLearnset", f.get("eggMoveLearnset", "") or "")
        tset = re.search(r"s(\w+)TeachableLearnset", f.get("teachableLearnset", "") or "")
        taught = teachables(tset.group(1), teaching) if tset and tset.group(1) != "None" else None
        src_file, src_line = pp.where(off)
        out.append({
            "id": name,
            "name": cstr(f.get("speciesName", "")),
            "national_dex": dex[resolve(f["natDexNum"])],
            "enabled": fam[family],
            "family": family,
            "types": {"primary": types[0], "secondary": types[1] if types[1] != types[0] else None},
            "base_stats": {
                "hp": num(f["baseHP"]), "attack": num(f["baseAttack"]),
                "defense": num(f["baseDefense"]), "sp_attack": num(f["baseSpAttack"]),
                "sp_defense": num(f["baseSpDefense"]), "speed": num(f["baseSpeed"]),
            },
            "abilities": {
                "primary": abilities[0],
                "secondary": abilities[1] if len(abilities) > 1 and abilities[1] != "ABILITY_NONE" else None,
                "hidden": abilities[2] if len(abilities) > 2 and abilities[2] != "ABILITY_NONE" else None,
            },
            "evolutions": evos,
            "breeding_links": breeding,
            "level_up_learnset": level_up.get(lset.group(1), []) if lset else [],
            "egg_moves": egg.get(eset.group(1), []) if eset else [],
            "tm_moves": [
                {"item": ("ITEM_HM%02d" % hm_no[m]) if m in hm_no else ("ITEM_TM%02d" % tm_no[m]),
                 "kind": "HM" if m in hm_no else "TM",
                 "number": hm_no[m] if m in hm_no else tm_no[m],
                 "move": m}
                for m in (taught[0] if taught else [])
            ],
            "tutor_moves": taught[1] if taught else [],
            "teaching_type": teaching,
            "obtainable_via": None,
            "gate": None,
            "severity": None,
            "gaps": [
                gap("obtainable_via", "needs the encounter/trainer/script cross-reference to "
                                      "separate evolution-only from unreachable", "9.6"),
                gap("gate", "progression.json does not exist yet", None),
            ],
            "source": source(src_file, key=name, line=src_line),
        })
    out.sort(key=lambda r: r["id"])
    return {
        **Common.header(),
        "species": out,
        "tm_moves": [{"number": i + 1, "item": "ITEM_TM%02d" % (i + 1), "move": m} for i, m in enumerate(tms)],
        "hm_moves": [{"number": i + 1, "item": "ITEM_HM%02d" % (i + 1), "move": m} for i, m in enumerate(hms)],
        "tutor_rosters": tutor_rosters(),
    }


# --- verify ------------------------------------------------------------------


def verify(payload):
    fam = family_enabled()
    dis = sorted(k for k, v in fam.items() if not v)
    checks = []

    def ck(label, got, want):
        checks.append((label, got, want, got == want))

    ck("families total", len(fam), 539)
    ck("families disabled", len(dis), 339)
    ck("families enabled", len(fam) - len(dis), 200)
    ck("species records", len(payload["species"]), 1571)
    ck("TM moves", len(payload["tm_moves"]), 50)
    ck("HM moves", len(payload["hm_moves"]), 8)

    v = subprocess.run([sys.executable, "Testing/ValidateGen13.py"], cwd=Common.GAME,
                       capture_output=True, text=True)
    m = re.search(r"families disabled: (\d+) \| species mapped: (\d+)", v.stdout)
    ck("ValidateGen13 exit", v.returncode, 0)
    ck("ValidateGen13 disabled", int(m.group(1)) if m else None, len(dis))
    ck("ValidateGen13 species mapped", int(m.group(2)) if m else None, len(payload["species"]))

    leaked = [s["id"] for s in payload["species"] if any(e["method"] == "EVO_NONE" for e in s["evolutions"])]
    ck("EVO_NONE rows in evolutions", len(leaked), 0)

    ungated = [
        (s["id"], e["target_species"]) for s in payload["species"] for e in s["evolutions"]
        if e["method"] == "EVO_LEVEL" and e["param"] == 0 and not e["conditions"]
    ]
    ck("EVO_LEVEL param 0 without conditions", len(ungated), 0)

    ck("levelled EVO_LEVEL rows carry a level", 0, len([
        1 for s in payload["species"] for e in s["evolutions"]
        if e["method"] == "EVO_LEVEL" and e["param"] and e["level"] != e["param"]
    ]))

    tmset = {t["move"] for t in payload["tm_moves"]} | {t["move"] for t in payload["hm_moves"]}
    ck("TM n tutor disjoint", len(tmset & set(tutor_moves())), 0)

    enabled = sum(1 for s in payload["species"] if s["enabled"])
    print("species: %d enabled / %d total; %d breeding-only EVO_NONE links held back" % (
        enabled, len(payload["species"]),
        sum(len(s["breeding_links"]) for s in payload["species"])))
    for label, got, want, ok in checks:
        print("%-42s %-8s %s %s" % (label, got, "==" if ok else "!=", want))
    bad = [c for c in checks if not c[3]]
    if bad:
        raise SystemExit("FAIL: %d assertion(s)" % len(bad))


if __name__ == "__main__":
    payload = build()
    verify(payload)
    print(Common.write("species.json", payload))
