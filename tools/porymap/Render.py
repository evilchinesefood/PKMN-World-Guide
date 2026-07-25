"""Map image renderer. Replaces Porymap, which cannot render this project at all --
see docs/DECISIONS.md 3 and docs/DATA-AUDIT.md 0.3.

Reference implementation is Porymap's own src/core/maplayout.cpp (Layout::render)
and src/ui/imageproviders.cpp (getMetatileImage).

Output is 1:1 at 16px per block, one PNG per LIVE layout (966 of 1040 defined),
which covers all 1195 map pages because 49 layouts are shared by 277 maps.
"""

import os, sys, re, json, hashlib, functools
import numpy as np
from PIL import Image

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "extract"))
import Common as C

OUTDIR = os.path.join(C.ROOT, "public", "maps")

# The three coexisting regimes. Selected per layout by layouts.json `layout_version`.
# tiles/metatiles/pals come from GetNum*InPrimary (src/fieldmap.c:429-441), which keys
# on (isFrlg || isJohto). Attribute width keys on isFrlg ALONE (ExtractMetatileAttribute,
# src/fieldmap.c:492) -- which is why johto is 640-split but 2-byte.
REGIME = {
    "emerald": dict(tiles=512, metatiles=512, pals=6, attr=2),
    "frlg": dict(tiles=640, metatiles=640, pals=7, attr=4),
    "johto": dict(tiles=640, metatiles=640, pals=7, attr=2),
}
PALS_TOTAL = 13

# layerType -> which quadrant group draws on each of the 3 layers.
# 8 tiles are stored but 12 draws happen; the missing 4 come from here.
# 0=tiles 0-3, 1=tiles 4-7, None=nothing.
LAYERS = {0: (None, 0, 1), 1: (0, 1, None), 2: (0, None, 1)}


# Asset paths come from the source, never from guessing directory names. The mapping is
# not derivable from the symbol: gTileset_SecretBaseRedCave draws its tiles+palettes from
# secondary/secret_base/red_cave/ but SHARES gMetatiles_SecretBaseSecondary from
# secondary/secret_base/. Directory guessing cannot express that, so parse the chain:
#   headers.h   gTileset_X -> .tiles/.palettes/.metatiles/.metatileAttributes symbols
#   graphics.h  tiles symbol -> tiles.png,  palettes symbol -> [NN.pal, ...]
#   metatiles.h metatile symbols -> metatiles.bin / metatile_attributes.bin

_FIELD = re.compile(r"\.(\w+)\s*=\s*(\w+)")
_INC = re.compile(r'INC(?:BIN|GFX)_U\d+\("([^"]+)"')


@functools.lru_cache(maxsize=1)
def _headers():
    txt = C.read("src", "data", "tilesets", "headers.h")
    out = {}
    for blk in re.finditer(r"struct Tileset (gTileset_\w+)\s*=\s*\{(.*?)\};", txt, re.S):
        out[blk.group(1)] = dict(_FIELD.findall(blk.group(2)))
    return out


@functools.lru_cache(maxsize=1)
def _assets():
    """symbol -> list of repo-relative paths. Most live in src/data/tilesets/, but the
    stock Emerald primaries (gTilesetTiles_General and friends) sit in src/graphics.c."""
    out = {}
    srcs = [("src", "data", "tilesets", "graphics.h"), ("src", "data", "tilesets", "metatiles.h"), ("src", "graphics.c")]
    for parts in srcs:
        txt = C.read(*parts)
        for m in re.finditer(r"(\w+)\s*\[\s*\]\s*(?:\[16\]\s*)?=\s*(\{.*?\}|INC\w+\([^;]*?\));", txt, re.S):
            paths = _INC.findall(m.group(2))
            if paths:
                out[m.group(1)] = paths
        for m in re.finditer(r"(\w+)\s*\[\s*\]\s*\[\s*16\s*\]\s*=\s*\{(.*?)\};", txt, re.S):
            paths = _INC.findall(m.group(2))
            if paths:
                out[m.group(1)] = paths
    return out


def asset(sym, field):
    h = _headers().get(sym)
    if not h or field not in h:
        raise KeyError(f"{sym}: no .{field} in headers.h")
    a = _assets().get(h[field])
    if not a:
        raise KeyError(f"{sym}.{field} -> {h[field]}: no path binding")
    return a


def load_pal(path):
    lines = [l.strip() for l in open(path) if l.strip()]
    rgb = [tuple(int(x) for x in l.split()) for l in lines[3:19]]
    return np.array(rgb, dtype=np.uint8)


def load_tiles(path):
    """4bpp indexed sheet, 128px wide, 16 tiles/row -> (n,8,8) uint8 of palette indices."""
    im = Image.open(path)
    a = np.array(im.convert("P") if im.mode != "P" else im, dtype=np.uint8)
    if im.mode != "P" or a.max() > 15:
        a = a % 16  # 8bpp sheets carry the index in the low nibble
    h, w = a.shape
    rows, cols = h // 8, w // 8
    a = a.reshape(rows, 8, cols, 8).transpose(0, 2, 1, 3).reshape(rows * cols, 8, 8)
    return a


class Tileset:
    def __init__(self, sym):
        self.sym = sym
        self.paths = {f: asset(sym, f) for f in ("tiles", "palettes", "metatiles", "metatileAttributes")}
        self.tiles = load_tiles(C.g(*self.paths["tiles"][0].split("/")))
        self.meta = np.fromfile(C.g(*self.paths["metatiles"][0].split("/")), dtype="<u2")
        with open(C.g(*self.paths["metatileAttributes"][0].split("/")), "rb") as f:
            self.attr_raw = f.read()
        # Palette files are named by their GLOBAL index -- .../palettes/07.pal IS palette 7.
        self.pals = {}
        for p in self.paths["palettes"]:
            self.pals[int(os.path.basename(p)[:2])] = load_pal(C.g(*p.split("/")))

    def attrs(self, width):
        dt = "<u2" if width == 2 else "<u4"
        return np.frombuffer(self.attr_raw, dtype=dt)


_TS = {}


def tileset(sym):
    if sym not in _TS:
        _TS[sym] = Tileset(sym)
    return _TS[sym]


class Renderer:
    """One (primary, secondary, layout_version) combination."""

    def __init__(self, prim, sec, version):
        self.r = REGIME[version]
        self.p, self.s = tileset(prim), tileset(sec)
        self.pa = self.p.attrs(self.r["attr"])
        self.sa = self.s.attrs(self.r["attr"])
        self.cache = {}

    def palette(self, i):
        # Global index: primary owns [0, pals), secondary owns [pals, PALS_TOTAL) and its
        # files are named by the GLOBAL index -- secondary/x/palettes/07.pal IS palette 7.
        src = self.p if i < self.r["pals"] else self.s
        return src.pals.get(i, self.p.pals.get(i))

    def layer_type(self, mid):
        n = self.r["metatiles"]
        a, i = (self.pa, mid) if mid < n else (self.sa, mid - n)
        if i >= len(a):
            return 0
        v = int(a[i])
        return (v & 0xF000) >> 12 if self.r["attr"] == 2 else (v & 0x60000000) >> 29

    def metatile(self, mid):
        if mid in self.cache:
            return self.cache[mid]
        n = self.r["metatiles"]
        ts, idx = (self.p, mid) if mid < n else (self.s, mid - n)
        img = np.zeros((16, 16, 4), dtype=np.uint8)
        base = idx * 8
        if base + 8 <= len(ts.meta):
            words = ts.meta[base : base + 8]
            for layer, group in enumerate(LAYERS.get(self.layer_type(mid), LAYERS[0])):
                if group is None:
                    continue
                for q in range(4):
                    self._draw(img, int(words[group * 4 + q]), (q % 2) * 8, (q // 2) * 8)
        self.cache[mid] = img
        return img

    def _draw(self, img, word, x, y):
        tid = word & 0x03FF
        nt = self.r["tiles"]
        src, ti = (self.p, tid) if tid < nt else (self.s, tid - nt)
        if ti >= len(src.tiles):
            return
        t = src.tiles[ti]
        if word & 0x0400:
            t = t[:, ::-1]
        if word & 0x0800:
            t = t[::-1, :]
        pal = self.palette((word & 0xF000) >> 12)
        if pal is None:
            return
        mask = t != 0  # index 0 is always fully transparent
        if not mask.any():
            return
        dst = img[y : y + 8, x : x + 8]
        dst[..., :3][mask] = pal[t[mask]]
        dst[..., 3][mask] = 255


def render_layout(lay):
    blocks = np.fromfile(C.g(*lay["blockdata_filepath"].split("/")), dtype="<u2")
    w, h = lay["width"], lay["height"]
    if len(blocks) < w * h:
        raise ValueError(f"{lay['id']}: blockdata {len(blocks)} < {w*h}")
    r = Renderer(lay["primary_tileset"], lay["secondary_tileset"], lay["layout_version"])
    out = np.zeros((h * 16, w * 16, 4), dtype=np.uint8)
    for i in range(w * h):
        mt = r.metatile(int(blocks[i]) & 0x03FF)
        y, x = (i // w) * 16, (i % w) * 16
        out[y : y + 16, x : x + 16] = mt
    return Image.fromarray(out, "RGBA")


def content_hash(lay):
    """Hash of the INPUTS, not the PNG -- stays stable across encoder changes."""
    hsh = hashlib.sha256()
    with open(C.g(*lay["blockdata_filepath"].split("/")), "rb") as f:
        hsh.update(f.read())
    for sym in (lay["primary_tileset"], lay["secondary_tileset"]):
        ts = tileset(sym)
        for field in ("tiles", "metatiles", "metatileAttributes", "palettes"):
            for p in ts.paths[field]:
                with open(C.g(*p.split("/")), "rb") as f:
                    hsh.update(f.read())
    hsh.update(lay["layout_version"].encode())
    return "sha256:" + hsh.hexdigest()


def main():
    only = sys.argv[1] if len(sys.argv) > 1 else None
    os.makedirs(OUTDIR, exist_ok=True)
    maps, lays = C.maps(), C.layouts()
    live = C.live_layout_ids()
    todo = sorted(live if not only else {m["layout"] for m in maps.values() if m["id"] == only})
    done, failed = {}, []
    for n, lid in enumerate(todo, 1):
        lay = lays[lid]
        try:
            im = render_layout(lay)
            assert im.width == lay["width"] * 16 and im.height == lay["height"] * 16
            im.save(os.path.join(OUTDIR, lid + ".png"))
            done[lid] = content_hash(lay)
        except Exception as e:
            failed.append((lid, str(e)))
        if n % 100 == 0:
            print(f"  {n}/{len(todo)}", flush=True)

    entries = []
    for mid, m in sorted(maps.items()):
        lid = m.get("layout")
        if lid not in done:
            continue
        lay = lays[lid]
        entries.append(
            {
                "map_id": mid,
                "layout_id": lid,
                "region": C.region_of_map(m),
                "block_width": lay["width"],
                "block_height": lay["height"],
                "pixel_width": lay["width"] * 16,
                "pixel_height": lay["height"] * 16,
                "image": f"maps/{lid}.png",
                "content_hash": done[lid],
            }
        )
    C.write(
        "map-manifest.json",
        {
            "generator": {"name": "tools/porymap/Render.py", "version": "1.0.0"},
            "game": C.header(),
            "maps": entries,
        },
        C.MANIFEST,
    )
    print(f"rendered {len(done)}/{len(todo)} layouts -> {len(entries)} map entries")
    if failed:
        print(f"FAILED {len(failed)}:")
        for lid, e in failed[:10]:
            print(f"  {lid}: {e}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
