"""Proves the M1 coordinate math by drawing markers onto the rendered map at the exact
pixel positions the site uses, so they can be eyeballed against real map features.

A warp marker MUST land on a door or stairs -- those are baked into the map image, so
if the maths is off by even one block it is obvious. Also asserts the invariants that
cannot be seen: image size, marker bounds, and manifest agreement.
"""

import json, os, sys
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "extract"))
import Common as C

COLOR = {
    "item": (242, 182, 50),
    "hidden_item": (154, 110, 240),
    "trainer": (226, 85, 61),
    "warp": (53, 167, 216),
    "sign": (127, 138, 153),
}


def markers_for(m):
    out = []
    for o in m["object_events"]:
        if o.get("graphics_id") == "OBJ_EVENT_GFX_ITEM_BALL":
            out.append(("item", o["coord"]))
        elif o.get("trainer_type") in ("TRAINER_TYPE_NORMAL", "TRAINER_TYPE_BURIED"):
            out.append(("trainer", o["coord"]))
    out += [("hidden_item", h["coord"]) for h in m["hidden_items"]]
    out += [("warp", w["coord"]) for w in m["warps"]]
    out += [("sign", s["coord"]) for s in m["signs"]]
    return out


def check(map_id, manifest, maps, draw_to=None):
    m = maps[map_id]
    img = manifest[map_id]
    png = os.path.join(C.ROOT, "public", img["image"])
    im = Image.open(png).convert("RGBA")

    errs = []
    if (im.width, im.height) != (img["pixel_width"], img["pixel_height"]):
        errs.append(f"png {im.size} != manifest {(img['pixel_width'], img['pixel_height'])}")
    if img["pixel_width"] != img["block_width"] * 16:
        errs.append("pixel_width != block_width*16")

    mk = markers_for(m)
    for kind, c in mk:
        if not (0 <= c["x"] < img["block_width"] and 0 <= c["y"] < img["block_height"]):
            errs.append(f"{kind} at ({c['x']},{c['y']}) outside {img['block_width']}x{img['block_height']}")

    if draw_to:
        d = ImageDraw.Draw(im)
        for kind, c in mk:
            # The site places a marker at the CENTRE of the block: (x*16+8, y*16+8).
            px, py = c["x"] * 16 + 8, c["y"] * 16 + 8
            r, col = 5, COLOR[kind]
            d.ellipse([px - r, py - r, px + r, py + r], fill=col + (235,), outline=(255, 255, 255, 255))
        im.save(draw_to)

    return mk, errs


def main():
    maps = {m["id"]: m for m in json.load(open(os.path.join(C.OUT, "maps.json")))["maps"]}
    manifest = {m["map_id"]: m for m in json.load(open(os.path.join(C.MANIFEST, "map-manifest.json")))["maps"]}

    targets = sys.argv[1:] or ["MAP_PALLET_TOWN", "MAP_ROUTE102", "MAP_NEW_BARK_TOWN"]
    outdir = os.environ.get("COORD_OUT", "/tmp")
    bad = 0
    for mid in targets:
        mk, errs = check(mid, manifest, maps, os.path.join(outdir, f"coords_{mid}.png"))
        kinds = {}
        for k, _ in mk:
            kinds[k] = kinds.get(k, 0) + 1
        print(f"{mid:26s} {len(mk):3d} markers {kinds}")
        for e in errs:
            print(f"    ERROR {e}")
            bad += 1

    # Whole-corpus pass. Out-of-bounds markers are GAME DATA anomalies, not extractor
    # bugs -- SSAqua_RoomNW authors two trainers at y=-5, and the six 1x1 UnusedContestHall
    # stubs inherit events from the full-size ContestHall. They are reported, not fatal,
    # because a marker drawn off-image silently vanishes on the site and someone should
    # know. Only the structural invariants below fail the build.
    n = 0
    off = []
    for mid, img in sorted(manifest.items()):
        for kind, c in markers_for(maps[mid]):
            n += 1
            if not (0 <= c["x"] < img["block_width"] and 0 <= c["y"] < img["block_height"]):
                off.append((mid, kind, c["x"], c["y"], img["block_width"], img["block_height"]))
    print(f"\nall maps: {n} markers")
    print(f"  off-image markers (game-data anomalies, not fatal): {len(off)}")
    for mid, kind, x, y, w, h in off:
        print(f"    {mid:46s} {kind:12s} ({x},{y}) in {w}x{h}")

    px = sum(
        1
        for i in manifest.values()
        if i["pixel_width"] != i["block_width"] * 16 or i["pixel_height"] != i["block_height"] * 16
    )
    print(f"manifest: {len(manifest)} entries, {px} with pixel != block*16")
    if bad or px:
        print("FAIL: structural invariant broken")
    return 1 if (bad or px) else 0


if __name__ == "__main__":
    sys.exit(main())
