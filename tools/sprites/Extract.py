"""Sprite extractor: species front pics, species icons and item icons -> public/sprites/.

Output is keyed on the id of the thing it depicts, so no lookup table is committed:
  public/sprites/pokemon/<slug>.png  64x64 front pic, one per ENABLED SPECIES
  public/sprites/icons/<slug>.png    32x32 party icon, one per enabled species
  public/sprites/items/<slug>.png    24x24 item icon
with slug = the id minus its SPECIES_/ITEM_ prefix, kebab-cased.

Species art is emitted per species and NOT per national dex number, which means this file
has no opinion about which of dex 386's four forms is "Deoxys". It used to: the same
base-form denylist was written out here, in src/pages/species/[slug].astro and again in
src/pages/species/index.astro, the three copies drifted, and dex 386 published Deoxys with
the Attack forme's sprite. The one authority is now `is_base_form` in species.json (see
tools/extract/Species.py), the pages ask for a sprite by the id they picked, and the extra
166 front pics cost ~1.7 MiB of gitignored output.

Nothing here guesses a filename. The chain is
  species_info.h   .frontPic/.iconSprite/.iconPalIndex  ->  symbol, palette slot
  graphics/pokemon.h   symbol -> "graphics/pokemon/<dir>/<file>.png"   (INCGFX)
and the same shape for items via graphics/items.h.  See docs/DATA-AUDIT.md and
tools/porymap/Render.py, which resolves tileset assets the same way and for the same
reason: the path is not derivable from the symbol.

THE #if TRAP.  graphics/pokemon.h declares each sprite twice --
    #if !P_GBA_STYLE_SPECIES_GFX  ... anim_front.png  #else ... anim_front_gba.png  #endif
-- and the GBA arm is second, so a regex that scans the whole file into a dict binds EVERY
species to the unused _gba file and still produces a green build with 596 wrong sprites.
At this pin P_GBA_STYLE_SPECIES_GFX and P_GBA_STYLE_SPECIES_ICONS are both FALSE, so only
the pre-#else arm is live.  `_live()` tracks the conditional stack, `_check_config()` fails
if either macro ever flips, and GUARD asserts three known-good bindings on every run.

Palettes come from the .pal text file, never from the PNG's embedded palette: the two drift
on 20 Gmax/Galar icons (Meowth-Gmax and Snorlax-Gmax badly) and on two front pics, and the
.pal is the file the game's own graphics pipeline compiles from.  Palette index 0 is the
GBA's transparent slot and is forced to alpha 0 -- the RGB stored there is real colour data
in some files and would render as a solid box.
"""

import os, re, sys, json, hashlib, shutil, tempfile
import numpy as np
from PIL import Image

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "extract"))
import Common as C
import Species
from Species import Preprocessed, blocks, fields, num, resolve

OUTDIR = os.path.join(C.ROOT, "public", "sprites")
KINDS = ("pokemon", "icons", "items")

# Resolved from include/config/pokemon.h on every run by _check_config(); the whole binding
# direction below depends on all three being FALSE. Footprints are not extracted, but they
# share the file and the same double declaration, so leaving them ambiguous would trip
# _bindings()' own conflict check.
GBA = {
    "P_GBA_STYLE_SPECIES_GFX": False,
    "P_GBA_STYLE_SPECIES_ICONS": False,
    "P_GBA_STYLE_SPECIES_FOOTPRINTS": False,
}

# The regression this file exists to prevent. A #if-blind scan resolves all three to the
# _gba variant; the Venusaur entry also pins the base/form filename split (anim_front.png
# in a species directory, front.png in a nested form directory).
GUARD = {
    "gMonFrontPic_Bulbasaur": "graphics/pokemon/bulbasaur/anim_front.png",
    "gMonIcon_Bulbasaur": "graphics/pokemon/bulbasaur/icon.png",
    "gMonFrontPic_VenusaurMega": "graphics/pokemon/venusaur/mega/front.png",
}


# --- config ------------------------------------------------------------------


def _check_config():
    t = C.read("include", "config", "pokemon.h")
    for macro, want_false in GBA.items():
        m = re.search(r"^#define\s+%s\s+(\w+)" % macro, t, re.M)
        if not m:
            raise SystemExit("%s not found in include/config/pokemon.h" % macro)
        if (m.group(1) == "FALSE") != (not want_false):
            raise SystemExit(
                "%s is now %s. Every path in graphics/pokemon.h flips to the other #if arm; "
                "update GBA and GUARD before re-running." % (macro, m.group(1))
            )


# --- source bindings ---------------------------------------------------------

_BIND = re.compile(r'(\w+)\s*\[\s*\]\s*=\s*INC(?:BIN|GFX)_(?:U\d+|COMP)\s*\(\s*"([^"]+)"')
_IFDEF = re.compile(r"#if\s+(!?)\s*(\w+)\s*(?://.*)?$")


def _live(text):
    """The lines of `text` whose enclosing #if stack is live under the resolved config.

    Only the two P_GBA_STYLE_* conditionals are evaluated. Every other guard (P_FAMILY_*,
    P_FOOTPRINTS, OW_*, P_GENDER_DIFFERENCES) keeps both arms, which is safe because the
    symbols looked up here come from species_info and do not vary by those macros -- and
    _bindings() fails loudly if that ever stops being true.
    """
    out, stack = [], []  # stack entries: (condition was resolved, this arm is live)
    for line in text.split("\n"):
        s = line.lstrip()
        if s.startswith("#if"):
            m = _IFDEF.match(s)
            if m and m.group(2) in GBA:
                v = GBA[m.group(2)]
                stack.append((True, (not v) if m.group(1) else v))
            else:
                stack.append((False, True))
        elif s.startswith("#elif"):
            if stack:
                stack[-1] = (False, True)
        elif s.startswith("#else"):
            if stack:
                resolved, live = stack[-1]
                stack[-1] = (resolved, (not live) if resolved else True)
        elif s.startswith("#endif"):
            if stack:
                stack.pop()
        elif all(live for _, live in stack):
            out.append(line)
    return "\n".join(out)


def _bindings(*parts):
    """symbol -> repo-relative asset path, from the live arms only."""
    out = {}
    for m in _BIND.finditer(_live(C.read(*parts))):
        sym, path = m.group(1), m.group(2)
        if out.setdefault(sym, path) != path:
            raise SystemExit(
                "%s binds to two live paths (%s, %s) in %s -- an unresolved #if is keeping "
                "both arms; teach _live() about that macro." % (sym, out[sym], path, "/".join(parts))
            )
    return out


def resolve_path(sym, table, what):
    p = table.get(sym)
    if not p:
        raise SystemExit("%s: no live INCGFX binding for %s" % (what, sym))
    full = C.g(*p.split("/"))
    if not os.path.isfile(full):
        raise SystemExit("%s: %s binds to %s, which does not exist" % (what, sym, p))
    return full


# --- pixels ------------------------------------------------------------------


def load_pal(path):
    """JASC-PAL. Line 3 is the entry count; some form palettes declare fewer than 16."""
    lines = [l.strip() for l in open(path) if l.strip()]
    n = int(lines[2])
    return np.array([[int(x) for x in l.split()] for l in lines[3 : 3 + n]], dtype=np.uint8)


def load_indices(path):
    """4bpp indexed PNG -> (h, w) uint8 of palette indices. Same handling as
    tools/porymap/Render.py:load_tiles -- 8bpp sheets carry the index in the low nibble."""
    im = Image.open(path)
    if im.mode != "P":
        raise SystemExit("%s: expected an indexed PNG, got mode %s" % (path, im.mode))
    a = np.array(im, dtype=np.uint8)
    return a % 16 if a.max() > 15 else a


def emit(png, pal_path, out, frame=None):
    """Recolour `png` from `pal_path` and write RGBA, index 0 transparent.

    `frame` is the square edge to take from the top of a vertically stacked sheet; the
    second frame is the animation pose and is never what a page wants. 170 of the 596 front
    pics are single-frame already (all Megas, all Gmax, and a good number of base forms),
    so the crop keys on the actual image height rather than a per-file assumption.
    """
    idx = load_indices(png)
    if frame:
        h, w = idx.shape
        if w != frame or h not in (frame, frame * 2):
            raise SystemExit("%s: expected %dx%d or %dx%d, got %dx%d" % (png, frame, frame, frame, frame * 2, w, h))
        idx = idx[:frame]
    pal = load_pal(pal_path)
    if idx.max() >= len(pal):
        raise SystemExit("%s: index %d is past the %d-entry palette %s" % (png, idx.max(), len(pal), pal_path))
    rgba = np.zeros(idx.shape + (4,), dtype=np.uint8)
    mask = idx != 0  # index 0 is the GBA's transparent slot, whatever RGB sits in it
    rgba[..., :3][mask] = pal[idx[mask]]
    rgba[..., 3][mask] = 255
    Image.fromarray(rgba, "RGBA").save(out)
    return os.path.getsize(out)


# --- species -----------------------------------------------------------------


def species_slug(species_id):
    return species_id[len("SPECIES_"):].lower().replace("_", "-")


def species_rows():
    """(slug, front png, front pal, icon png, icon pal) for every enabled species."""
    gfx = _bindings("src", "data", "graphics", "pokemon.h")
    for sym, want in GUARD.items():
        if gfx.get(sym) != want:
            raise SystemExit(
                "%s -> %s, expected %s. The #if-blind bug is back: the _gba arm is declared "
                "second and wins in a flat dict." % (sym, gfx.get(sym), want)
            )

    pp = Preprocessed(Species.cpp("src/data/pokemon/species_info.h",
                                  extra_includes=["metaprogram.h", Species._famforce()]))
    # All three or nothing: an .iconSprite without an .iconPalIndex would otherwise fall back
    # to palette 0 and recolour the whole sprite wrong without failing. Entries missing any of
    # the three are dropped here and become an error below if they are enabled --
    # SPECIES_STARAPTOR_MEGA has its icon fields commented out and is disabled. All 596
    # enabled species resolve all three at this pin.
    info = {}
    for name, body, _ in blocks(pp.text, "SPECIES"):
        f = fields(body)
        got = [f.get(k, "").rstrip(",") for k in ("frontPic", "iconSprite", "iconPalIndex")]
        if all(got):
            info[name] = tuple(got)

    with open(os.path.join(C.OUT, "species.json"), encoding="utf-8") as f:
        enabled = [s for s in json.load(f)["species"] if s["enabled"]]

    for s in sorted(enabled, key=lambda s: s["id"]):
        sid = s["id"]
        if sid not in info:
            raise SystemExit("%s: no .frontPic/.iconSprite in species_info.h" % sid)
        front_sym, icon_sym, pal_expr = info[sid]
        front = resolve_path(front_sym, gfx, sid)
        icon = resolve_path(icon_sym, gfx, sid)
        # 27 Unown forms and dudunsparce/three_segment have no normal.pal of their own.
        pal = os.path.join(os.path.dirname(front), "normal.pal")
        if not os.path.isfile(pal):
            pal = os.path.join(os.path.dirname(os.path.dirname(front)), "normal.pal")
            if not os.path.isfile(pal):
                raise SystemExit("%s: no normal.pal beside or above %s" % (sid, front))
        # .iconPalIndex is a plain int, a ternary on P_GBA_STYLE_SPECIES_ICONS, or a macro
        # parameter -- cpp has already substituted the last, resolve() collapses the ternary.
        ipal = C.g("graphics", "pokemon", "icon_palettes", "pal%d.pal" % num(resolve(pal_expr)))
        if not os.path.isfile(ipal):
            raise SystemExit("%s: icon palette %s does not exist" % (sid, ipal))
        yield species_slug(sid), front, pal, icon, ipal


# --- items -------------------------------------------------------------------

# The 50 TMs, the 50 numbered TMs and the 8 HMs carry no .iconPic at all: their icon is
# recoloured at runtime from the move's type, so there is no static file to extract. That is
# the ONLY legitimate miss, and it is asserted rather than assumed -- anything else without
# an icon is an extractor failure.
NO_ICON = re.compile(r"^ITEM_(TM\d+|TM_\w+|HM_\w+)$")


def item_slug(item_id):
    return item_id[len("ITEM_"):].lower().replace("_", "-")


def item_rows():
    gfx = _bindings("src", "data", "graphics", "items.h")
    pp = Preprocessed(Species.cpp("src/data/items.h"))
    skipped = []
    for name, body, _ in blocks(pp.text, "ITEM"):
        f = fields(body)
        if "iconPic" not in f:
            if not NO_ICON.match(name):
                raise SystemExit("%s has no .iconPic and is not a TM/HM" % name)
            skipped.append(name)
            continue
        png = resolve_path(f["iconPic"].rstrip(","), gfx, name)
        pal = resolve_path(f["iconPalette"].rstrip(","), gfx, name)
        yield item_slug(name), png, pal
    if len(skipped) != 108:
        raise SystemExit("expected 108 icon-less TM/HM items, got %d" % len(skipped))


# --- run ---------------------------------------------------------------------


def build(outdir):
    _check_config()
    for k in KINDS:
        os.makedirs(os.path.join(outdir, k), exist_ok=True)
    written, total = {k: set() for k in KINDS}, 0

    for slug, front, fpal, icon, ipal in species_rows():
        if slug + ".png" in written["pokemon"]:
            raise SystemExit("species slug collision: %s" % slug)
        total += emit(front, fpal, os.path.join(outdir, "pokemon", slug + ".png"), frame=64)
        total += emit(icon, ipal, os.path.join(outdir, "icons", slug + ".png"), frame=32)
        written["pokemon"].add(slug + ".png")
        written["icons"].add(slug + ".png")

    seen = set()
    for slug, png, pal in item_rows():
        if slug in seen:
            raise SystemExit("item slug collision: %s" % slug)
        seen.add(slug)
        total += emit(png, pal, os.path.join(outdir, "items", slug + ".png"))
        written["items"].add(slug + ".png")

    # The output is a pure function of the pin, so a file left over from an older one is a
    # stale sprite on a page, not a harmless orphan.
    stale = 0
    for k in KINDS:
        d = os.path.join(outdir, k)
        for f in os.listdir(d):
            if f.endswith(".png") and f not in written[k]:
                os.remove(os.path.join(d, f))
                stale += 1

    print("sprites: %d front pics, %d icons, %d item icons -> %s (%.1f KB%s)" % (
        len(written["pokemon"]), len(written["icons"]), len(written["items"]),
        os.path.relpath(outdir, C.ROOT), total / 1024.0,
        ", %d stale removed" % stale if stale else ""))
    return sum(len(v) for v in written.values())


def digest(outdir):
    h = hashlib.sha256()
    for k in KINDS:
        d = os.path.join(outdir, k)
        for f in sorted(os.listdir(d)):
            h.update(f.encode())
            with open(os.path.join(d, f), "rb") as fh:
                h.update(fh.read())
    return h.hexdigest()


def main():
    args = sys.argv[1:]
    if "--check-determinism" in args:
        digests = []
        for _ in range(2):
            d = tempfile.mkdtemp(prefix="sprites")
            build(d)
            digests.append(digest(d))
            shutil.rmtree(d)
        print("determinism: %s" % ("OK " + digests[0][:16] if digests[0] == digests[1] else "FAILED"))
        if digests[0] != digests[1]:
            return 1
        args = [a for a in args if a != "--check-determinism"]
    build(args[0] if args else OUTDIR)
    return 0


if __name__ == "__main__":
    sys.exit(main())
