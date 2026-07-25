"""Wild encounters -> data/generated/encounters.json. See docs/SCHEMAS.md, DATA-AUDIT.md 4.

Mirrors game/tools/wild_encounters/wild_encounters_to_header.py: slot percentages and the
fishing rod split come from the JSON's own `fields` array, never from constants here.
"""

import functools, glob, re, sys, tempfile
import Common as C

SRC = "src/data/wild_encounters.json"
ENABLED_H = "include/config/species_enabled.h"
GROUP = "gWildMonHeaders"  # the only for_maps group; pyramid and pike are not map-linked


# --- species enablement ------------------------------------------------------
# A species is catchable only if its P_FAMILY_* guard is not literally FALSE. Same rule as
# the game's Testing/ValidateGen13.py. Species.py will want this too — lift it into Common.py
# once both extractors exist.


def disabled_families():
    return set(re.findall(r"#define\s+(P_FAMILY_\w+)\s+FALSE\b", C.read(*ENABLED_H.split("/"))))


def species_families():
    """species -> innermost enclosing P_FAMILY_* guard in gen_*_families.h."""
    out = {}
    for p in sorted(glob.glob(C.g("src", "data", "pokemon", "species_info", "gen_*_families.h"))):
        stack = []
        with open(p, encoding="utf-8", errors="replace") as f:
            for line in f:
                m = re.match(r"\s*#if\s+(P_FAMILY_\w+)", line)
                if m:
                    stack.append(m.group(1))
                elif re.match(r"\s*#(if|ifdef|ifndef)\b", line):
                    stack.append(None)
                elif re.match(r"\s*#(else|elif)\b", line):
                    # an #else arm is not guarded by the family above it
                    if stack:
                        stack[-1] = None
                elif re.match(r"\s*#endif", line):
                    if stack:
                        stack.pop()
                else:
                    m = re.match(r"\s*\[(SPECIES_\w+)\]\s*=", line)
                    fam = next((s for s in reversed(stack) if s), None)
                    if m and fam:
                        out[m.group(1)] = fam
    return out


@functools.lru_cache(maxsize=1)
def _enablement():
    fams, dis = species_families(), disabled_families()
    if len(fams) < 1000 or len(dis) < 100:
        raise SystemExit(f"enablement parse looks wrong: {len(fams)} species, {len(dis)} disabled")
    return fams, dis


def species_enabled(sp):
    fams, dis = _enablement()
    return fams.get(sp) not in dis  # unguarded species compile unconditionally


# --- extraction --------------------------------------------------------------


def group():
    for grp in C.load(*SRC.split("/"))["wild_encounter_groups"]:
        if grp["label"] == GROUP:
            return grp
    raise SystemExit(f"{GROUP} not found in {SRC}")


def method_name(t):
    return t[:-5] if t.endswith("_mons") else t


def slots(mons, rates, idxs):
    out = []
    for i in idxs:
        m = mons[i]
        out.append(
            {
                "slot": i,
                "percent": rates[i],
                "species": m["species"],
                "min_level": m.get("min_level", 2),
                "max_level": m.get("max_level", 100),
                "species_enabled": species_enabled(m["species"]),
            }
        )
    return out


def method(entry, field):
    """encounter_rate is the per-step chance and is unrelated to the slot percentages."""
    rates, mons = field["encounter_rates"], entry["mons"]
    out = {"encounter_rate": entry["encounter_rate"]}
    groups = field.get("groups")
    if groups:
        out["rods"] = {
            name: {
                "slots": slots(mons, rates, idxs),
                "percent_total": sum(rates[i] for i in idxs),
            }
            for name, idxs in groups.items()
        }
    else:
        idxs = list(range(len(rates)))
        out["slots"] = slots(mons, rates, idxs)
        out["percent_total"] = sum(rates)
    return out


def records():
    grp = group()
    maps = C.maps()
    out = []
    for e in grp["encounters"]:
        m = maps.get(e["map"])
        out.append(
            {
                "map": e["map"],
                "base_label": e["base_label"],
                "region": C.region_of_map(m) if m else None,
                "methods": {
                    method_name(f["type"]): method(e[f["type"]], f)
                    for f in grp["fields"]
                    if f["type"] in e
                },
                "gate": None,  # joined in a later pass
                "severity": None,
                "source": C.source(SRC, e["base_label"]),
            }
        )
    out.sort(key=lambda r: (r["map"], r["base_label"]))
    return out


def payload(recs):
    return dict(C.header(), encounters=recs)


# --- verification ------------------------------------------------------------

EXPECT_RECORDS = 479
EXPECT_MAPS = 331
EXPECT_REGIONS = {"kanto": 124, "johto": 91, "hoenn": 116}


def fail(msg):
    print(f"FAIL — {msg}")
    sys.exit(1)


def check(recs, path):
    if len(recs) != EXPECT_RECORDS:
        fail(f"{len(recs)} records, expected {EXPECT_RECORDS}")

    keys = {(r["map"], r["base_label"]) for r in recs}
    if len(keys) != len(recs):
        fail(f"{len(recs) - len(keys)} duplicate (map, base_label) keys")

    by_map = {}
    for r in recs:
        by_map.setdefault(r["map"], []).append(r)
    if len(by_map) != EXPECT_MAPS:
        fail(f"{len(by_map)} distinct maps, expected {EXPECT_MAPS}")

    known = C.maps()
    dangling = sorted(m for m in by_map if m not in known)
    if dangling:
        fail(f"{len(dangling)} dangling map refs: {dangling[:5]}")

    disabled = empty = 0
    for r in recs:
        for name, meth in r["methods"].items():
            for label, part in ([(name, meth)] if "slots" in meth else meth["rods"].items()):
                if part["percent_total"] != 100:
                    fail(f"{r['base_label']} {label} percent_total={part['percent_total']}")
                disabled += sum(1 for s in part["slots"] if not s["species_enabled"])
                empty += sum(1 for s in part["slots"] if s["species"] == "SPECIES_NONE")
    if disabled:
        fail(f"{disabled} slots reference a disabled species")

    regions = {}
    for m, rs in by_map.items():
        regions[rs[0]["region"]] = regions.get(rs[0]["region"], 0) + 1
    if regions != EXPECT_REGIONS:
        fail(f"region coverage {regions}, expected {EXPECT_REGIONS}")

    with tempfile.TemporaryDirectory() as d:
        C.write("encounters.json", payload(records()), d)
        with open(path, "rb") as a, open(f"{d}/encounters.json", "rb") as b:
            if a.read() != b.read():
                fail("rebuild is not byte-identical")

    multi = sum(1 for rs in by_map.values() if len(rs) > 1)
    widest = max(by_map.items(), key=lambda kv: len(kv[1]))
    methods = {}
    slot_count = 0
    for r in recs:
        for name, meth in r["methods"].items():
            methods[name] = methods.get(name, 0) + 1
            slot_count += sum(
                len(p["slots"]) for p in ([meth] if "slots" in meth else meth["rods"].values())
            )
    print(f"OK — {len(recs)} records, {len(by_map)} maps, {slot_count} slots, 0 dangling")
    print(f"     regions {regions}")
    print(f"     methods {methods}")
    print(f"     multi-table maps {multi}, widest {widest[0]} x{len(widest[1])}")
    print(f"     disabled-species slots {disabled}, SPECIES_NONE slots {empty}")
    print("     rebuild byte-identical")


def main():
    recs = records()
    path = C.write("encounters.json", payload(recs))
    print(path)
    check(recs, path)


if __name__ == "__main__":
    main()
