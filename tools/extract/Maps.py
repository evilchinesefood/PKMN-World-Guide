"""maps.json — one record per data/maps/*/map.json. See docs/SCHEMAS.md, DATA-AUDIT.md 2, 3, 6.

TODO: `gate` and `severity` are emitted as null. progression.json is being written in parallel and
the gate join happens in a later pass — do not invent gate keys here.
"""

import collections, functools, os, re, sys

import Common as C

COPY = (
    "music",
    "weather",
    "map_type",
    "battle_scene",
    "requires_flash",
    "allow_cycling",
    "allow_escaping",
    "allow_running",
    "show_map_name",
)

COUNTED = (
    "connections",
    "warps",
    "object_events",
    "signs",
    "hidden_items",
    "secret_bases",
    "coord_triggers",
    "weather_triggers",
)


def coord(e):
    return {"x": e["x"], "y": e["y"], "elevation": e.get("elevation")}


@functools.lru_cache(maxsize=1)
def warp_consts():
    # 65 warps use a symbolic dest_warp_id (WARP_ID_DYNAMIC, WARP_ID_SECRET_BASE).
    src = C.read("include", "constants", "maps.h")
    pairs = re.findall(r"#define\s+(WARP_ID_\w+)\s+\(?(-?(?:0x)?[0-9A-Fa-f]+)\)?", src)
    return {n: int(v, 0) for n, v in pairs}


def warp_id(v):
    if isinstance(v, int):
        return v
    return int(v) if re.fullmatch(r"-?\d+", v) else warp_consts()[v]


def warp(e):
    return {
        "coord": coord(e),
        "dest_map": e["dest_map"],
        "dest_warp_id": warp_id(e["dest_warp_id"]),
    }


def obj(e):
    return {
        "local_id": e.get("local_id"),
        "graphics_id": e["graphics_id"],
        "coord": coord(e),
        "movement_type": e.get("movement_type"),
        "movement_range": {"x": e.get("movement_range_x"), "y": e.get("movement_range_y")},
        "trainer_type": e.get("trainer_type"),
        "trainer_sight_or_berry_tree_id": e.get("trainer_sight_or_berry_tree_id"),
        "script": e.get("script"),
        "flag": e.get("flag"),
        "kind": e.get("type", "object"),
        "target_local_id": e.get("target_local_id"),
        "target_map": e.get("target_map"),
    }


def split_bg(evs):
    signs, items, bases = [], [], []
    for e in evs:
        t = e.get("type")
        if t == "sign":
            signs.append(
                {
                    "coord": coord(e),
                    "player_facing_dir": e["player_facing_dir"],
                    "script": e["script"],
                }
            )
        elif t == "hidden_item":
            # Engine defaults, tools/mapjson/mapjson.cpp:345-351 — not gaps.
            items.append(
                {
                    "coord": coord(e),
                    "item": e["item"],
                    "flag": e["flag"],
                    "quantity": e.get("quantity", 1),
                    "underfoot": e.get("underfoot", False),
                }
            )
        elif t == "secret_base":
            bases.append({"coord": coord(e), "secret_base_id": e["secret_base_id"]})
        else:
            raise ValueError("unknown bg_event type %r" % t)
    return signs, items, bases


def split_coord(evs):
    trig, wthr = [], []
    for e in evs:
        t = e.get("type")
        if t == "trigger":
            trig.append(
                {
                    "coord": coord(e),
                    "var": e["var"],
                    "var_value": e["var_value"],
                    "script": e["script"],
                }
            )
        elif t == "weather":
            wthr.append({"coord": coord(e), "weather": e["weather"]})
        else:
            raise ValueError("unknown coord_event type %r" % t)
    return trig, wthr


def inherit(field, name, bydir):
    """shared_events_map / shared_scripts_map name a directory, not a MAP_* id."""
    if not name:
        return None, None
    i = bydir.get(name)
    if i:
        return i, None
    return None, C.gap(field, "'%s' is not a map directory; it names an assembly label" % name)


@functools.lru_cache(maxsize=1)
def encounter_maps():
    d = C.load("src", "data", "wild_encounters.json")
    g = next(x for x in d["wild_encounter_groups"] if x["label"] == "gWildMonHeaders")
    return {e["map"] for e in g["encounters"]}


def build():
    ms, lay, enc = C.maps(), C.layouts(), encounter_maps()
    bydir = {m["_dir"]: i for i, m in ms.items()}
    out = []
    for i in sorted(ms):
        m = ms[i]
        ev_from, ev_gap = inherit("shared_events_from", m.get("shared_events_map"), bydir)
        sc_from, sc_gap = inherit("shared_scripts_from", m.get("shared_scripts_map"), bydir)
        ev = ms[ev_from] if ev_from else m
        signs, items, bases = split_bg(ev.get("bg_events") or [])
        trig, wthr = split_coord(ev.get("coord_events") or [])
        l = lay.get(m["layout"])
        r = {
            "id": i,
            "name": m["name"],
            "region": C.region_of_map(m),
            # Sevii is 160 of Kanto's 416 maps and gets its own atlas views, so the
            # sub-region is carried alongside the region rather than inferred by the site.
            "subregion": C.subregion_of_map(m),
            "region_map_section": m["region_map_section"],
            "layout": m["layout"],
            "floor_number": m.get("floor_number"),
            "dimensions": {"width": l["width"], "height": l["height"]} if l else None,
            "connections": [
                {"direction": c["direction"], "offset": c["offset"], "map": c["map"]}
                for c in (m.get("connections") or [])
            ],
            "warps": [warp(w) for w in (ev.get("warp_events") or [])],
            "object_events": [obj(o) for o in (ev.get("object_events") or [])],
            "signs": signs,
            "hidden_items": items,
            "secret_bases": bases,
            "coord_triggers": trig,
            "weather_triggers": wthr,
            "encounters": i if i in enc else None,
            "shared_events_from": ev_from,
            "shared_scripts_from": sc_from,
            "gate": None,
            "severity": None,
            "gaps": [x for x in (ev_gap, sc_gap) if x],
            "source": C.source("data/maps/%s/map.json" % m["_dir"]),
        }
        for k in COPY:
            r[k] = m[k]
        out.append(r)
    return out


def totals(recs, own_only):
    t = collections.Counter()
    for r in recs:
        if own_only and r["shared_events_from"]:
            continue
        for k in COUNTED:
            t[k] += len(r[k])
    return t


def chk(label, got, want):
    ok = got == want
    print("%-28s %-8s %s" % (label, got, "ok" if ok else "FAIL expected %s" % want))
    return ok


def report(recs, deterministic, size):
    own, emitted = totals(recs, True), totals(recs, False)
    reg = collections.Counter(r["region"] for r in recs)
    hid = [h for r in recs for h in r["hidden_items"]]
    ok = [
        chk("maps", len(recs), 1195),
        chk("region kanto", reg["kanto"], 416),
        chk("region johto", reg["johto"], 254),
        chk("region hoenn", reg["hoenn"], 458),
        chk("region shared", reg["shared"], 67),
        chk("hidden_items", own["hidden_items"], 304),
        chk("hidden_items complete", sum(1 for h in hid if h["item"] and h["flag"]), len(hid)),
        # Three counts dropped at the 2b1fba48 re-pin, each fully accounted for by a deletion
        # upstream. Game issue #38 removed the four events sitting beyond the addressable
        # border: signs -2 (MeteorFalls_1F_1R/1F_2R) and object_events -2 (FiveIsland_Frlg and
        # Route7_Frlg). #39 deleted EcruteakCity's dead Battle Frontier warp: warps -1.
        chk("signs", own["signs"], 1587),
        chk("secret_bases", own["secret_bases"], 75),
        chk("object_events", own["object_events"], 6923),
        chk("warps", own["warps"], 3433),
        chk("coord_triggers", own["coord_triggers"], 932),
        chk("weather_triggers", own["weather_triggers"], 86),
        chk("connections", own["connections"], 366),
        chk("maps missing layout", sum(1 for r in recs if not r["dimensions"]), 0),
        chk("deterministic", deterministic, True),
    ]
    print()
    print("inherited events  %s resolved" % sum(1 for r in recs if r["shared_events_from"]))
    print(
        "inherited scripts %s resolved, %s unresolvable"
        % (
            sum(1 for r in recs if r["shared_scripts_from"]),
            sum(1 for r in recs if r["gaps"] and not r["shared_scripts_from"]),
        )
    )
    print("gaps              %s" % sum(len(r["gaps"]) for r in recs))
    print(
        "emitted objects   %s (census %s + inherited)"
        % (emitted["object_events"], own["object_events"])
    )
    print("size              %.1f MB" % (size / 1e6))
    return all(ok)


def main():
    recs = build()
    p = C.write("maps.json", dict(C.header(), maps=recs))
    with open(p, "rb") as f:
        a = f.read()
    C.write("maps.json", dict(C.header(), maps=build()))
    with open(p, "rb") as f:
        b = f.read()
    if not report(recs, a == b, len(b)):
        sys.exit(1)


if __name__ == "__main__":
    main()
