// Sprites live in public/sprites/ and are NOT committed -- tools/sprites/Extract.py
// regenerates them from the pinned submodule, and CI runs it before the build (.gitignore,
// .github/workflows/Deploy.yml). A checkout that has not run the extractor must still build
// and read correctly, so every call site asks here and falls back to the text-only layout
// rather than emitting an <img> that resolves to a broken-image icon.
//
// The filename is computed, never looked up: every sprite is keyed on the id of the thing it
// depicts, minus its SPECIES_/ITEM_ prefix. Nothing has to be checked into the repo to join
// the two halves. Species art is per SPECIES, not per dex number, so this module never has to
// know which form is dex 386 -- callers pass the id that src/Species.ts picked.
//
// WHY A FILESYSTEM READ AND NOT A GENERATED MANIFEST (data/manifest/map-manifest.json is the
// house pattern, and this deliberately does not follow it):
//   - That manifest is COMMITTED while public/maps/*.png is gitignored, so it asserts an
//     image exists whether or not Render.py has run. Copying that here would assert 1,646
//     sprites exist on a checkout with an empty public/sprites/ and emit 1,646 broken-image
//     icons -- the one outcome the brief rules out.
//   - Gitignoring the manifest instead fails harder: the import cannot resolve at all on a
//     fresh checkout and the whole build dies.
//   - The manifest earns its keep for maps because it carries geometry (pixel/block sizes)
//     that cannot be derived from a filename. Sprites have no such data -- the path is pure
//     string work on the id -- so the only question left is "is the file there?", and a
//     directory read is the only thing that actually answers it.
//
// BUILD-TIME ONLY. This module is imported from .astro frontmatter, which Astro evaluates in
// Node during `astro build` and never bundles for the browser; the pages ship the resolved
// strings, not this code. It must never be imported from a client <script> or a `client:`
// component, which would put node:fs in a browser bundle.
import fs from "node:fs";
import path from "node:path";
import { url } from "./Url";

const ROOT = path.join(process.cwd(), "public", "sprites");

function present(kind: string) {
  try {
    return new Set(fs.readdirSync(path.join(ROOT, kind)));
  } catch {
    return new Set<string>();
  }
}
const HAVE = {
  pokemon: present("pokemon"),
  icons: present("icons"),
  items: present("items"),
};

function pick(kind: keyof typeof HAVE, file: string) {
  return HAVE[kind].has(file) ? url(`sprites/${kind}/${file}`) : null;
}

const slugOfId = (id: string, prefix: RegExp) =>
  id.replace(prefix, "").toLowerCase().replaceAll("_", "-");

/** ITEM_PREMIER_BALL -> premier-ball. Must match Extract.py's item_slug(). */
export const itemSlug = (id: string) => slugOfId(id, /^ITEM_/);

/** SPECIES_DEOXYS_NORMAL -> deoxys-normal. Must match Extract.py's species_slug(). */
export const speciesSlug = (id: string) => slugOfId(id, /^SPECIES_/);

/** 64x64 front pic for a species id, or null. */
export function frontSprite(id: string) {
  return pick("pokemon", `${speciesSlug(id)}.png`);
}

/** 32x32 party icon for a species id, or null. */
export function iconSprite(id: string) {
  return pick("icons", `${speciesSlug(id)}.png`);
}

/** 24x24 bag icon for an item id, or null. The 100 TMs and 8 HMs have no static icon in
 *  the source at all -- the game recolours one at runtime by move type -- so null is the
 *  normal answer for those, not a failure. */
export function itemSprite(id: string) {
  return pick("items", `${itemSlug(id)}.png`);
}
