// Internal link and orphan check over the built site. Brief section 9 requires zero broken
// internal links and zero orphaned generated records, and the cross-cutting rules require it
// to run on every push.
//
// Only internal links are checked. External ones are not this tool's business and would make
// the build depend on someone else's uptime.

import { readFileSync, readdirSync, statSync, existsSync } from "node:fs";
import { join, relative } from "node:path";

const DIST = "dist";
const BASE = "/pkmn-world";

function walk(dir, out = []) {
  for (const name of readdirSync(dir)) {
    const p = join(dir, name);
    if (statSync(p).isDirectory()) walk(p, out);
    else out.push(p);
  }
  return out;
}

if (!existsSync(DIST)) {
  console.error(`${DIST}/ not found — run the build first.`);
  process.exit(1);
}

const files = walk(DIST);
const pages = files.filter((f) => f.endsWith(".html"));
const assets = new Set(
  files.map((f) => "/" + BASE.replace(/^\//, "") + "/" + relative(DIST, f)),
);

// A directory-format page is served at its directory path as well as .../index.html.
for (const p of pages) {
  if (p.endsWith("index.html")) {
    assets.add(
      "/" +
        BASE.replace(/^\//, "") +
        "/" +
        relative(DIST, p).replace(/index\.html$/, ""),
    );
  }
}

const HREF = /(?:href|src)="([^"#?]+)(?:[#?][^"]*)?"/g;
const broken = new Map();
let checked = 0;

for (const page of pages) {
  const html = readFileSync(page, "utf8");
  for (const m of html.matchAll(HREF)) {
    const target = m[1];
    if (!target.startsWith(BASE + "/")) continue; // external, or a bare anchor
    checked++;
    const norm =
      target.endsWith("/") || /\.[a-z0-9]+$/i.test(target)
        ? target
        : target + "/";
    if (!assets.has(norm) && !assets.has(norm.replace(/\/$/, ""))) {
      const key = norm;
      if (!broken.has(key)) broken.set(key, []);
      broken.get(key).push(relative(DIST, page));
    }
  }
}

console.log(`${pages.length} pages, ${checked} internal links checked`);

if (broken.size) {
  console.error(`\n${broken.size} broken internal target(s):`);
  for (const [target, from] of [...broken].slice(0, 25)) {
    console.error(
      `  ${target}\n      linked from ${from.slice(0, 3).join(", ")}${from.length > 3 ? ` (+${from.length - 3} more)` : ""}`,
    );
  }
  process.exit(1);
}

// Orphan check: every map in the manifest must have rendered a page.
const manifest = JSON.parse(
  readFileSync("data/manifest/map-manifest.json", "utf8"),
);
// MUST match slugOf() in src/Names.ts exactly. Note it deliberately does NOT split
// letter/digit the way titleOf() does -- MAP_ROUTE1 is the slug "route1", not "route-1".
const slug = (id) => id.replace(/^MAP_/, "").toLowerCase().replaceAll("_", "-");
const missing = manifest.maps.filter(
  (m) => !existsSync(join(DIST, "maps", slug(m.map_id), "index.html")),
);

if (missing.length) {
  console.error(
    `\n${missing.length} manifest entries with no page, e.g. ${missing
      .slice(0, 5)
      .map((m) => m.map_id)
      .join(", ")}`,
  );
  process.exit(1);
}

console.log(
  `${manifest.maps.length} manifest entries all have a page. No broken links, no orphans.`,
);
