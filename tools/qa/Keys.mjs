// The departure checklist's stored-tick keys, frozen against the built site.
//
// WHY THIS EXISTS, AND WHY tools/qa/Checklist.mjs CANNOT DO IT. A tick is stored in the reader's
// browser under a hash of the item's compiled sentence (decision 43), and `text()` in
// src/Checklist.ts strips tags but NOT entities -- so a sentence containing "&" hashes the
// literal string the markdown compiler chose, which today is "&#x26;". src/Features.ts already
// documents that the compiler spells "&" numerically. An Astro or remark upgrade that spells it
// "&amp;" instead, or that turns on smartypants and rewrites a quote or a dash, therefore
// SILENTLY REKEYS every checklist line containing one, and every tick a reader has stored on
// those lines is orphaned. Nothing renders differently. Nothing warns.
//
// The fixture cannot catch that, because it compiles through the same processor the site does:
// both sides of its "same sentence keys identically" assertion move together. This file compares
// what the site BUILT against a frozen literal, which is the only comparison a toolchain change
// cannot pass by moving both sides of it.
//
// It reads dist/ rather than compiling markdown, so what is checked is what ships. Run it after
// the build, beside tools/qa/Links.mjs.
//
//   node tools/qa/Keys.mjs           verify
//   node tools/qa/Keys.mjs --write   record chapters and sentences that are not yet recorded
//
// --write ONLY ADDS. It will not rewrite the key of a sentence already in the file, because that
// is exactly the orphaning this guard exists to catch, and blessing it must be a deliberate edit
// by a person who has read the failure below -- not a command someone runs to make CI green.

import { readFileSync, writeFileSync, existsSync, readdirSync } from "node:fs";
import { join } from "node:path";

const DIST = "dist/walkthrough";
const GOLDEN = "tools/qa/GoldenKeys.json";
const write = process.argv.includes("--write");

if (!existsSync(DIST)) {
  console.error(`${DIST}/ not found — run the build first.`);
  process.exit(1);
}

const NAMED = { amp: "&", lt: "<", gt: ">", quot: '"', apos: "'", nbsp: " " };
/** The sentence a reader sees. Entities are DECODED here on purpose: the decoded text is the
 *  stable identity of an item across a toolchain change, while the key is the thing under test.
 *  That is what lets a rekey be told apart from an author rewording the line. */
const plain = (h) =>
  h
    .replace(/<[^>]+>/g, "")
    .replace(/&#x([0-9a-f]+);/gi, (_, n) =>
      String.fromCodePoint(parseInt(n, 16)),
    )
    .replace(/&#(\d+);/g, (_, n) => String.fromCodePoint(Number(n)))
    .replace(/&([a-z]+);/gi, (all, n) => NAMED[n.toLowerCase()] ?? all)
    .replace(/\s+/g, " ")
    .trim();

// Every chapter's items, in document order. The slug is the directory, which is exactly the
// namespace the ticks are stored under: `pw-checked:<slug>`.
const built = {};
for (const slug of readdirSync(DIST)) {
  const page = join(DIST, slug, "index.html");
  if (!existsSync(page)) continue;
  const html = readFileSync(page, "utf8");
  const items = [
    ...html.matchAll(
      /data-check="([^"]+)"[\s\S]*?<span class="lbl">([\s\S]*?)<\/span>/g,
    ),
  ].map((m) => ({ key: m[1], text: plain(m[2]) }));
  if (items.length) built[slug] = items;
}

const golden = existsSync(GOLDEN)
  ? JSON.parse(readFileSync(GOLDEN, "utf8"))
  : {};

// Sentence -> the keys it holds. A list, because a chapter may legitimately repeat a sentence
// and the later copies carry `~2`, `~3` (decision 48).
const byText = (rows) => {
  const m = new Map();
  for (const r of rows) m.set(r.text, [...(m.get(r.text) ?? []), r.key]);
  return m;
};

/** The same sentence with its TYPOGRAPHY folded away -- curly quotes, dashes and ellipses back
 *  to the ASCII an author actually typed. Two sentences that differ only here are the same words
 *  to a reader and a different key to the hash, which is precisely what a markdown processor
 *  turning smartypants on or off does to a whole site at once. Without this fold that change
 *  looks like every author having reworded every line on the same day. */
const loose = (s) =>
  s
    .replace(/[‘’‛]/g, "'")
    .replace(/[“”]/g, '"')
    .replace(/[–—]/g, "-")
    .replace(/…/g, "...")
    .replace(/\s+/g, " ")
    .trim();

const rekeyed = []; // recorded sentence still on the page, under a different key
const gone = []; // recorded sentence no longer on the page at all
const fresh = {}; // on the page, never recorded

for (const [slug, rows] of Object.entries(golden)) {
  const now = byText(built[slug] ?? []);
  const byLoose = new Map([...now].map(([t, k]) => [loose(t), [t, k]]));
  for (const [text, keys] of byText(rows)) {
    let live = now.get(text) ?? [];
    let note = "";
    if (!live.length) {
      // Same words, different typography: a processor change, not an author edit.
      const near = byLoose.get(loose(text));
      if (!near) {
        gone.push({ slug, text, keys });
        continue;
      }
      live = near[1];
      note = ` — the sentence now reads "${near[0]}", which is the same words with different typography`;
    }
    for (const k of keys)
      if (!live.includes(k))
        rekeyed.push({ slug, text, was: k, now: live, note });
  }
}
for (const [slug, rows] of Object.entries(built)) {
  const had = byText(golden[slug] ?? []);
  const add = rows.filter((r) => !(had.get(r.text) ?? []).includes(r.key));
  if (add.length) fresh[slug] = add;
}

const show = (r) => `      ${r.slug} · "${r.text}"`;

if (rekeyed.length) {
  console.error(
    `\n${rekeyed.length} checklist sentence(s) STILL ON THE PAGE but now hash to a different key.\n` +
      `\n` +
      `      THIS ORPHANS EVERY TICK READERS HAVE ALREADY STORED ON THESE LINES. Nobody edited\n` +
      `      the words -- the sentence is character-for-character what it was -- so the change\n` +
      `      came from the markdown processor: an Astro or remark upgrade spelling an entity\n` +
      `      differently, or smartypants rewriting a quote or a dash. The page will render\n` +
      `      perfectly and every affected box will come back unticked.\n` +
      `\n` +
      `      THE FIX IS A DELIBERATE MIGRATION, NOT ACCEPTING THE NEW KEYS. Ticks live in\n` +
      `      localStorage under pw-checked:<chapter-slug>; nothing in the build can reach them.\n` +
      `      Either pin the processor back, or ship a one-off migration that rewrites the stored\n` +
      `      keys in the reader's browser before you update this file. See DECISIONS.md 43, 51.\n` +
      `      Running --write will NOT do this for you, by design.\n`,
  );
  for (const r of rekeyed)
    console.error(
      `      ${r.slug} · "${r.text}"${r.note}\n        was ${r.was} → now ${r.now.join(", ")}`,
    );
}

if (gone.length) {
  console.error(
    `\n${gone.length} recorded checklist sentence(s) are no longer on the page.\n` +
      `      If an author reworded or removed these items, that is decision 43's accepted cost\n` +
      `      and the only thing to do is update ${GOLDEN} -- delete the stale lines and run\n` +
      `      --write to add the new ones. If nobody edited the chapter, treat it as the case\n` +
      `      above instead: something rewrote the sentence without an author asking.\n`,
  );
  for (const r of gone) console.error(show(r) + `  (${r.keys.join(", ")})`);
}

if (Object.keys(fresh).length) {
  const n = Object.values(fresh).flat().length;
  if (write) {
    for (const [slug, rows] of Object.entries(fresh))
      golden[slug] = [...(golden[slug] ?? []), ...rows];
    // Chapters in slug order so a diff stays readable as M5 adds 45-58 of them.
    const sorted = Object.fromEntries(
      Object.keys(golden)
        .sort()
        .map((k) => [k, golden[k]]),
    );
    writeFileSync(GOLDEN, JSON.stringify(sorted, null, 2) + "\n");
    console.log(`recorded ${n} new checklist key(s) in ${GOLDEN}`);
  } else {
    console.error(
      `\n${n} checklist key(s) on the built site are not recorded in ${GOLDEN}.\n` +
        `      These are not protected: if a toolchain change rekeys them later, nothing here\n` +
        `      will notice. No reader can have a tick stored under a key that has never shipped,\n` +
        `      so there is nothing to lose right now -- run:\n` +
        `\n        node tools/qa/Keys.mjs --write\n`,
    );
    for (const [slug, rows] of Object.entries(fresh))
      for (const r of rows)
        console.error(`      ${slug} · ${r.key} · "${r.text}"`);
  }
}

const bad =
  rekeyed.length +
  gone.length +
  (write ? 0 : Object.values(fresh).flat().length);
if (bad) {
  console.error(`\n${bad} problem(s). See above.`);
  process.exit(1);
}
const total = Object.values(golden).flat().length;
console.log(
  `${total} checklist key(s) across ${Object.keys(golden).length} chapter(s) unchanged.`,
);
