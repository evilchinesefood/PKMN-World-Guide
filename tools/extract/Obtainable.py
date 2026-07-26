"""Fills species.json's `obtainable_via`. Runs after Encounters, Species and Maps.

This is the field the "where do I get X" index is built from, and the one the completeness
ledger checks ("every obtainable species has at least one documented acquisition method").

Five sources, and the distinction that matters is between a species being ENABLED and being
REACHABLE. A species can compile fine and still have nothing anywhere that produces it --
that is not a gap in this extractor, it is a fact about the game, so those are reported as
`unreachable` rather than silently left null. See DATA-AUDIT 9.6.

Wild encounters use LIVE tables only. The *_LeafGreen duplicates are compiled out of the
shipped build, so a species that appears only there is not obtainable.
"""

import os, re, sys, json, glob, collections

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import Common as C

GIVEMON = re.compile(r"^\s*(?:givemon|givenamedmon)\s+(SPECIES_\w+)", re.M)
GIVEEGG = re.compile(r"^\s*giveegg\s+(SPECIES_\w+)", re.M)
STATIC = re.compile(r"^\s*setwildbattle\s+(SPECIES_\w+)", re.M)
# Scripted one-off legendaries (Lugia, Ho-Oh) use seteventmon, not setwildbattle.
EVENTMON = re.compile(r"^\s*seteventmon\s+(SPECIES_\w+)", re.M)
# Entei/Raikou/Suicune and Latias/Latios roam the map instead of sitting in a table.
ROAMER = re.compile(r"TryAddRoamer\(\s*(SPECIES_\w+)")
STARTER_GIVE = re.compile(r"^\s*givemon\s+PLAYER_STARTER_SPECIES", re.M)

# The debug menu can hand over any species in the game. Treating it as an acquisition source
# would mark almost everything obtainable and tell a player Bulbasaur is "a gift".
SKIP_SCRIPTS = ("data/scripts/debug.inc",)


def map_of_script_file(path):
    """data/maps/<Dir>/scripts.inc -> the MAP_* id that directory belongs to."""
    parts = path.split(os.sep)
    if "maps" not in parts:
        return None
    d = parts[parts.index("maps") + 1]
    for mid, m in C.maps().items():
        if m.get("_dir") == d:
            return mid
    return None


def starters():
    """The nine starters, from sStarterMon in src/starter_choose.c.

    They are given by `givemon PLAYER_STARTER_SPECIES` -- a macro, not a literal SPECIES_*,
    so a plain givemon scan misses every one of them. The table is region-aware, and Kanto's
    order is deliberately Charmander/Bulbasaur/Squirtle rather than the natural grass-first
    order so Blue's VAR_STARTER_MON variant-select stays correct.
    """
    txt = C.read("src", "starter_choose.c")
    body = txt[txt.index("sStarterMon[REGIONS_COUNT]") :]
    body = body[: body.index("};")]
    out = {}
    for m in re.finditer(r"\[REGION_(\w+)\]\s*=\s*\{([^}]*)\}", body):
        region = m.group(1).lower()
        for i, sp in enumerate(re.findall(r"SPECIES_\w+", m.group(2))):
            out.setdefault(sp, []).append({"region": region, "index": i})
    return out


def starter_maps():
    """region -> the map where `givemon PLAYER_STARTER_SPECIES` runs."""
    out = {}
    for p in glob.glob(C.g("data", "maps", "*", "scripts.inc")):
        with open(p, encoding="utf-8", errors="replace") as f:
            if not STARTER_GIVE.search(f.read()):
                continue
        mid = map_of_script_file(p)
        if mid:
            out[C.region_of_map(C.maps()[mid])] = mid
    return out


def from_scripts():
    """Gift, egg and static-battle sources, with the map they happen on where known."""
    out = collections.defaultdict(list)
    for p in glob.glob(C.g("data", "**", "*.inc"), recursive=True):
        rel = os.path.relpath(p, C.GAME)
        if rel.replace(os.sep, "/") in SKIP_SCRIPTS:
            continue
        with open(p, encoding="utf-8", errors="replace") as f:
            txt = f.read()
        mid = map_of_script_file(p)
        for pat, kind in ((GIVEMON, "gift"), (GIVEEGG, "egg"), (STATIC, "static"), (EVENTMON, "static")):
            for m in pat.finditer(txt):
                line = txt[: m.start()].count("\n") + 1
                out[m.group(1)].append(
                    {"kind": kind, "map": mid, "source": C.source(rel, line=line)}
                )
    return out


def from_trades():
    """src/data/trade.h -- what the NPC gives you, and what it wants."""
    txt = C.read("src", "data", "trade.h")
    out = collections.defaultdict(list)
    for blk in re.finditer(r"\[(INGAME_TRADE_\w+)\]\s*=\s*\{(.*?)\n    \}", txt, re.S):
        name, body = blk.group(1), blk.group(2)
        got = re.search(r"\.species\s*=\s*(SPECIES_\w+)", body)
        want = re.search(r"\.requestedSpecies\s*=\s*(SPECIES_\w+)", body)
        if got:
            out[got.group(1)].append(
                {
                    "kind": "trade",
                    "trade": name,
                    "wants": want.group(1) if want else None,
                    "source": C.source("src/data/trade.h", key=name),
                }
            )
    return out


def from_encounters():
    d = json.load(open(os.path.join(C.OUT, "encounters.json")))["encounters"]
    out = collections.defaultdict(list)
    for e in d:
        if e.get("live") is False:
            continue
        for method, meth in (e.get("methods") or {}).items():
            groups = meth["rods"].items() if meth.get("rods") else [(None, meth)]
            for rod, tbl in groups:
                agg = {}
                for s in tbl["slots"]:
                    k = s["species"]
                    a = agg.setdefault(k, {"percent": 0, "lo": 99, "hi": 0})
                    a["percent"] += s["percent"]
                    a["lo"] = min(a["lo"], s["min_level"])
                    a["hi"] = max(a["hi"], s["max_level"])
                for sp, a in agg.items():
                    out[sp].append(
                        {
                            "kind": "wild",
                            "map": e["map"],
                            "region": e.get("region"),
                            "method": method,
                            "rod": rod,
                            "percent": a["percent"],
                            "min_level": a["lo"],
                            "max_level": a["hi"],
                        }
                    )
    return out


def from_roamers():
    """Roaming legendaries have no encounter table row; they are spawned by src/roamer.c."""
    txt = C.read("src", "roamer.c")
    out = collections.defaultdict(list)
    seen = set(ROAMER.findall(txt))
    # The trio is named in IsRoamerAllowed rather than a TryAddRoamer call.
    for m in re.finditer(r"species ==\s*(SPECIES_\w+)", txt):
        seen.add(m.group(1))
    for sp in sorted(seen):
        out[sp].append({"kind": "roamer", "source": C.source("src/roamer.c")})
    return out


def from_form_change():
    """Alternate forms reachable from a base form.

    Castform Rainy, Deoxys Attack, every Mega -- these are not caught, given or evolved
    into. `.formChangeTable = sXFormChangeTable` in species_info binds a species to a table
    in form_change_tables.h whose rows name the target form. Without this, 94 alternate
    forms report as unreachable when they are simply reached a different way.
    """
    tables = collections.defaultdict(list)
    txt = C.read("src", "data", "pokemon", "form_change_tables.h")
    for m in re.finditer(r"static const struct FormChange (\w+)\[\]\s*=\s*\{(.*?)\n\};", txt, re.S):
        for row in re.finditer(r"\{\s*(FORM_CHANGE_\w+)\s*,\s*(SPECIES_\w+)", m.group(2)):
            tables[m.group(1)].append((row.group(1), row.group(2)))

    out = collections.defaultdict(list)
    for p in sorted(glob.glob(C.g("src", "data", "pokemon", "species_info", "*.h"))):
        rel = os.path.relpath(p, C.GAME)
        body = open(p, encoding="utf-8", errors="replace").read()
        for m in re.finditer(r"\[(SPECIES_\w+)\]\s*=\s*\{(.*?)\n    \},", body, re.S):
            src_sp, blk = m.group(1), m.group(2)
            t = re.search(r"\.formChangeTable\s*=\s*(\w+)", blk)
            if not t:
                continue
            for kind, target in tables.get(t.group(1), []):
                if target != src_sp:
                    out[target].append(
                        {"kind": "form", "from": src_sp, "trigger": kind,
                         "source": C.source(rel, key=src_sp)}
                    )
    return out


def apply_breeding(species, by_id):
    """Baby Pokemon come from breeding their evolved form, not from anywhere on a map.

    Azurill, Cleffa and Budew have no encounter, no gift and no evolution INTO them --
    they are the pre-evolution. The rule is "X is breedable if X evolves into some Y that
    is obtainable", but that is circular if Y's only source is evolving X, so it runs as a
    fixpoint over species that already have a non-breeding source. Returns how many gained one.
    """
    added = 0
    while True:
        grew = False
        for s in species:
            if not s["enabled"] or s["obtainable_via"]:
                continue
            for ev in s.get("evolutions") or []:
                t = by_id.get(ev.get("target_species") or "")
                if not t or ev.get("method") == "EVO_NONE" or not t.get("obtainable_via"):
                    continue
                s["obtainable_via"] = [{"kind": "breed", "from": t["id"]}]
                added += 1
                grew = True
                break
        if not grew:
            return added


def from_evolution(species):
    """Inverted evolution graph: who evolves INTO each species."""
    out = collections.defaultdict(list)
    for s in species:
        for ev in s.get("evolutions") or []:
            # EVO_NONE is a breeding link, not an evolution (DATA-AUDIT 9.5).
            if ev.get("method") == "EVO_NONE" or not ev.get("target_species"):
                continue
            out[ev["target_species"]].append(
                {
                    "kind": "evolution",
                    "from": s["id"],
                    "method": ev["method"],
                    "param": ev.get("param"),
                    "level": ev.get("level"),
                    "conditions": ev.get("conditions") or [],
                }
            )
    return out


def main():
    path = os.path.join(C.OUT, "species.json")
    doc = json.load(open(path))
    species = doc["species"]
    by_id = {s["id"]: s for s in species}

    wild = from_encounters()
    evo = from_evolution(species)
    scripts = from_scripts()
    trades = from_trades()
    formch = from_form_change()
    roam = from_roamers()
    starts, start_maps = starters(), starter_maps()
    for sp, picks in starts.items():
        for p in picks:
            scripts[sp].append(
                {
                    "kind": "starter",
                    "map": start_maps.get(p["region"]),
                    "region": p["region"],
                    "source": C.source("src/starter_choose.c", key="sStarterMon"),
                }
            )

    stats = collections.Counter()
    for s in species:
        if not s["enabled"]:
            s["obtainable_via"] = None
            stats["disabled"] += 1
            continue
        src = (
            sorted(wild.get(s["id"], []), key=lambda x: (-x["percent"], x["map"]))
            + evo.get(s["id"], [])
            + sorted(scripts.get(s["id"], []), key=lambda x: json.dumps(x, sort_keys=True))
            + trades.get(s["id"], [])
            + formch.get(s["id"], [])
            + roam.get(s["id"], [])
        )
        s["obtainable_via"] = src or None
        if not src:
            stats["unreachable"] += 1
        else:
            for k in {x["kind"] for x in src}:
                stats[k] += 1
            stats["reachable"] += 1

    bred = apply_breeding(species, by_id)
    stats["breed"] = bred
    stats["unreachable"] -= bred
    stats["reachable"] += bred

    C.write("species.json", doc)

    print(f"enabled {sum(1 for s in species if s['enabled'])}  disabled {stats['disabled']}")
    print(f"  reachable   {stats['reachable']}")
    print(f"  unreachable {stats['unreachable']}  (enabled but nothing produces them)")
    for k in ("wild", "evolution", "form", "breed", "roamer", "starter", "gift", "egg", "static", "trade"):
        if stats[k]:
            print(f"    {k:10s} {stats[k]} species")

    # Every species reachable ONLY by evolving must have a reachable parent, or the chain
    # is rooted in nothing and the guide would tell the reader to evolve something they
    # cannot get.
    evo_only = [
        s for s in species
        if s["enabled"] and s["obtainable_via"] and all(x["kind"] == "evolution" for x in s["obtainable_via"])
    ]
    rootless = []
    for s in evo_only:
        seen, stack, ok = set(), [x["from"] for x in s["obtainable_via"]], False
        while stack:
            p = stack.pop()
            if p in seen:
                continue
            seen.add(p)
            par = by_id.get(p)
            if not par or not par.get("obtainable_via"):
                continue
            if any(x["kind"] != "evolution" for x in par["obtainable_via"]):
                ok = True
                break
            stack += [x["from"] for x in par["obtainable_via"]]
        if not ok:
            rootless.append(s["id"])
    print(f"  evolution-only {len(evo_only)}, of which rootless {len(rootless)}")
    if rootless:
        print("    " + ", ".join(rootless[:8]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
