"""Assigns `gate` and `severity` to maps, encounters, trainers and items. Runs LAST.

Every gate key comes from data/generated/progression.json -- nothing here invents one.
A record only gets a gate when a real file in game/ says so; otherwise it stays null and
`gate_rule` records *why*, because a wrong gate silently mis-hides or mis-reveals content
and a visible hole does not.

Rules that fire, all verified against the pin (see the coverage report on stdout):

  awards_champion   the map's own scripts.inc -- or a label it calls, resolved one level --
                    runs `setflag FLAG_<REGION>_CHAMPION`. That is the Hall of Fame.
  league_trainer    the map hosts a placed trainer of class Elite Four / Champion whose
                    `anomaly` is null. The 22 hijacked FRLG-boss slots (DATA-AUDIT 0.5) are
                    excluded by that filter: TRAINER_LYLE renders as LORELEI but is fought
                    in Petalburg Woods at Lv 8.
  champion_native   a script guards a `warp` with callnative RegionHub_ScrIs{Any,Two,Three}
                    RegionChampion AND the target map has zero other inbound edges in the
                    whole map graph, so that warp is the only way in. The in-degree test is
                    the point: MAP_BATTLE_FRONTIER_RECEPTION_GATE is guarded the same way but
                    has a back door, so it is rejected rather than wrongly gated.
  field_move        Flash for `requires_flash` maps, Dive for MAP_TYPE_UNDERWATER maps, and
                    Surf / Rock Smash for encounter tables whose EVERY method needs the move
                    (fishing is excluded -- a rod works from a shore tile). Badge INDEX per
                    region is parsed out of src/field_move.c, never assumed: Kanto Flash is
                    index 0, Johto Surf is index 3, Kanto Rock Smash is index 5.
  map_gate          encounters and trainers inherit the gate of the map they sit on.
  world_championship_registrar
                    the 16 FRONTIER_TRAINER_WC_* ids are seeded only by the Dome registrar,
                    which is guarded by IsNRegionChampion(3).

Rules deliberately NOT implemented, and why -- see the `rejected` block in the report:

  * Region floor. progression.json has no region-entry key (its 30 keys are 24 badges, 3
    champions, 3 globals). The lowest key in a region is `{region}:badge-1`, and using it as
    a floor would hide every pre-first-badge town. Nothing is invented to fill the hole.
  * Badge flag checks inside a map's scripts (brief rule 3) at MAP granularity. Disproved on
    real data: ViridianCity_Frlg checks FLAG_KANTO_BADGE_2..7, but that check is
    ViridianCity_EventScript_TryUnlockGym -- it gates the gym DOOR, not the city, which is
    the second map of the Kanto campaign. The same shape appears in 60+ map dirs (gym
    statues, post-badge NPC swaps), so no direction of the check is safe to lift to the map.
  * Water/cut reachability. Would need a collision-and-connection reachability graph that
    cannot be verified here. MAP_TYPE_OCEAN_ROUTE looks like a cheap stand-in and is not:
    it includes MAP_OLIVINE_CITY_PORT_OUTSIDE and two walkable Safari Zone quadrants.

A gate is a FLOOR: the earliest requirement a real file proves, not a claim that nothing
else is needed. MAP_VICTORY_ROAD_B1F gets hoenn:badge-2 because it is dark and Flash needs
that badge; the league's own 8-badge requirement lives on a different map's script and is
not asserted here.

`severity` is set on every record, including ungated ones: null gate -> routine, badge gate
-> story, champion or global gate -> endgame. Battle Frontier content is endgame regardless
of gate, since it is facility content even though it turns out not to be gated.
"""

import os, re, sys, json, glob, collections

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import Common as C

LABEL = re.compile(r"^(\w+)::", re.M)
CHAMPION_SET = re.compile(r"^\s*setflag\s+FLAG_(KANTO|JOHTO|HOENN)_CHAMPION\b", re.M)
CALLS = re.compile(r"^\s*(?:call|goto)\s+(\w+)", re.M)
NATIVE_WARP = re.compile(
    r"callnative\s+RegionHub_ScrIs(Any|Two|Three)RegionChampion(.*?)^\s*warp\s+(MAP_\w+)",
    re.M | re.S,
)
FN = re.compile(r"static bool32 IsFieldMoveUnlocked_(\w+)\(void\)\s*\{(.*?)^\}", re.M | re.S)
HAS_BADGE = re.compile(
    r"HasBadge\(\s*region\s*,\s*region\s*==\s*REGION_(\w+)\s*\?\s*(\d+)\s*:\s*(\d+)\s*\)"
)
CUR_BADGE = re.compile(r"HasCurrentRegionBadge\(\s*(\d+)\s*\)")
TOOL_ITEM = re.compile(r"\.toolItemId\s*=\s*(ITEM_\w+)")

REGIONS = ("kanto", "johto", "hoenn")
LEAGUE_CLASSES = re.compile(r"^(Elite Four|Champion)\b")
NATIVE_KEY = {"Any": "global:champion-any", "Two": "global:champion-two", "Three": "global:champion-all"}
# Encounter method -> the field move you must already be using to meet it. Fishing is not
# here on purpose: a rod works from a shore tile, so a fishing table is not Surf-gated.
METHOD_MOVE = {"water": "Surf", "rock_smash": "RockSmash"}


# --- progression -------------------------------------------------------------


def gate_index(prog):
    return {g["key"]: g for g in prog["gates"]}


def badge_key(ix, region, idx):
    """0-based badge index -> gate key. GetBadgeFlag() takes 0..7; FLAG_*_BADGE_N is 1-based."""
    k = "%s:badge-%d" % (region, idx + 1)
    return k if k in ix else None


def champion_key(ix, region):
    k = "%s:champion" % region
    return k if k in ix else None


# Only used to break ties when two rules land on the same gate: report the one carrying the
# most direct evidence. Lower wins.
RULE_RANK = [
    "awards_champion",
    "champion_native",
    "league_trainer",
    "league_class",
    "field_move:dive",
    "field_move:flash",
    "field_move:method",
    "world_championship_registrar",
    "location_gate",
    "map_gate",
]


def pick(ix, cands, how):
    """cands: [(key, rule, src)]. `how` is max for a conjunction of requirements (you need
    both, so the later one binds) and min for alternatives (earliest availability)."""
    cands = [c for c in cands if c[0]]
    if not cands:
        return None, None, None
    f = max if how == "max" else min
    order = f(ix[c[0]]["order"] for c in cands)
    tied = [c for c in cands if ix[c[0]]["order"] == order]
    return min(tied, key=lambda c: RULE_RANK.index(c[1]))


def severity_of(ix, key):
    if not key:
        return "routine"
    return "story" if ":badge-" in key else "endgame"


FACILITY_MAPSEC = "MAPSEC_BATTLE_FRONTIER"


# --- src/field_move.c --------------------------------------------------------


def field_moves():
    """{move: {region: badge_index}} straight out of the source table. Moves with no badge
    requirement are absent. Also returns the tool items that bypass the badge gate."""
    txt = C.read("src", "field_move.c")
    out = {}
    for name, body in FN.findall(txt):
        m = HAS_BADGE.search(body)
        if m:
            named, a, b = m.group(1).lower(), int(m.group(2)), int(m.group(3))
            out[name] = {r: (a if r == named else b) for r in REGIONS}
            continue
        m = CUR_BADGE.search(body)
        if m:
            out[name] = {r: int(m.group(1)) for r in REGIONS}
    return out, sorted(set(TOOL_ITEM.findall(txt)))


def bypass_is_live(tools, items):
    """QOL_FIELD_MOVES_ITEM_GATE lets a tool item skip the badge. At this pin no script
    gives one and no mart sells one, so the badge is the only path. If that ever changes
    the field-move rules must stop firing, so this is checked rather than assumed."""
    have = {i["id"] for i in items if i.get("locations")}
    return sorted(t for t in tools if t in have)


# --- game scripts ------------------------------------------------------------


def index_scripts():
    ix = {}
    for p in sorted(glob.glob(C.g("data", "**", "*.inc"), recursive=True)):
        rel = os.path.relpath(p, C.GAME).replace(os.sep, "/")
        with open(p, encoding="utf-8", errors="replace") as f:
            txt = f.read()
        marks = list(LABEL.finditer(txt))
        for n, m in enumerate(marks):
            end = marks[n + 1].start() if n + 1 < len(marks) else len(txt)
            ix.setdefault(m.group(1), (txt[m.end() : end], rel, txt[: m.start()].count("\n") + 1))
    return ix


def champion_awarding_maps(labels):
    """map dir -> (region, source). A map awards a champion flag if its own scripts.inc sets
    one, or if a label it calls does. One level of resolution covers all three Halls of Fame:
    the Hoenn and Kanto setters live in data/scripts/hall_of_fame*.inc."""
    out = {}
    for p in sorted(glob.glob(C.g("data", "maps", "*", "scripts.inc"))):
        d = os.path.basename(os.path.dirname(p))
        with open(p, encoding="utf-8", errors="replace") as f:
            txt = f.read()
        rel = "data/maps/%s/scripts.inc" % d
        m = CHAMPION_SET.search(txt)
        if m:
            out[d] = (m.group(1).lower(), C.source(rel, line=txt[: m.start()].count("\n") + 1))
            continue
        for lbl in sorted(set(CALLS.findall(txt))):
            body = labels.get(lbl)
            if not body:
                continue
            m = CHAMPION_SET.search(body[0])
            if m:
                out[d] = (m.group(1).lower(), C.source(body[1], key=lbl))
                break
    return out


def native_guarded_warps(labels):
    """Warp targets sitting behind a callnative RegionHub_ScrIs*RegionChampion guard.
    {map_id: (gate_key, source)}."""
    out = {}
    for p in sorted(glob.glob(C.g("data", "**", "*.inc"), recursive=True)):
        rel = os.path.relpath(p, C.GAME).replace(os.sep, "/")
        with open(p, encoding="utf-8", errors="replace") as f:
            txt = f.read()
        for m in NATIVE_WARP.finditer(txt):
            if "::" in m.group(2):  # guard and warp are in different script bodies
                continue
            out.setdefault(m.group(3), (NATIVE_KEY[m.group(1)], C.source(rel, line=txt[: m.start()].count("\n") + 1)))
    return out


def in_degree(maps):
    n = collections.Counter()
    for m in maps:
        for w in m["warps"]:
            if w["dest_map"] != m["id"]:
                n[w["dest_map"]] += 1
        for c in m["connections"]:
            if c["map"] != m["id"]:
                n[c["map"]] += 1
    return n


# --- record passes -----------------------------------------------------------


def map_dir(m):
    return m["source"]["file"].split("/")[2]


def loc_map(loc, dir2id):
    """Ground and hidden locations carry `map`; gifts and shop stock carry only the script
    they came from. Resolve those through the directory when the script is a map script --
    the shared data/scripts/*.inc ones belong to no single map and stay unresolved."""
    if loc.get("map"):
        return loc["map"]
    f = ((loc.get("source") or {}).get("file")) or ""
    p = f.split("/")
    return dir2id.get(p[2]) if len(p) > 3 and p[0] == "data" and p[1] == "maps" else None


def gate_maps(ix, maps, trainers, labels, fm, fm_ok):
    awards = champion_awarding_maps(labels)
    guarded = native_guarded_warps(labels)
    deg = in_degree(maps)

    league = collections.defaultdict(list)
    for t in trainers:
        p = t.get("placement") or {}
        if t.get("anomaly") or not p.get("map") or not LEAGUE_CLASSES.match(t.get("class") or ""):
            continue
        league[p["map"]].append(t["trainer_id"])

    rejected = collections.defaultdict(list)
    out = {}
    for m in maps:
        region, cands = m["region"], []
        d = map_dir(m)
        if d in awards and awards[d][0] == region:
            cands.append((champion_key(ix, awards[d][0]), "awards_champion", awards[d][1]))
        if m["id"] in league and region in REGIONS:
            cands.append(
                (
                    champion_key(ix, region),
                    "league_trainer",
                    C.source("src/data/trainers.party", key="trainer_id=%d" % min(league[m["id"]])),
                )
            )
        if m["id"] in guarded:
            if deg[m["id"]]:
                rejected["champion_native_has_other_entrance"].append(m["id"])
            else:
                cands.append((guarded[m["id"]][0], "champion_native", guarded[m["id"]][1]))
        for need, move, rule in (
            (m["requires_flash"], "Flash", "field_move:flash"),
            (m["map_type"] == "MAP_TYPE_UNDERWATER", "Dive", "field_move:dive"),
        ):
            if not (need and region in REGIONS):
                continue
            if fm_ok and move in fm:
                cands.append(
                    (
                        badge_key(ix, region, fm[move][region]),
                        rule,
                        C.source("src/field_move.c", key="IsFieldMoveUnlocked_" + move),
                    )
                )
            else:
                rejected["field_move_bypass_live"].append(m["id"])
        out[m["id"]] = pick(ix, cands, "max")
    detail = {
        "champion_awarding_maps": {k: v[0] for k, v in sorted(awards.items())},
        "champion_guarded_warps": {k: v[0] for k, v in sorted(guarded.items())},
        "rejected": {k: sorted(v) for k, v in sorted(rejected.items())},
    }
    return out, detail


def apply_gate(rec, ix, key, rule, src=None):
    rec["gate"] = key
    rec["gate_rule"] = rule
    rec["severity"] = severity_of(ix, key)
    if src and key:
        rec["gate_source"] = src
    else:
        rec.pop("gate_source", None)
    if isinstance(rec.get("gaps"), list):
        rec["gaps"] = [x for x in rec["gaps"] if x.get("field") != "gate"]
        if not key:
            rec["gaps"].append(C.gap("gate", rule))
        rec["gaps"].sort(key=lambda x: (x.get("field") or "", x.get("reason") or ""))


def build(data):
    prog = data["progression"]
    ix = gate_index(prog)
    maps, encs = data["maps"]["maps"], data["encounters"]["encounters"]
    trs, items = data["trainers"]["trainers"], data["items"]["items"]
    fr = data["trainers"]["frontier_trainers"]

    fm, tools = field_moves()
    live = bypass_is_live(tools, items)
    fm_ok = not live

    labels = index_scripts()
    mg, detail = gate_maps(ix, maps, trs, labels, fm, fm_ok)

    # Region floor, applied to mg BEFORE anything reads it so encounters, trainers and items
    # inherit it too. A map with no stronger evidence still belongs to a region, and
    # {region}:entry is always-satisfied, so carrying it is honest rather than a guess: it says
    # "this is Kanto content" and nothing more. Without a floor 96% of records are null and the
    # brief's "every chunk has a gate" CI rule cannot be met. `shared` maps (hub, secret bases,
    # link rooms) genuinely belong to no region and stay null -- see DATA-AUDIT 2.4.
    for m in maps:
        key, rule, src = mg[m["id"]]
        if not key and m.get("region") in ("kanto", "johto", "hoenn"):
            mg[m["id"]] = (f"{m['region']}:entry", "region_floor", None)

    for m in maps:
        key, rule, src = mg[m["id"]]
        apply_gate(m, ix, key, rule or "none:no_evidence", src)

    facility = {m["id"] for m in maps if m["region_map_section"] == FACILITY_MAPSEC}
    for m in maps:
        if m["id"] in facility and m["severity"] == "routine":
            m["severity"] = "endgame"

    for e in encs:
        cands = []
        if mg.get(e["map"], (None,))[0]:
            cands.append((mg[e["map"]][0], "map_gate", None))
        moves = {METHOD_MOVE.get(k) for k in e["methods"]}
        if fm_ok and None not in moves and e["region"] in REGIONS:
            idxs = [fm[mv][e["region"]] for mv in moves if mv in fm]
            if len(idxs) == len(moves):
                cands.append(
                    (
                        badge_key(ix, e["region"], max(idxs)),
                        "field_move:method",
                        C.source("src/field_move.c", key="+".join(sorted(moves))),
                    )
                )
        key, rule, src = pick(ix, cands, "max")
        apply_gate(e, ix, key, rule or "none:no_evidence", src)
        if e["map"] in facility and e["severity"] == "routine":
            e["severity"] = "endgame"

    for t in trs:
        p = t.get("placement") or {}
        cands, league_class = [], LEAGUE_CLASSES.match(t.get("class") or "")
        if p.get("map") and mg.get(p["map"], (None,))[0]:
            cands.append((mg[p["map"]][0], "map_gate", None))
        if league_class and not t.get("anomaly") and p.get("region") in REGIONS:
            cands.append(
                (
                    champion_key(ix, p["region"]),
                    "league_class",
                    C.source(t["source"]["file"], key="Class: " + t["class"], line=t["source"]["line"]),
                )
            )
        key, rule, src = pick(ix, cands, "max")
        if not key:
            # The 22 hijacked slots carry a Kanto boss class on an ordinary route id
            # (DATA-AUDIT 0.5), so their class is not evidence of league content.
            rule = (
                "none:anomaly_constant_is_not_identity"
                if t.get("anomaly") and league_class
                else "none:unplaced" if not p.get("map") else "none:map_ungated"
            )
        apply_gate(t, ix, key, rule, src)
        if p.get("map") in facility and t["severity"] == "routine":
            t["severity"] = "endgame"

    for t in fr:
        # Pool-based facility trainers. The Battle Frontier itself cannot be gated:
        # MAP_ECRUTEAK_CITY warps straight into MAP_BATTLE_FRONTIER_BATTLE_TOWER_LOBBY with no
        # guard, and that lobby exits to BATTLE_FRONTIER_OUTSIDE_EAST -- an ungated back door
        # into the whole facility. Only the World Championship pool has a real gate.
        if t["constant"].startswith("FRONTIER_TRAINER_WC_"):
            apply_gate(
                t,
                ix,
                "global:champion-all",
                "world_championship_registrar",
                C.source("data/maps/BattleFrontier_BattleDomeLobby/scripts.inc", key="EventScript_Maniac", line=399),
            )
        else:
            apply_gate(t, ix, None, "none:frontier_reachable_ungated")
            t["severity"] = "endgame"

    dir2id = {map_dir(m): m["id"] for m in maps}
    for it in items:
        locs = it.get("locations") or []
        if not locs:
            apply_gate(it, ix, None, "none:no_location")
            continue
        mids = [loc_map(l, dir2id) for l in locs]
        if any(m is None for m in mids):
            apply_gate(it, ix, None, "none:location_map_unresolved")
            continue
        keys = [mg[m][0] for m in mids]
        if any(k is None for k in keys):
            apply_gate(it, ix, None, "none:location_ungated")
            continue
        if len({ix[k]["region"] for k in keys}) > 1:
            # No region ordering exists (DATA-AUDIT 5B.4), so "earliest" is undefined here.
            apply_gate(it, ix, None, "none:locations_span_regions")
            continue
        key, rule, _ = pick(ix, [(k, "location_gate", None) for k in keys], "min")
        apply_gate(it, ix, key, rule)

    detail["battle_frontier_ungated_backdoor"] = {
        "warp": "MAP_ECRUTEAK_CITY -> MAP_BATTLE_FRONTIER_BATTLE_TOWER_LOBBY",
        "source": "data/maps/EcruteakCity/map.json warp_events[14]",
        "effect": "the lobby exits to MAP_BATTLE_FRONTIER_OUTSIDE_EAST with no flag check, so no "
        "Battle Frontier map can carry global:champion-any",
    }
    detail["field_move_badge_index"] = fm
    detail["field_move_tools_obtainable"] = live
    detail["field_move_tools_note"] = (
        "QOL_FIELD_MOVES_ITEM_GATE is TRUE, so a tool item would bypass the badge; at this pin "
        "none of the six is sold, given or on the ground, so the badge is the only path. The "
        "field-move rules stop firing if that list is ever non-empty."
    )
    return detail


# --- report ------------------------------------------------------------------


def tally(recs):
    by = collections.Counter(r["gate_rule"] for r in recs)
    gated = sum(v for k, v in by.items() if not k.startswith("none:"))
    return {
        "records": len(recs),
        "gated": gated,
        "null": len(recs) - gated,
        "gated_pct": round(100.0 * gated / len(recs), 1) if recs else 0.0,
        "by_rule": dict(sorted(by.items())),
        "by_severity": dict(sorted(collections.Counter(r["severity"] for r in recs).items())),
        "by_gate": dict(sorted(collections.Counter(r["gate"] for r in recs if r["gate"]).items())),
    }


def serialize(payload):
    return json.dumps(payload, indent=1, sort_keys=True, ensure_ascii=False) + "\n"


WRITE = ["maps", "encounters", "trainers", "items"]
FILES = WRITE + ["progression"]  # progression is read-only: it defines the keys


def main():
    data = {n: json.load(open(os.path.join(C.OUT, n + ".json"), encoding="utf-8")) for n in FILES}
    meta = build(data)
    once = {n: serialize(data[n]) for n in FILES}

    # Determinism: Gates.py rewrites its own inputs, so a second pass over the gated files
    # must reproduce the same bytes or the output is not stable across runs.
    again = {n: json.loads(once[n]) for n in FILES}
    build(again)
    drift = sorted(n for n in FILES if serialize(again[n]) != once[n])
    if drift:
        print("NOT DETERMINISTIC: %s" % drift, file=sys.stderr)
        return 1

    for n in WRITE:
        with open(os.path.join(C.OUT, n + ".json"), "w", encoding="utf-8") as f:
            f.write(once[n])

    report = {
        "game_commit": C.game_commit(),
        "gate_keys_available": sorted(gate_index(data["progression"])),
        "deterministic": True,
        "gate_semantics": "a gate is a FLOOR -- the earliest requirement that a real file in "
        "game/ proves, not a claim that nothing else is needed. MAP_VICTORY_ROAD_B1F carries "
        "hoenn:badge-2 because it is dark and Flash needs that badge; the league's own 8-badge "
        "requirement is not provable from the map's data, so it is not asserted.",
        "entities": {
            "maps": tally(data["maps"]["maps"]),
            "encounters": tally(data["encounters"]["encounters"]),
            "trainers": tally(data["trainers"]["trainers"]),
            "frontier_trainers": tally(data["trainers"]["frontier_trainers"]),
            "items": tally(data["items"]["items"]),
        },
        "evidence": meta,
        "not_implemented": {
            "region_floor": "progression.json has no region-entry key; the lowest key in a region is "
            "{region}:badge-1 and using it as a floor would hide every pre-first-badge map",
            "script_badge_checks_on_maps": "disproved on real data -- ViridianCity_Frlg checks "
            "FLAG_KANTO_BADGE_2..7 in ViridianCity_EventScript_TryUnlockGym, which gates the gym "
            "door, not the city",
            "water_cut_reachability": "needs a collision + connection reachability graph that "
            "cannot be verified from the pinned tree here",
            "map_type_ocean_route": "looks like a Surf gate and is not: the 14 MAP_TYPE_OCEAN_ROUTE "
            "maps include MAP_OLIVINE_CITY_PORT_OUTSIDE and two walkable Safari Zone quadrants. "
            "MAP_TYPE_UNDERWATER does hold, and is used",
        },
    }
    print(json.dumps(report, indent=1, sort_keys=True, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
