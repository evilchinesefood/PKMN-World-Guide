// The departure checklist's markdown surface, asserted rather than rediscovered.
//
// WHY THIS FILE EXISTS. This one small feature has produced five silent-failure shapes -- a
// nested sub-list, a loose list, duplicate keys, `- [x]`, and the `<p>` wrapper (decision 48).
// THREE OF THE FIVE WERE INVISIBLE ON THE PAGE and existed only because someone sat down and
// constructed the input. The failure signature is always the same: boxes render, and they do
// nothing. M5 writes 45-58 chapters against this code, so the point of the table below is the
// SPACE of shapes markdown can produce, not the bugs that have already been fixed -- a test
// that only covers those cannot catch shape six.
//
// Deliberately not a framework: no runner, no config, no new dependency. It compiles markdown
// through the same processor Astro uses, drives src/Checklist.ts over the result, prints a
// readable diff on failure and exits non-zero.
//
// Needs Node >= 22.18 for its type stripping, so it can import the .ts directly rather than
// keeping a second copy of the rules. CI pins node-version: 22.
//
// If astro.config.mjs ever gains `markdown:` options, mirror them in the processor below or
// this fixture stops testing what the site actually builds.

import { createMarkdownProcessor } from "@astrojs/markdown-remark";
import {
  checklist,
  checkSource,
  isTaskList,
  keyOf,
} from "../../src/Checklist.ts";

const proc = await createMarkdownProcessor({});
const compile = async (md) => (await proc.render(md)).code;

let failed = 0;
let ran = 0;
const ok = (name, cond, detail = "") => {
  ran++;
  if (cond) return true;
  failed++;
  console.error(`FAIL  ${name}${detail ? `\n      ${detail}` : ""}`);
  return false;
};
const eq = (name, actual, expected, hint = "") =>
  ok(
    name,
    JSON.stringify(actual) === JSON.stringify(expected),
    `expected ${JSON.stringify(expected)}\n      actual   ${JSON.stringify(actual)}${hint ? `\n      ${hint}` : ""}`,
  );

const keysIn = (h) => [...h.matchAll(/data-check="([^"]+)"/g)].map((m) => m[1]);
const labelsIn = (h) =>
  [...h.matchAll(/<span class="lbl">([\s\S]*?)<\/span>/g)].map((m) => m[1]);
// Each label's OWN content. Labels do not nest, so non-greedy to the first close is exact.
const labelBodies = (h) =>
  [...h.matchAll(/<label\b[^>]*>([\s\S]*?)<\/label>/g)].map((m) => m[1]);

// Tag balance the way a parser would see it: every close matches the innermost open.
function balanced(html) {
  const open = [];
  for (const m of html.matchAll(
    /<(\/?)(li|ul|ol|label|span|p)\b[^>]*?(\/?)>/g,
  )) {
    if (m[3] === "/") continue;
    if (m[1]) {
      if (open.pop() !== m[2]) return false;
    } else open.push(m[2]);
  }
  return open.length === 0;
}

// The one sentence that appears across shapes. Its key is the thing readers' stored ticks are
// filed under, so every shape that contains it must produce the same key.
const S = "Catch a Mankey on Route 22";

// The space of shapes markdown can produce for a checklist. `carries` marks the ones whose
// first item is S and must therefore key identically.
const SHAPES = [
  {
    name: "tight",
    carries: true,
    md: `- [ ] ${S}\n- [ ] The Town Map from Daisy\n`,
  },
  {
    name: "loose",
    carries: true,
    md: `- [ ] ${S}\n\n- [ ] The Town Map from Daisy\n`,
  },
  {
    name: "tight + nested notes",
    carries: true,
    md: `- [ ] ${S}\n  - it learns Low Kick at 8\n  - Fighting beats Rock\n- [ ] The Town Map from Daisy\n`,
  },
  {
    name: "loose + nested notes",
    carries: true,
    md: `- [ ] ${S}\n\n  - it learns Low Kick at 8\n  - Fighting beats Rock\n\n- [ ] The Town Map from Daisy\n`,
  },
  {
    name: "tight + nested task list",
    carries: true,
    md: `- [ ] ${S}\n  - [ ] buy five Poke Balls\n`,
  },
  {
    name: "tight parent + LOOSE nested task list",
    carries: true,
    md: `- [ ] ${S}\n  - [ ] buy five Poke Balls\n\n  - [ ] and a Potion\n`,
  },
  {
    name: "loose + trailing paragraph",
    carries: true,
    md: `- [ ] ${S}\n\n  Bring it with you.\n\n- [ ] The Town Map from Daisy\n`,
  },
  {
    name: "deep nesting (grandchild)",
    carries: true,
    md: `- [ ] ${S}\n  - child\n    - grandchild\n  - child two\n- [ ] Sibling\n`,
  },
  {
    name: "inline markup in the sentence",
    md: `- [ ] Catch a **Mankey** with a [link](https://x.test) and \`code\`\n- [ ] Plain\n`,
  },
  {
    name: "hard line break in the sentence",
    md: `- [ ] Catch a Mankey  \non Route 22\n- [ ] Plain\n`,
  },
  {
    name: "ordered task list",
    carries: true,
    md: `1. [ ] ${S}\n2. [ ] Second\n`,
  },
  {
    name: "mixed task and plain items",
    carries: true,
    md: `- [ ] ${S}\n- just a bullet, no box\n- [ ] Another task\n`,
  },
  {
    name: "duplicate sentences",
    carries: true,
    md: `- [ ] ${S}\n- [ ] Other\n- [ ] ${S}\n- [ ] ${S}\n`,
  },
  {
    name: "two separate checklists in one chunk",
    carries: true,
    md: `- [ ] ${S}\n- [ ] Other\n\nSome prose between them.\n\n- [ ] A second list\n- [ ] With two items\n`,
  },
  { name: "pre-checked item", md: `- [x] Already done\n- [ ] Not done\n` },
];

console.log("checklist fixture\n");

// ---------------------------------------------------------------------------------------
// 1. THE ONE THAT GUARDS READER DATA. Run first, because everything else is cosmetic beside
//    it. A tick is stored under a hash of the item's sentence, so if the same sentence keys
//    differently depending on how the author happened to lay the markdown out, then merely
//    reformatting a chapter -- adding a blank line, indenting a note -- silently wipes ticks
//    readers have already made. The site is live. This is not a style check.
// ---------------------------------------------------------------------------------------
const bare = keyOf(S);
for (const s of SHAPES.filter((s) => s.carries)) {
  const first = keysIn(checklist(await compile(s.md)).html)[0];
  ok(
    `key stability · ${s.name}`,
    first === bare,
    `"${S}" keys as ${first} in this shape but ${bare} elsewhere.\n` +
      `      STORED TICKS ARE AT RISK: readers' ticks are filed under the key, so a sentence\n` +
      `      that keys differently per markdown shape means reformatting a chapter silently\n` +
      `      clears boxes the reader already ticked. See docs/DECISIONS.md 43 and 48.`,
  );
}

// ---------------------------------------------------------------------------------------
// 2. Invariants every shape must hold, whatever it is.
// ---------------------------------------------------------------------------------------
for (const s of SHAPES) {
  const src = await compile(s.md);
  const { html } = checklist(src);

  ok(`balanced markup · ${s.name}`, balanced(html), html);
  ok(
    `no block element inside a <label> · ${s.name}`,
    labelBodies(html).every((c) => !/<(?:ul|ol|p|table|blockquote)\b/.test(c)),
    "a <label> takes phrasing content; a block inside one is invalid markup",
  );
  ok(
    `every compiled checkbox became a real control · ${s.name}`,
    !/type="checkbox"[^>]*\bdisabled/.test(html) &&
      keysIn(html).length === (src.match(/type="checkbox"/g) ?? []).length,
    `${keysIn(html).length} controls for ${(src.match(/type="checkbox"/g) ?? []).length} compiled boxes -- a leftover disabled box is a box that renders and does nothing`,
  );
  ok(
    `keys are unique within the list · ${s.name}`,
    new Set(keysIn(html)).size === keysIn(html).length,
    `${keysIn(html).join(", ")} -- a shared key makes a tick spread across items on reload`,
  );
  ok(
    `no label swallowed a sibling item · ${s.name}`,
    labelsIn(html).every((l) => !/<li\b/.test(l)),
  );

  // THE FOLD CONTRACT 45-58 CHAPTERS INHERIT. A task list is detected by the checkbox it
  // compiles to, and that detection is what keeps the checklist OUT of a fold. The rewrite
  // must not break it -- the <input> survives on purpose.
  const hasBoxes = /type="checkbox"/.test(src);
  ok(
    `fold rule detects the compiled task list · ${s.name}`,
    isTaskList(src) === hasBoxes,
  );
  ok(
    `fold rule still detects it AFTER the rewrite · ${s.name}`,
    isTaskList(html) === hasBoxes,
    "the rewrite dropped the checkbox input, so this section would now fold shut",
  );
}

// ---------------------------------------------------------------------------------------
// 3. Shape-specific behaviour worth pinning down.
// ---------------------------------------------------------------------------------------
const bySpec = Object.fromEntries(SHAPES.map((s) => [s.name, s.md]));
const run = async (name) => checklist(await compile(bySpec[name])).html;

const notes = await run("tight + nested notes");
eq(
  "nested notes: the label is the item's own sentence only",
  labelsIn(notes)[0],
  S,
  "a nested list folded into the parent's label also folds into its key",
);
ok(
  "nested notes: the note list stays inside the item, after the label",
  /<\/label><ul>\n<li>it learns Low Kick at 8<\/li>/.test(notes),
);

const looseNotes = await run("loose + nested notes");
eq("loose + nested notes: same label", labelsIn(looseNotes)[0], S);
ok(
  "loose: the <p> wrapper is gone, so loose and tight render alike",
  !/<li[^>]*><p>/.test(looseNotes),
);

const trailing = await run("loose + trailing paragraph");
ok(
  "trailing paragraph is kept as the label's sibling",
  /<\/label>\n<p>Bring it with you.<\/p>/.test(trailing),
);

const mixed = await run("mixed task and plain items");
ok(
  "a plain <li> beside task items keeps its own markup",
  /<li>just a bullet, no box<\/li>/.test(mixed),
);
eq("mixed: only the task items become controls", keysIn(mixed).length, 2);

const ordered = await run("ordered task list");
ok(
  "ordered task list stays an <ol>",
  /<ol class="contains-task-list">/.test(ordered),
);

const dup = await run("duplicate sentences");
eq(
  "duplicates: first keeps the bare key, later ones are suffixed in order",
  [keysIn(dup)[0], keysIn(dup)[2], keysIn(dup)[3]],
  [bare, `${bare}~2`, `${bare}~3`],
  "the first occurrence is the one that may already be ticked in a reader's browser",
);
eq(
  "duplicates: the repeated sentence is reported once, for the build warning",
  checklist(await compile(bySpec["duplicate sentences"])).repeated,
  [S],
);
eq(
  "a unique sentence never gains a suffix",
  checklist(await compile(bySpec["tight"])).repeated,
  [],
);

const two = await run("two separate checklists in one chunk");
eq(
  "two lists in one chunk: all four items are controls",
  keysIn(two).length,
  4,
);

// A list with no checkboxes must come through untouched.
const plain = await compile("- just a bullet\n- another\n");
eq(
  "a list with no checkboxes is left exactly as it came in",
  checklist(plain).html,
  plain,
);

// ---------------------------------------------------------------------------------------
// 4. Source-level checks -- the ones that need the author's markdown, not the compiled HTML.
// ---------------------------------------------------------------------------------------
const md = `---\ntitle: Test\n---\n\n## Before you leave\n\n- [ ] A normal item\n- [x] Already done\n* [X] Star bullet, capital X\n`;
const warns = checkSource(md, "content/kanto/Test.md");
eq("- [x] warns once per pre-checked item", warns.length, 2);
ok(
  "- [x] warning counts the frontmatter, so the line number is the file's",
  warns[0].startsWith("content/kanto/Test.md:8:") &&
    warns[1].startsWith("content/kanto/Test.md:9:"),
  warns.join("\n      "),
);
eq(
  "an unticked item does not warn",
  checkSource("- [ ] Normal\n", "x.md").length,
  0,
);
eq(
  "prose mentioning [x] does not warn",
  checkSource("- see the [x] column in the table\n", "x.md").length,
  0,
);
ok(
  "a pre-checked item still renders an EMPTY box (the checklist is the reader's)",
  !/checked/.test(await run("pre-checked item")),
  "decision 48: a checklist whose first act is to claim the reader has done something is a lie",
);

// ---------------------------------------------------------------------------------------
if (failed) {
  console.error(
    `\n${failed} of ${ran} assertions FAILED across ${SHAPES.length} markdown shapes.`,
  );
  process.exit(1);
}
console.log(`${SHAPES.length} markdown shapes, ${ran} assertions, all passed.`);
