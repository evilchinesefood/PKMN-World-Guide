// The chapter `sections:` schema, asserted rather than trusted.
//
// WHY THIS FILE EXISTS. The schema was deliberately designed so that authoring errors are
// DETECTABLE, and then nothing detected them: `src/Steps.ts` opens with "bad content degrades,
// it never throws", which is the right rule for a renderer and no rule at all for the author.
// A group of one renders as an ordinary step, a `choice` with no `choice_group` renders as an
// ordinary step, a mistyped `at:` drops the pin, and every one of those looks like a page that
// simply did not say what you meant. One chapter can be proofread. M5 writes 45-58 of them
// plus 24 boss pages and three leagues, all by hand, against a frozen contract -- so the
// contract needs a reader that is not a person.
//
// WHY NODE AND NOT tools/validate/ (which is Python). The rules being checked are not in this
// file: `stepsOf` below is the renderer's own module, so what this reports is what the page
// will actually do. A Python copy of the grouping rules would be a second implementation of
// the thing under test, and this repo has already paid that bill twice -- `slugOf()` drifting
// from its copy in Links.mjs produced 486 phantom orphans, and the base-form rule drifted
// across three copies until decision 29 deleted two of them. tools/validate/ checks the
// EXTRACTED data, which has no TypeScript to defer to; this checks hand-written content
// against code, so it defers to the code. Same reasoning as tools/qa/Checklist.mjs.
//
// Frontmatter is parsed with js-yaml because that is what @astrojs/markdown-remark parses it
// with, so this checker and the page are looking at the same object rather than at two
// readings of the same file.
//
// ERROR vs WARN. An ERROR is something the contract forbids AND the renderer swallows -- the
// two together are what makes it invisible. A WARN is well-defined behaviour that is almost
// certainly not what the author meant; it is loud but it does not fail the build, because
// being wrong about intent should not stop a chapter shipping.
//
// THE FIXTURE TABLE AT THE BOTTOM IS NOT OPTIONAL. Every rule here is proved to fire by a
// constructed chapter that breaks it, in the same run, because the failure mode of a checker
// is silence and silence is indistinguishable from success. tools/qa/Checklist.mjs learned
// this the hard way: its own assertion for shape six sat green because no shape in its table
// exercised it, and the bug was found by review instead.

import { readdirSync, readFileSync, existsSync, statSync } from "node:fs";
import { join, relative } from "node:path";
import yaml from "js-yaml";
import { sectionsOf, stepsOf } from "../../src/Steps.ts";

const ROOT = process.cwd();
const CONTENT = join(ROOT, "content");
const DIST = join(ROOT, "dist");
const MANIFEST = join(ROOT, "data", "manifest", "map-manifest.json");

// The renderer's labels, named here so an unrecognised `choice` can be reported as such. Kept
// as a list rather than imported because src/Steps.ts does not export it, and the failure mode
// of drift here is a WARN that stops firing -- not a wrong page.
const KNOWN_CHOICE = new Set(["pick", "depends", "true"]);

// A section id becomes a DOM id, the `map-<id>` id of its viewer, a querySelector argument in
// MapViewer's client script and a URL fragment. Anything outside this class breaks at least
// one of those, and a capital letter breaks only the fragment, which is the one nobody tests.
const ID = /^[a-z0-9]+(?:-[a-z0-9]+)*$/;

const isNonEmptyString = (v) => typeof v === "string" && v.trim() !== "";

// `choice` as src/Steps.ts reads it, so "is this a choice at all" is answered once.
const kindOf = (v) => {
  if (v === true) return "true";
  if (typeof v !== "string" || !v || v === "false") return null;
  return v;
};

// The same three-way filter src/Chapters.ts applies. A companion declares its pointer and is
// not a chapter; re-deciding that here is how the two lists drift, so it is one expression.
const isChapter = (fm) => fm && !fm.companion_to && !fm.technical_to;

const manifest = existsSync(MANIFEST)
  ? new Set(
      JSON.parse(readFileSync(MANIFEST, "utf8")).maps.map((m) => m.map_id),
    )
  : null;

// ---------------------------------------------------------------------------------------
// The rules. One function, so the fixture table below and content/ go through the same code.
// ---------------------------------------------------------------------------------------

function checkChapter(fm) {
  const out = [];
  let sections = 0;
  let steps = 0;
  const error = (where, msg) => out.push({ level: "error", where, msg });
  const warn = (where, msg) => out.push({ level: "warn", where, msg });

  const seenId = new Map();

  sectionsOf(fm).forEach((section, si) => {
    sections++;
    const at = `section ${si + 1}${isNonEmptyString(section?.id) ? ` (${section.id})` : ""}`;

    // -- B5: ids ------------------------------------------------------------------------
    if (!isNonEmptyString(section?.id)) {
      error(
        at,
        "section has no `id:`. The id is the section's DOM id, its viewer's `map-<id>` id and " +
          "its link target; without one the viewer cannot be addressed at all.",
      );
    } else if (!ID.test(section.id)) {
      error(
        at,
        `id "${section.id}" is not lowercase kebab-case. It is used raw as a DOM id, inside a ` +
          "querySelector and as a URL fragment, and a space, a dot or a capital breaks at least " +
          "one of those.",
      );
    } else if (seenId.has(section.id)) {
      error(
        at,
        `id "${section.id}" is already used by section ${seenId.get(section.id) + 1}. The page ` +
          `emits duplicate DOM ids and MapViewer resolves "#${section.id}" to the FIRST one, so ` +
          "this section's viewer silently draws the earlier section's pins.",
      );
    } else {
      seenId.set(section.id, si);
    }

    if (!isNonEmptyString(section?.title))
      error(at, "section has no `title:`, so the page renders an empty <h2>.");

    // A section whose map is absent from the manifest renders its steps and no map, on
    // purpose -- but a typo is indistinguishable from that decision, and at ~500 hand-written
    // map ids the typo is the likelier of the two. Reported, never fatal.
    if (
      manifest &&
      isNonEmptyString(section?.map) &&
      !manifest.has(section.map)
    )
      warn(
        at,
        `map "${section.map}" is not in map-manifest.json, so this section renders with no map. ` +
          "That is legal; check it is deliberate and not a typo.",
      );

    // -- B3: steps ----------------------------------------------------------------------
    const raw = Array.isArray(section?.steps) ? section.steps : [];
    const list = stepsOf(section);
    steps += list.length;

    if (!raw.length) warn(at, "section has no steps.");

    raw.forEach((s, i) => {
      const where = `${at} · step ${i + 1}`;
      if (typeof s === "string") {
        if (!s.trim())
          error(where, "step is empty, so it renders a badge and no sentence.");
        return;
      }
      if (s === null || typeof s !== "object") {
        error(
          where,
          `step is ${s === null ? "null" : typeof s}; a step is a string or a mapping.`,
        );
        return;
      }

      if (!isNonEmptyString(s.text))
        error(
          where,
          "step has no `text:`, so it renders a numbered badge beside nothing.",
        );

      // `at:` is the whole point of a pin, and coord() returns null for anything malformed --
      // `at: [16]`, `at: "16,4"` and `at: {x: 16, y: 4}` all drop the pin with no other sign.
      if (s.at !== undefined && list[i] && list[i].at === null)
        error(
          where,
          `\`at:\` is ${JSON.stringify(s.at)}, which is not a two-number [x, y]. The step ` +
            "renders, and its pin silently does not.",
        );

      const kind = kindOf(s.choice);
      const group = isNonEmptyString(s.choice_group) ? s.choice_group : null;

      if (s.choice === false)
        error(
          where,
          '`choice: false` is forbidden -- it is a second spelling of "not a choice" and is ' +
            "read as absent. Delete the key.",
        );

      if (s.choice_group !== undefined && !group)
        error(
          where,
          `\`choice_group\` is ${JSON.stringify(s.choice_group)}; it must be a non-empty string.`,
        );

      if (group && !kind)
        error(
          where,
          "`choice_group` without `choice`. Decision 25 requires both keys together; with one " +
            "missing the renderer ignores the group entirely and the step renders alone.",
        );

      if (kind && !group)
        error(
          where,
          "`choice` without `choice_group`. Adjacency was explicitly rejected as the grouping " +
            "signal (decision 25), so a choice with no group has nothing to join and degrades " +
            "to an ordinary step.",
        );

      if (kind && group && !KNOWN_CHOICE.has(kind))
        warn(
          where,
          `\`choice: ${kind}\` is not a value the renderer labels (pick, depends). The run still ` +
            "groups, unlabelled -- which is the contract's forward compatibility, so this is only " +
            "a warning. Check the spelling.",
        );

      // A declared group that comes back null from the renderer's own maximal-run pass had no
      // neighbour sharing it. Read off `stepsOf` rather than recomputed, so this reports the
      // grouping the page will draw and not a second opinion about it.
      if (kind && group && list[i] && list[i].group === null)
        error(
          where,
          `\`choice_group: ${group}\` has no neighbour sharing it, so it is a group of one. The ` +
            'renderer drops it rather than print a "Pick one:" over a single option; either give ' +
            "it its alternatives or remove both keys.",
        );
    });

    // -- B3: runs -----------------------------------------------------------------------
    const runs = [];
    for (let i = 0; i < list.length; i++) {
      if (!list[i].group) continue;
      const start = i;
      while (i + 1 < list.length && list[i + 1].group === list[start].group)
        i++;
      runs.push({ group: list[start].group, start, end: i });
    }

    for (const run of runs) {
      // The label is taken from the FIRST member only, so a different `choice` further down a
      // run is read, discarded, and never appears anywhere.
      const kinds = new Set();
      for (let i = run.start; i <= run.end; i++) {
        const s = raw[i];
        const k = s && typeof s === "object" ? kindOf(s.choice) : null;
        if (k) kinds.add(k);
      }
      if (kinds.size > 1)
        error(
          `${at} · steps ${run.start + 1}-${run.end + 1}`,
          `one \`choice_group\` ("${run.group}") carries more than one \`choice\` value ` +
            `(${[...kinds].join(", ")}). Only the first member's value is read, so the others are ` +
            "silently discarded. Make the run agree.",
        );
    }

    const slugRuns = new Map();
    for (const run of runs)
      slugRuns.set(run.group, (slugRuns.get(run.group) ?? 0) + 1);
    for (const [slug, n] of slugRuns)
      if (n > 1)
        warn(
          at,
          `\`choice_group: ${slug}\` names ${n} separate runs in this section. A group is a ` +
            "MAXIMAL RUN, so these render as two independent choices rather than one. Legal, and " +
            "rarely what was meant.",
        );
  });

  return { out, sections, steps };
}

// ---------------------------------------------------------------------------------------
// content/**/*.md
// ---------------------------------------------------------------------------------------

function markdownFiles(dir) {
  const found = [];
  for (const name of readdirSync(dir)) {
    const p = join(dir, name);
    if (statSync(p).isDirectory()) found.push(...markdownFiles(p));
    else if (name.endsWith(".md")) found.push(p);
  }
  return found;
}

const frontmatterOf = (text) => {
  const m = /^---\r?\n([\s\S]*?)\r?\n---(\r?\n|$)/.exec(text);
  if (!m) return null;
  try {
    return yaml.load(m[1]) ?? {};
  } catch (e) {
    return { __yamlError: String(e.message ?? e) };
  }
};

let errors = 0;
let warns = 0;
const report = (where, d) => {
  const line = `${d.level === "error" ? "ERROR" : "WARN "} ${where} · ${d.where}\n      ${d.msg}`;
  if (d.level === "error") {
    errors++;
    console.error(line);
  } else {
    warns++;
    console.warn(line);
  }
};

let chapters = 0;
let sectionCount = 0;
let stepCount = 0;

for (const file of (existsSync(CONTENT) ? markdownFiles(CONTENT) : []).sort()) {
  const rel = relative(ROOT, file);
  const fm = frontmatterOf(readFileSync(file, "utf8"));
  if (fm?.__yamlError) {
    report(rel, {
      level: "error",
      where: "frontmatter",
      msg: `not valid YAML: ${fm.__yamlError}`,
    });
    continue;
  }
  if (!isChapter(fm)) continue;
  chapters++;
  const r = checkChapter(fm);
  sectionCount += r.sections;
  stepCount += r.steps;
  for (const d of r.out) report(rel, d);
}

console.log(
  `${chapters} chapter(s), ${sectionCount} section(s), ${stepCount} step(s) checked against the sections: contract`,
);

// ---------------------------------------------------------------------------------------
// Built output: B7, the badge and the pin cannot disagree
// ---------------------------------------------------------------------------------------
//
// `ol.steps > li::before` renders `counter(step)` and `ol.steps > li[data-step]::before`
// overrides it with `attr(data-step)`; MapViewer's script queries `li[data-step][data-at]`.
// So a step that renders without `data-step` still shows a number -- the CSS counter's number
// -- while the pin script skips it, and from that point the badges and the pins are counting
// two different things. Nothing in the source can prove this; it is a property of the emitted
// HTML, so it is measured there.

const OL = /<ol\b[^>]*\bclass="steps"[^>]*>([\s\S]*?)<\/ol>/g;
const LI = /<li\b([^>]*)>/g;
const walkDir = join(DIST, "walkthrough");

if (!existsSync(walkDir)) {
  // Said out loud rather than skipped quietly. Three separate defects in this repo were
  // harnesses that measured nothing and reported success for it.
  console.log(
    "dist/walkthrough is absent, so the built-output check (B7: data-step on every step) did " +
      "NOT run. Build first if you wanted it.",
  );
} else {
  const pages = readdirSync(walkDir)
    .map((d) => join(walkDir, d, "index.html"))
    .filter((p) => existsSync(p));
  let lists = 0;
  let items = 0;
  for (const page of pages) {
    const html = readFileSync(page, "utf8");
    let m;
    OL.lastIndex = 0;
    while ((m = OL.exec(html))) {
      lists++;
      const here = `${relative(ROOT, page)} · steps list ${lists}`;
      [...m[1].matchAll(LI)].forEach((li, i) => {
        items++;
        const d = /\bdata-step="(\d+)"/.exec(li[1]);
        if (!d)
          report(here, {
            level: "error",
            where: `item ${i + 1}`,
            msg:
              "rendered <li> carries no data-step, so its badge falls back to the CSS counter " +
              "while MapViewer's `li[data-step][data-at]` query skips it. From here the badges " +
              "and the pins are numbering two different lists.",
          });
        else if (Number(d[1]) !== i + 1)
          report(here, {
            level: "error",
            where: `item ${i + 1}`,
            msg:
              `data-step="${d[1]}" on the item in position ${i + 1}. The badge prints the ` +
              "attribute and the reader counts positions, so the two disagree on this page.",
          });
      });
    }
  }
  console.log(
    `${pages.length} built chapter page(s), ${lists} steps list(s), ${items} step(s) checked for data-step`,
  );
}

// ---------------------------------------------------------------------------------------
// The fixture table. Every rule above, broken on purpose.
// ---------------------------------------------------------------------------------------
//
// Each fixture is the `sections:` block an author would actually write, in YAML, so the read
// path is tested alongside the rule. `expect` lists a distinctive fragment of every diagnostic
// the fixture must produce -- and the COUNT must match too, so a rule that fires twice, or a
// second rule that fires by accident, fails here rather than in a chapter.

const S = (steps, extra = "") => `
sections:
  - id: pallet-town
    map: MAP_PALLET_TOWN
    title: Pallet Town${extra}
    steps:
${steps}
`;

const FIXTURES = [
  {
    name: "healthy: a plain step and a real two-member group",
    yaml: S(
      `      - Go downstairs.
      - text: Take the left ball.
        choice: pick
        choice_group: starter
      - text: Take the right ball.
        choice: pick
        choice_group: starter`,
    ),
    expect: [],
  },

  {
    name: "B5 · no id",
    yaml: `
sections:
  - map: MAP_PALLET_TOWN
    title: Pallet Town
    steps: [Go downstairs.]
`,
    expect: ["has no `id:`"],
  },

  {
    name: "B5 · id is not kebab-case",
    yaml: `
sections:
  - id: Oaks Lab
    map: MAP_PALLET_TOWN
    title: Oak's Lab
    steps: [Go downstairs.]
`,
    expect: ["is not lowercase kebab-case"],
  },

  {
    name: "B5 · two sections share an id",
    yaml: `
sections:
  - id: pallet-town
    map: MAP_PALLET_TOWN
    title: Pallet Town
    steps: [Go downstairs.]
  - id: pallet-town
    map: MAP_ROUTE1
    title: Route 1
    steps: [Walk north.]
`,
    expect: ["is already used by section 1"],
  },

  {
    name: "B5 · no title",
    yaml: `
sections:
  - id: pallet-town
    map: MAP_PALLET_TOWN
    steps: [Go downstairs.]
`,
    expect: ["has no `title:`"],
  },

  {
    name: "map id is not in the manifest",
    yaml: `
sections:
  - id: pallet-town
    map: MAP_PALLET_TOWNN
    title: Pallet Town
    steps: [Go downstairs.]
`,
    expect: ["is not in map-manifest.json"],
  },

  {
    name: "section with no steps",
    yaml: `
sections:
  - id: pallet-town
    map: MAP_PALLET_TOWN
    title: Pallet Town
    steps: []
`,
    expect: ["has no steps"],
  },

  {
    name: "empty step string",
    yaml: S(`      - ""`),
    expect: ["step is empty"],
  },

  {
    name: "mapping step with no text",
    yaml: S(`      - at: [6, 7]`),
    expect: ["has no `text:`"],
  },

  {
    name: "malformed at:",
    yaml: S(
      `      - text: Head out of your front door.
        at: [6]`,
    ),
    expect: ["not a two-number"],
  },

  {
    name: "B3 · choice: false",
    yaml: S(
      `      - text: Go downstairs.
        choice: false`,
    ),
    expect: ["`choice: false` is forbidden"],
  },

  {
    name: "B3 · empty choice_group",
    yaml: S(
      `      - text: Take the left ball.
        choice: pick
        choice_group: ""`,
    ),
    expect: ["must be a non-empty string", "without `choice_group`"],
  },

  {
    name: "B3 · choice_group without choice",
    yaml: S(
      `      - text: Take the left ball.
        choice_group: starter
      - text: Take the right ball.
        choice_group: starter`,
    ),
    expect: ["without `choice`", "without `choice`"],
  },

  {
    name: "B3 · choice without choice_group",
    yaml: S(
      `      - text: Take the left ball.
        choice: pick`,
    ),
    expect: ["without `choice_group`"],
  },

  {
    name: "B3 · a group of one",
    yaml: S(
      `      - text: Take the left ball.
        choice: pick
        choice_group: starter
      - Walk out.`,
    ),
    expect: ["is a group of one"],
  },

  {
    name: "B3 · unrecognised choice value",
    yaml: S(
      `      - text: Take the left ball.
        choice: maybe
        choice_group: starter
      - text: Take the right ball.
        choice: maybe
        choice_group: starter`,
    ),
    expect: [
      "is not a value the renderer labels",
      "is not a value the renderer labels",
    ],
  },

  {
    name: "B3 · one run, two choice values",
    yaml: S(
      `      - text: Take the left ball.
        choice: pick
        choice_group: starter
      - text: Take the right ball.
        choice: depends
        choice_group: starter`,
    ),
    expect: ["more than one `choice` value"],
  },

  {
    name: "B3 · one slug, two separate runs",
    yaml: S(
      `      - text: Take the left ball.
        choice: pick
        choice_group: starter
      - text: Take the right ball.
        choice: pick
        choice_group: starter
      - Walk out.
      - text: Come back for the third.
        choice: pick
        choice_group: starter
      - text: Or the fourth.
        choice: pick
        choice_group: starter`,
    ),
    expect: ["names 2 separate runs"],
  },
];

let fixFailed = 0;
for (const f of FIXTURES) {
  const got = checkChapter(yaml.load(f.yaml)).out;
  const lines = got.map((d) => d.msg);
  const missing = [];
  const pool = [...lines];
  for (const want of f.expect) {
    const hit = pool.findIndex((l) => l.includes(want));
    if (hit < 0) missing.push(want);
    else pool.splice(hit, 1);
  }
  if (missing.length || pool.length) {
    fixFailed++;
    console.error(
      `FIXTURE FAIL  ${f.name}` +
        (missing.length
          ? `\n      never fired: ${missing.map((m) => `"${m}"`).join(", ")}`
          : "") +
        (pool.length
          ? `\n      unexpected: ${pool.map((m) => `"${m}"`).join("\n                  ")}`
          : ""),
    );
  }
}

console.log(
  fixFailed
    ? `\n${FIXTURES.length} fixtures, ${fixFailed} FAILED`
    : `${FIXTURES.length} fixtures: every rule fires on content that breaks it, and the healthy one is silent`,
);

if (errors || warns || fixFailed)
  console.log(`\n${errors} error(s), ${warns} warning(s)`);
else console.log("no errors, no warnings");

process.exit(errors || fixFailed ? 1 : 0);
