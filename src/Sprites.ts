// Sprites live in public/sprites/ and are NOT committed -- tools/sprites/Extract.py
// regenerates them from the pinned submodule, and CI runs it before the build (.gitignore,
// .github/workflows/Deploy.yml). A checkout that has not run the extractor must still build
// and read correctly, so every call site asks here and falls back to the text-only layout
// rather than emitting an <img> that resolves to a broken-image icon.
//
// The filename is computed, never looked up: species art is keyed on the national dex number
// the species URLs already use, items on their id minus the ITEM_ prefix. Nothing has to be
// checked into the repo to join the two halves.
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

/** ITEM_PREMIER_BALL -> premier-ball. Must match Extract.py's item_slug(). */
export function itemSlug(id: string) {
  return id
    .replace(/^ITEM_/, "")
    .toLowerCase()
    .replaceAll("_", "-");
}

/** 64x64 front pic for a dex slug ("006"), or null. */
export function frontSprite(dexSlug: string) {
  return pick("pokemon", `${dexSlug}.png`);
}

/** 32x32 party icon for a dex slug, or null. */
export function iconSprite(dexSlug: string) {
  return pick("icons", `${dexSlug}.png`);
}

/** 24x24 bag icon for an item id, or null. The 100 TMs and 8 HMs have no static icon in
 *  the source at all -- the game recolours one at runtime by move type -- so null is the
 *  normal answer for those, not a failure. */
export function itemSprite(id: string) {
  return pick("items", `${itemSlug(id)}.png`);
}
