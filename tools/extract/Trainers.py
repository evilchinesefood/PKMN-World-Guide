#!/usr/bin/env python3
"""trainers.json — see docs/SCHEMAS.md and docs/DATA-AUDIT.md 0.5, 5, 5.1-5.4.

Both .party files go into ONE table keyed by (trainer_id, difficulty). The source file
never decides region; the map the trainer occupies does.
"""

import os, re, sys, glob, functools

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import Common as C

PARTY_FILES = ["src/data/trainers.party", "src/data/trainers_frlg.party"]

# Expectations. `audit` is what DATA-AUDIT.md recorded; `pin` is measured at the pinned
# commit. They diverge where the submodule moved after the audit was written — a DRIFT
# line is printed for every one of those so a stale figure can never pass silently.
EXPECT = {
    #  name                 audit  pin
    # The 22 hijacked slots were fixed upstream in 0f5b2595 (game issue #36), so the pin
    # measures 0 while the audit still records 22. The detection below is KEPT: it is the
    # tripwire that would catch the same paste happening again.
    "anomalies": (22, 0),
    "hard": (30, 42),
    "frlg_hoenn_johto_placements": (0, 2),
    "disabled_species_refs": (0, 0),
    "evs_non_null": (0, 0),
}


def die(msg):
    print("FAIL " + msg)
    sys.exit(1)


# --- constants ---------------------------------------------------------------
# ALL_REGIONS=1 is always-on (Makefile:12) and GAME_VERSION=EMERALD, so IS_FRLG=0.
# opponents_frlg.h carries the whole Kanto block twice, once rebased by
# KANTO_TRAINER_ID_OFFSET under `#if ALL_REGIONS` and once native under `#else`.
# Taking the wrong arm shifts every Kanto id by 1096.

FLAGS = {"ALL_REGIONS": True, "IS_FRLG": False}

_DEF = re.compile(r"^\s*#\s*define\s+(\w+)\s+(.+?)\s*(?://.*)?$")
_COND = re.compile(r"^\s*#\s*(if|ifdef|ifndef|elif|else|endif)\b\s*(.*?)\s*$")


def _defines(path):
    """Yields (name, value) for defines in live preprocessor arms only."""
    stack = []
    for line in C.read(*path.split("/")).splitlines():
        m = _COND.match(line)
        if m:
            op, arg = m.group(1), m.group(2)
            if op in ("if", "ifdef", "ifndef"):
                stack.append(FLAGS.get(arg.strip(), True) if op == "if" else True)
            elif op == "elif":
                if stack:
                    stack[-1] = not stack[-1]
            elif op == "else":
                if stack:
                    stack[-1] = not stack[-1]
            elif op == "endif":
                if stack:
                    stack.pop()
            continue
        if all(stack):
            m = _DEF.match(line)
            if m:
                yield m.group(1), m.group(2)


@functools.lru_cache(maxsize=1)
def trainer_ids():
    """TRAINER_* -> int, aliases resolved. Non-numeric non-alias defines are dropped."""
    ids, alias = {}, {}
    for p in ("include/constants/opponents_frlg.h", "include/constants/opponents.h",
              "include/constants/johto_compat_ids.h"):
        for k, v in _defines(p):
            if not k.startswith("TRAINER_"):
                continue
            v = v.strip()
            if v.isdigit():
                ids[k] = int(v)
            elif v.startswith("TRAINER_"):
                alias[k] = v
    for k, v in alias.items():
        if v in ids:
            ids.setdefault(k, ids[v])
    return ids


# --- species -----------------------------------------------------------------
# Mirrors Testing/ValidateGen13.py: family enablement lives in species_enabled.h and the
# species -> family edge is the innermost `#if P_FAMILY_*` in gen_*_families.h. An #else
# arm is NOT guarded by the family above it.


@functools.lru_cache(maxsize=1)
def species_tables():
    disabled = set(re.findall(r"#define\s+(P_FAMILY_\w+)\s+FALSE\b",
                              C.read("include", "config", "species_enabled.h")))
    fam, name_const = {}, {}
    for path in sorted(glob.glob(C.g("src", "data", "pokemon", "species_info", "gen_*_families.h"))):
        stack, cur = [], None
        with open(path, encoding="utf-8", errors="replace") as f:
            for line in f:
                m = re.match(r"\s*#if\s+(P_FAMILY_\w+)", line)
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
                f_ = next((s for s in reversed(stack) if s), None)
                m = re.match(r"\s*\[(SPECIES_\w+)\]\s*=", line)
                if m and f_:
                    cur = m.group(1)
                    fam[cur] = f_
                    continue
                m = re.search(r'\.speciesName\s*=\s*_\(\s*"([^"]+)"', line)
                if m and f_ and cur:
                    name_const.setdefault(m.group(1).lower(), cur)
    if len(disabled) < 200 or len(fam) < 800:
        die(f"species tables look wrong: {len(disabled)} disabled, {len(fam)} mapped")
    return disabled, fam, name_const


def species_enabled(const):
    disabled, fam, _ = species_tables()
    f = fam.get(const)
    return None if f is None else f not in disabled


@functools.lru_cache(maxsize=1)
def ability_names():
    """ABILITY_* -> display name, so const-authored abilities read like the rest."""
    src = C.read("src", "data", "abilities.h")
    out, cur = {}, None
    for line in src.splitlines():
        m = re.match(r"\s*\[(ABILITY_\w+)\]\s*=", line)
        if m:
            cur = m.group(1)
            continue
        m = re.search(r'\.name\s*=\s*_\("([^"]*)"\)', line)
        if m and cur:
            out.setdefault(cur, m.group(1))
            cur = None
    return out


# --- constant-name normalisation ---------------------------------------------
# Reproduces trainerproc's fprint_constant / fprint_species exactly (main.c:1666, 1739),
# so a human-authored value and its raw-constant twin collapse to one token. Lossless:
# it is the same transform the compiler applies.


def to_const(prefix, s):
    if not s:
        return None
    if s.startswith(prefix + "_"):
        return s
    out = []
    for ch in s:
        if ch.isascii() and (ch.isupper() or ch.isdigit()):
            out.append(ch)
        elif ch.isascii() and ch.islower():
            out.append(ch.upper())
        elif ch == "'":
            pass
        else:
            out.append("_")
    return prefix + "_" + "".join(out)


def to_species(s):
    """Display name -> constant. The game's own name table wins where it has an entry:
    "Castform" is SPECIES_CASTFORM_NORMAL, and the bare SPECIES_CASTFORM alias the string
    transform produces has no family edge, which would silently skip the enablement test."""
    if not s:
        return None
    if s.startswith("SPECIES_"):
        return s
    named = species_tables()[2].get(s.lower())
    if named:
        return named
    out, sep = [], False
    for ch in s:
        if ch.isascii() and (ch.isalnum()):
            if sep and out:
                out.append("_")
            sep = False
            out.append(ch.upper())
        elif ch in "'’%":
            pass
        elif ch == "♂":
            sep = False
            out.append("_M")
        elif ch == "♀":
            sep = False
            out.append("_F")
        elif ch == "é":
            if sep and out:
                out.append("_")
            sep = False
            out.append("E")
        else:
            sep = True
    return "SPECIES_" + "".join(out)


# --- .party parsing ----------------------------------------------------------

_MON_KEYS = {"Level", "IVs", "EVs", "Ability", "Nature", "Ball", "Happiness", "Shiny",
             "Dynamax Level", "Gigantamax", "Tera Type", "Tags"}
_STATS = {"HP": "hp", "Atk": "atk", "Def": "def", "SpA": "spa", "SpD": "spd", "Spe": "spe"}


def _strip_comments(text):
    """Blanks /* */ comments but keeps every newline, so line numbers stay true."""
    return re.sub(r"/\*.*?\*/", lambda m: "\n" * m.group(0).count("\n"), text, flags=re.S)


def _parse_stats(v):
    out = {}
    for part in v.split("/"):
        part = part.strip()
        if not part:
            continue
        n, _, stat = part.partition(" ")
        key = _STATS.get(stat.strip())
        if key is None:
            return None
        out[key] = int(n)
    return out if len(out) == 6 else None


_HDR = re.compile(r"^(?P<a>[^@()]+?)(?:\s*\((?P<b>[^)]+)\))?(?:\s*\((?P<c>[MF])\))?(?:\s*@\s*(?P<item>.+?))?\s*$")


def _parse_mon_header(line):
    """Showdown header. main.c:698 — a single-letter parenthetical is a gender, not a species."""
    m = _HDR.match(line.strip())
    if not m:
        return None
    a, b, c, item = m.group("a").strip(), m.group("b"), m.group("c"), m.group("item")
    nick = None
    if b is None:
        species = a
    elif c is not None:
        nick, species = a, b.strip()
    elif len(b.strip()) == 1:
        species, c = a, b.strip()
    else:
        nick, species = a, b.strip()
    return nick, species, ("Male" if c == "M" else "Female" if c == "F" else None), item


def parse_party(rel):
    """One dict per `=== TRAINER_X ===` block, fields kept raw."""
    text = _strip_comments(C.read(*rel.split("/")))
    lines = text.splitlines()
    starts = [(i, m.group(1)) for i, l in enumerate(lines)
              for m in [re.match(r"^===\s*(\w+)\s*===\s*$", l)] if m]
    out = []
    for n, (ln, const) in enumerate(starts):
        end = starts[n + 1][0] if n + 1 < len(starts) else len(lines)
        body = lines[ln + 1:end]
        t = {"const": const, "file": rel, "line": ln + 1, "attrs": {}, "party": []}
        mon = None
        in_party = False
        for off, raw in enumerate(body):
            s = raw.strip()
            if not s:
                in_party = True
                mon = None
                continue
            if s.startswith("- "):
                if mon is not None:
                    mon["moves"].append(s[2:].strip())
                continue
            k, sep, v = s.partition(":")
            k, v = k.strip(), v.strip()
            if sep and not in_party and k not in _MON_KEYS:
                t["attrs"][k] = v
                continue
            if sep and mon is not None and k in _MON_KEYS:
                mon["attrs"][k] = v
                continue
            h = _parse_mon_header(s)
            if h is None:
                die(f"{rel}:{ln + off + 2} unparsed line {s!r}")
            mon = {"nickname": h[0], "species": h[1], "gender": h[2], "item": h[3],
                   "attrs": {}, "moves": [], "line": ln + off + 2}
            t["party"].append(mon)
            in_party = True
        out.append(t)
    return out


# --- scripts and placement ---------------------------------------------------

_TB = re.compile(r"^\s*trainerbattle\w*\s")
_TOK = re.compile(r"\bTRAINER_\w+\b")
_LABEL = re.compile(r"^(\w+)::?\s*$")


def _script_path(m):
    d = m.get("shared_scripts_map") or m["_dir"]
    p = os.path.join("data", "maps", d, "scripts.inc")
    return p if os.path.isfile(C.g(p)) else None


@functools.lru_cache(maxsize=None)
def _labels(rel):
    """label -> body lines, for one .inc."""
    out, cur = {}, None
    for line in C.read(*rel.split("/")).splitlines():
        m = _LABEL.match(line)
        if m:
            cur = m.group(1)
            out[cur] = []
            continue
        if cur:
            out[cur].append(line)
    return out


@functools.lru_cache(maxsize=1)
def _all_labels():
    """One label index across every script file. Kanto's route trainers live in the shared
    data/scripts/trainers_frlg.inc while the object_events that call them live in the
    Route*_Frlg map.json, so a per-map index loses 141 of them."""
    out = {}
    for path in sorted(glob.glob(os.path.join(C.g("data"), "**", "*.inc"), recursive=True)):
        rel = os.path.relpath(path, C.GAME).replace(os.sep, "/")
        for k, v in _labels(rel).items():
            out.setdefault(k, v)
    return out


def _trainers_in(body, ids):
    """All resolvable trainer constants on trainerbattle lines. The raw `trainerbattle`
    macro puts a TRAINER_BATTLE_* type first and two_trainers carries two trainers, so
    take every token and let the constant table filter."""
    got = []
    for line in body:
        if not _TB.match(line):
            continue
        for tok in _TOK.findall(line):
            if tok in ids and ids[tok] != 0:
                got.append(ids[tok])
    return got


def _reach(labels, start, seen):
    """Labels reachable from `start`, following any label mention. Crosses files."""
    stack = [start]
    while stack:
        cur = stack.pop()
        if cur in seen or cur not in labels:
            continue
        seen.add(cur)
        for line in labels[cur]:
            for tok in re.findall(r"\b\w+\b", line):
                if tok in labels and tok not in seen:
                    stack.append(tok)
    return seen


def map_placements():
    """trainer_id -> sorted list of (map_id, coord|None). One trainer can sit on many maps
    (Johto reuses Hoenn ids via johto_compat_ids.h)."""
    ids = trainer_ids()
    out = {}

    def add(tid, map_id, coord):
        out.setdefault(tid, {}).setdefault(map_id, coord if coord else None)
        if coord and out[tid][map_id] is None:
            out[tid][map_id] = coord

    every = _all_labels()
    for map_id, m in sorted(C.maps().items()):
        rel = _script_path(m)
        own = _labels(rel) if rel else {}
        claimed = set()
        events = []
        for ev in m.get("object_events") or []:
            if ev.get("script"):
                events.append((ev["script"], {"x": ev["x"], "y": ev["y"],
                                              "elevation": ev.get("elevation")}))
        for key in ("bg_events", "coord_events"):
            for ev in m.get(key) or []:
                if ev.get("script"):
                    events.append((ev["script"], {"x": ev["x"], "y": ev["y"],
                                                  "elevation": ev.get("elevation")}))
        for label, coord in events:
            seen = _reach(every, label, set())
            claimed |= seen
            for lb in sorted(seen):
                for tid in _trainers_in(every[lb], ids):
                    add(tid, map_id, coord)
        for lb in sorted(own):
            if lb in claimed:
                continue
            for tid in _trainers_in(own[lb], ids):
                add(tid, map_id, None)
    return {k: sorted(v.items()) for k, v in out.items()}


@functools.lru_cache(maxsize=1)
def rematch_placements():
    """trainer_id -> MAP_*, from gRematchTable. Each row carries its own map."""
    ids = trainer_ids()
    out = {}
    src = C.read("src", "data", "rematch_table.h") if os.path.isfile(
        C.g("src", "data", "rematch_table.h")) else C.read("src", "battle_setup.c")
    for m in re.finditer(r"REMATCH\(([^)]*)\)", src):
        args = [a.strip() for a in m.group(1).split(",")]
        if len(args) < 2 or not args[-1].startswith("MAP_"):
            continue
        for a in args[:-1]:
            if a in ids and ids[a] != 0:
                out.setdefault(ids[a], args[-1])
    return out


@functools.lru_cache(maxsize=1)
def c_placements():
    """Trainer constants referenced from C — Frontier Brains and the like. No map."""
    ids = trainer_ids()
    got = set()
    for root, _, files in os.walk(C.g("src")):
        for fn in files:
            if not fn.endswith(".c"):
                continue
            with open(os.path.join(root, fn), encoding="utf-8", errors="replace") as f:
                for tok in _TOK.findall(f.read()):
                    if tok in ids and ids[tok] != 0:
                        got.add(ids[tok])
    return got


# --- battle frontier ---------------------------------------------------------
# A different universe: FRONTIER_TRAINER_* indexes gBattleFrontierTrainers, which names a
# monSet pool instead of a party. Emitted under its own key with party: null.


def frontier():
    consts = {k: int(v) for k, v in _defines("include/constants/battle_frontier_trainers.h")
              if k.startswith("FRONTIER_TRAINER_") and v.strip().isdigit()}
    src = C.read("src", "data", "battle_frontier", "battle_frontier_trainers.h")
    out = []
    for m in re.finditer(r"\[(FRONTIER_TRAINER_\w+)\]\s*=\s*\{(.*?)\n    \}", src, re.S):
        key, body = m.group(1), m.group(2)
        name = re.search(r'\.trainerName\s*=\s*_\("([^"]*)"\)', body)
        cls = re.search(r"\.facilityClass\s*=\s*(\w+)", body)
        pool = re.search(r"\.monSet\s*=\s*\(const u16\[\]\)\s*\{([^}]*)\}", body, re.S)
        out.append({
            "trainer_id": consts.get(key),
            "constant": key,
            "name": name.group(1) if name else None,
            "facility_class": cls.group(1) if cls else None,
            "mon_sets": sorted(re.findall(r"FRONTIER_MONS_\w+", pool.group(1))) if pool else [],
            "party": None,
            "gate": None,
            "severity": None,
            "source": C.source("src/data/battle_frontier/battle_frontier_trainers.h", key, None),
        })
    return sorted(out, key=lambda r: (r["trainer_id"] is None, r["trainer_id"], r["constant"]))


# --- assembly ----------------------------------------------------------------


def _human_index(entries):
    """const -> human display string, learned from the entries authored in human form.
    Lets the ~250 raw-vocabulary Johto entries render like every other one."""
    idx = {}
    for e in entries:
        for field, prefix in (("Class", "TRAINER_CLASS"), ("Music", "TRAINER_ENCOUNTER_MUSIC")):
            v = e["attrs"].get(field)
            if v and not v.startswith(prefix + "_"):
                idx.setdefault(to_const(prefix, v), v)
        for v in re.split(r"\s*/\s*", e["attrs"].get("AI", "")):
            v = v.strip()
            if v and not v.startswith("AI_FLAG_"):
                idx.setdefault(to_const("AI_FLAG", v), v)
    return idx


def _display(idx, prefix, v, unresolved):
    if v is None:
        return None, None
    const = to_const(prefix, v)
    if not v.startswith(prefix + "_"):
        return v, const
    human = idx.get(const)
    if human is None:
        unresolved.add(const)
        return const, const
    return human, const


def build():
    ids = trainer_ids()
    entries = []
    for rel in PARTY_FILES:
        entries += parse_party(rel)
    entries = [e for e in entries if e["const"] != "TRAINER_NONE"]

    unknown = sorted({e["const"] for e in entries if e["const"] not in ids})
    if unknown:
        die(f"{len(unknown)} party blocks have no id constant: {unknown[:5]}")

    # 0.5 — a Kanto boss party parked on an ordinary Hoenn/Johto route id. Identity is the
    # (Name, Class, Pic) triple, so a triple that also exists in the Kanto file under an
    # Frlg class marks the slot as hijacked. The constant name proves nothing.
    def triple(e):
        a = e["attrs"]
        return (a.get("Name"), to_const("TRAINER_CLASS", a.get("Class")), a.get("Pic"))

    frlg_triples = {triple(e) for e in entries if e["file"].endswith("trainers_frlg.party")}
    anomalous = set()
    for e in entries:
        if e["file"].endswith("trainers_frlg.party"):
            continue
        t = triple(e)
        if t in frlg_triples and t[1] and "FRLG" in t[1]:
            anomalous.add(id(e))

    idx = _human_index(entries)
    unresolved = set()
    placed = map_placements()
    rematch = rematch_placements()
    ccode = c_placements()
    maps = C.maps()
    disabled_refs, unmapped = [], []

    recs = []
    for e in entries:
        a = e["attrs"]
        tid = ids[e["const"]]
        diff = (a.get("Difficulty") or "Normal").lower()

        cls, _ = _display(idx, "TRAINER_CLASS", a.get("Class"), unresolved)
        music, _ = _display(idx, "TRAINER_ENCOUNTER_MUSIC", a.get("Music"), unresolved)
        ai = []
        for v in re.split(r"\s*/\s*", a.get("AI", "")):
            if v.strip():
                ai.append(_display(idx, "AI_FLAG", v.strip(), unresolved)[0])

        party = []
        for mon in e["party"]:
            ma = mon["attrs"]
            sp = to_species(mon["species"])
            en = species_enabled(sp)
            if en is False:
                disabled_refs.append((e["const"], sp))
            elif en is None:
                unmapped.append((e["const"], sp))
            ab = ma.get("Ability")
            ivs = _parse_stats(ma["IVs"]) if "IVs" in ma else None
            party.append({
                "species": sp,
                "nickname": mon["nickname"],
                "gender": mon["gender"],
                "level": int(ma["Level"]) if "Level" in ma else 100,
                "level_is_default": "Level" not in ma,
                "ivs": ivs if ivs else {k: 31 for k in _STATS.values()},
                "ivs_are_default": "IVs" not in ma,
                # Absent is not zero. EVs/Nature/Ball/Happiness/Shiny are authored zero
                # times in both files; a 0 here would be the engine's choice, not anyone's.
                "evs": _parse_stats(ma["EVs"]) if "EVs" in ma else None,
                "nature": ma.get("Nature"),
                "ability": ability_names().get(ab, ab) if ab else None,
                "held_item": to_const("ITEM", mon["item"]) if mon["item"] else None,
                "moves": [to_const("MOVE", m) for m in mon["moves"]],
                "moves_are_default": not mon["moves"],
            })

        cands = placed.get(tid, [])
        if cands:
            best = sorted(cands, key=lambda c: (c[1] is None, c[0]))[0]
            place = {"map": best[0], "coord": best[1], "via": "map_script"}
        elif tid in rematch:
            place = {"map": rematch[tid], "coord": None, "via": "rematch_table"}
        elif tid in ccode:
            place = {"map": None, "coord": None, "via": "c_code"}
        else:
            place = {"map": None, "coord": None, "via": "unreferenced"}
        m = maps.get(place["map"]) if place["map"] else None
        place["region"] = C.region_of_map(m) if m else None
        place["also_on"] = [c[0] for c in cands if c[0] != place["map"]]

        recs.append({
            "trainer_id": tid,
            "constant": e["const"],
            "difficulty": diff,
            "name": a.get("Name") or None,
            "class": cls,
            "pic": a.get("Pic"),
            "gender": a.get("Gender"),
            "music": music,
            "double_battle": (a.get("Double Battle") or a.get("Battle Type") or "No")
            in ("Yes", "Doubles"),
            "items": [to_const("ITEM", i.strip()) for i in a.get("Items", "").split("/") if i.strip()],
            "ai_flags": ai,
            "mugshot": a.get("Mugshot"),
            "placement": place,
            "party": party,
            "flags": {"defeat_flag": None},
            "anomaly": "frlg_boss_in_hoenn_slot" if id(e) in anomalous else None,
            "gate": None,
            "severity": None,
            "source": C.source(e["file"], e["const"], e["line"]),
        })

    recs.sort(key=lambda r: (r["trainer_id"], r["difficulty"]))
    return recs, entries, unresolved, disabled_refs, unmapped


# --- verification ------------------------------------------------------------


def check(results, name, actual):
    audit, pin = EXPECT[name]
    ok = actual == pin
    results.append((name, actual, pin, ok))
    if audit != pin:
        print(f"DRIFT {name}: audit says {audit}, pin measures {pin}")
    return ok


def verify(recs, entries, unresolved, disabled_refs, unmapped):
    results = []
    ok = True

    seen = {}
    for r in recs:
        k = (r["trainer_id"], r["difficulty"])
        if k in seen:
            print(f"FAIL duplicate key {k}: {seen[k]} and {r['constant']}")
            ok = False
        seen[k] = r["constant"]
    results.append(("unique (id, difficulty)", len(seen), len(recs), len(seen) == len(recs)))

    byname = {}
    for r in recs:
        byname.setdefault(r["constant"], set()).add(r["trainer_id"])
    bad = {k: v for k, v in byname.items() if len(v) > 1}
    byid = {}
    for k, v in byname.items():
        byid.setdefault(tuple(v)[0], set()).add(k)
    collide = {k: v for k, v in byid.items() if len(v) > 1}
    results.append(("name<->id 1:1", len(bad) + len(collide), 0, not bad and not collide))
    if collide:
        print(f"FAIL ids with 2+ constants: {list(collide.items())[:3]}")
    ok = ok and not bad and not collide

    an = [r for r in recs if r["anomaly"] == "frlg_boss_in_hoenn_slot"]
    ok &= check(results, "anomalies", len(an))
    # The canonical hijacked slot, restored upstream. This asserts the identity rather than
    # the absence of the flag: "anomalies == 0" only says no slot still looks hijacked, this
    # says the one slot everyone checked by hand is the trainer it should always have been.
    lyle = [r for r in recs if r["constant"] == "TRAINER_LYLE"]
    lyle_ok = len(lyle) == 1 and lyle[0]["name"] == "LYLE" and lyle[0]["class"] == "Bug Catcher"
    results.append(("TRAINER_LYLE is Bug Catcher LYLE", lyle_ok, True, lyle_ok))
    ok = ok and lyle_ok

    ok &= check(results, "hard", sum(1 for r in recs if r["difficulty"] == "hard"))

    # "trainers_frlg.party is exactly Kanto" held when the audit was written. It no longer
    # does: the four Rocket Jessie/James ids are fought in all three regions. So the test
    # that still carries the audit's intent is the exclusive one — a Kanto-file trainer
    # must reach Kanto somewhere. The non-exclusive count is kept as a tripwire.
    frlg = {e["const"] for e in entries if e["file"].endswith("trainers_frlg.party")}
    regions = {}
    for r in recs:
        p = r["placement"]
        regions[r["constant"]] = {C.region_of_map(C.maps()[m])
                                  for m in ([p["map"]] if p["map"] else []) + p["also_on"]}
    leak = [r for r in recs if r["constant"] in frlg
            and r["placement"]["region"] in ("hoenn", "johto")]
    ok &= check(results, "frlg_hoenn_johto_placements", len(leak))
    if leak:
        print("NOTE cross-region: " + ", ".join(
            f"{r['constant']}@{sorted(regions[r['constant']])}" for r in leak))
    orphan = [r for r in recs if r["constant"] in frlg and regions[r["constant"]]
              and "kanto" not in regions[r["constant"]]]
    results.append(("frlg trainer with no kanto map", len(orphan), 0, not orphan))
    ok = ok and not orphan

    ok &= check(results, "disabled_species_refs", len(disabled_refs))
    if disabled_refs:
        print(f"FAIL disabled species referenced: {disabled_refs[:5]}")
    # Guards the check above against passing vacuously: an unresolvable species is not
    # evidence of an enabled one.
    results.append(("every party species has a family", len(unmapped), 0, not unmapped))
    ok = ok and not unmapped
    if unmapped:
        print(f"FAIL species with no P_FAMILY edge: {sorted(set(unmapped))[:5]}")

    mons = [m for r in recs for m in r["party"]]
    nulls = sum(1 for m in mons if m["level"] is None or m["ivs"] is None)
    results.append(("every mon has level+ivs", nulls, 0, nulls == 0))
    ok = ok and nulls == 0
    ok &= check(results, "evs_non_null", sum(1 for m in mons if m["evs"] is not None))

    w = max(len(r[0]) for r in results)
    for name, actual, want, good in results:
        print(f"{'PASS' if good else 'FAIL'} {name:<{w}}  {actual} (expected {want})")
    if unresolved:
        print(f"NOTE {len(unresolved)} raw constants have no human form anywhere; kept raw: "
              + ", ".join(sorted(unresolved)[:6]))
    return ok, mons


def main():
    recs, entries, unresolved, disabled_refs, unmapped = build()
    fr = frontier()
    ok, mons = verify(recs, entries, unresolved, disabled_refs, unmapped)

    def tally(key):
        out = {}
        for r in recs:
            k = r["placement"][key]
            out[k] = out.get(k, 0) + 1
        return " ".join(f"{k}={v}" for k, v in sorted(out.items(), key=lambda x: str(x[0])))

    print(f"\ntrainers {len(recs)} | mons {len(mons)} | frontier {len(fr)}")
    print("placement " + tally("via"))
    print("region    " + tally("region"))

    p = C.write("trainers.json", dict(C.header(), trainers=recs, frontier_trainers=fr))
    print("wrote " + p)
    if not ok:
        sys.exit(1)


if __name__ == "__main__":
    main()
