"""Fills in items.json's `locations` array. Runs after Maps.py and Items.py.

Four sources, and GROUND ITEMS use a different mechanism in each region (DATA-AUDIT 9.1).
That is the whole reason this is its own pass: an extractor that handles only the Hoenn
mechanism drops 246 items and still reports a clean run.

  Hoenn  Common_EventScript_FindItem, and the item id lives on the OBJECT EVENT, in a
         field named trainer_sight_or_berry_tree_id (read by
         GetItemBallIdAndAmountFromTemplate). Nothing about the name suggests that.
  Kanto  bespoke per-ball labels, nearly all in one data/scripts/item_ball_scripts_frlg.inc
  Johto  bespoke per-ball labels, scattered across ~23 per-map scripts.inc

Gifts have their own trap: giveitem_msg (Kanto only) wraps additem, so the ITEM IS
ARGUMENT TWO. A `giveitem` regex reads the message label as the item and runs clean.

Not every item-ball sprite is an item, so the resolved count is deliberately lower than
the number of balls. The `via` buckets record why each one was skipped:
  runtime_random      Battle Pyramid balls, rolled per run -- no fixed location exists
  script_no_finditem  ball sprite used as scenery or a battle trigger: the Electrodes,
                      the rival's Poke Ball, the starter and Eevee gift balls
  unknown_label       "script": "0x0", i.e. no script at all -- the Contest Halls
"""

import os, re, sys, json, glob, collections

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import Common as C

LABEL = re.compile(r"^(\w+)::", re.M)
FINDITEM = re.compile(r"\bfinditem\s+(ITEM_\w+)")
GIVEITEM = re.compile(r"^\s*giveitem\s+(ITEM_\w+)", re.M)
GIVEITEM_MSG = re.compile(r"^\s*giveitem_msg\s+\w+\s*,\s*(ITEM_\w+)", re.M)
ADDITEM = re.compile(r"^\s*additem\s+(ITEM_\w+)", re.M)
POKEMART = re.compile(r"^\s*pokemart\s+(\w+)", re.M)
MART_ITEM = re.compile(r"\.2byte\s+(ITEM_\w+)")


def index_scripts():
    ix = {}
    for p in glob.glob(C.g("data", "**", "*.inc"), recursive=True):
        rel = os.path.relpath(p, C.GAME)
        with open(p, encoding="utf-8", errors="replace") as f:
            txt = f.read()
        marks = list(LABEL.finditer(txt))
        for n, m in enumerate(marks):
            end = marks[n + 1].start() if n + 1 < len(marks) else len(txt)
            ix[m.group(1)] = (txt[m.end():end], rel, txt[: m.start()].count("\n") + 1)
    return ix


def ground(maps, ix, stats):
    for m in maps:
        for o in m["object_events"]:
            if o.get("graphics_id") != "OBJ_EVENT_GFX_ITEM_BALL":
                continue
            s = o.get("script") or ""
            item = via = None
            if s == "Common_EventScript_FindItem":
                cand = o.get("trainer_sight_or_berry_tree_id")
                if isinstance(cand, str) and cand.startswith("ITEM_"):
                    item, via = cand, "template"
                else:
                    via = "template_nonliteral"
            elif "BattlePyramid" in s:
                via = "runtime_random"
            elif s in ix:
                hit = FINDITEM.search(ix[s][0])
                item, via = (hit.group(1) if hit else None), ("script" if hit else "script_no_finditem")
            else:
                via = "unknown_label"
            stats[via] += 1
            if item:
                yield item, {"kind": "ground", "map": m["id"], "region": m["region"],
                             "coord": o["coord"], "via": via}


def main():
    ip = os.path.join(C.OUT, "items.json")
    items = json.load(open(ip))
    maps = json.load(open(os.path.join(C.OUT, "maps.json")))["maps"]
    ix = index_scripts()
    locs = collections.defaultdict(list)
    stats = collections.Counter()

    for item, rec in ground(maps, ix, stats):
        locs[item].append(rec)

    hidden = 0
    for m in maps:
        for h in m["hidden_items"]:
            hidden += 1
            locs[h["item"]].append({"kind": "hidden", "map": m["id"], "region": m["region"],
                                    "coord": h["coord"], "quantity": h.get("quantity"),
                                    "underfoot": h.get("underfoot")})

    marts = set()
    gifts = 0
    for label, (body, rel, line) in ix.items():
        for mm in POKEMART.finditer(body):
            stock = ix.get(mm.group(1))
            if not stock:
                continue
            marts.add(mm.group(1))
            for it in MART_ITEM.findall(stock[0]):
                if it != "ITEM_NONE":
                    locs[it].append({"kind": "shop", "script": label, "source": C.source(rel, line=line)})
        for pat in (GIVEITEM_MSG, GIVEITEM, ADDITEM):
            for mm in pat.finditer(body):
                gifts += 1
                locs[mm.group(1)].append({"kind": "gift", "script": label, "source": C.source(rel, line=line)})

    for r in items["items"]:
        got = locs.get(r["id"])
        r["locations"] = sorted(got, key=lambda x: json.dumps(x, sort_keys=True)) if got else None
    C.write("items.json", items)

    byregion = collections.Counter(
        l["region"] for v in locs.values() for l in v if l["kind"] == "ground" and l.get("region")
    )
    n_ground = sum(1 for v in locs.values() for l in v if l["kind"] == "ground")
    withloc = sum(1 for r in items["items"] if r["locations"])
    print(f"ground items resolved {n_ground}  by region {dict(byregion)}")
    print(f"  mechanisms {dict(stats)}")
    print(f"hidden {hidden}   mart lists {len(marts)}   gift sites {gifts}")
    print(f"items with >=1 location: {withloc}/{len(items['items'])}")

    fail = []
    if hidden != 304:
        fail.append(f"hidden {hidden} != 304")
    # Every region must contribute ground items, or a whole mechanism silently broke.
    for r in ("kanto", "johto", "hoenn"):
        if byregion.get(r, 0) == 0:
            fail.append(f"no ground items resolved for {r}")
    if fail:
        print("FAILED: " + "; ".join(fail))
    return 1 if fail else 0


if __name__ == "__main__":
    sys.exit(main())
