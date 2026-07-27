// The game's own FEATURES.md, reshaped for the reader this guide is written for.
//
// The file is READ FROM THE SUBMODULE at build time and never copied into this repo. The
// guide's premise is that it re-derives from the game's source, so a re-pin that rewrites
// FEATURES.md rewrites this page with it. A hand-copied features page is wrong at the next pin
// and nothing tells you.
//
// Nothing below names a heading in order to RENDER it: the parse walks whatever headings the
// file has. The tables name headings only to decide ORDER, and a heading missing from them
// falls into the middle tier rather than off the page -- a section the next re-pin adds
// publishes, in the wrong group at worst, instead of vanishing silently.
//
// BUILD-TIME ONLY, same contract as src/Sprites.ts: node:fs here is evaluated by Astro in Node
// during the build and never bundled for the browser.
import fs from "node:fs";
import path from "node:path";
import maps from "../data/generated/maps.json";

const mods = import.meta.glob("/game/FEATURES.md", { eager: true }) as Record<
  string,
  any
>;

export type Tier = "play" | "extra" | "build";

/** Heading text reduced to a match key. Entities go first: the compiled HTML spells the
 *  ampersand in "QoL &amp; gameplay defaults", and dropping punctuation alone would leave
 *  "amp" wedged in the middle of the key. */
const key = (s: string) =>
  s
    .toLowerCase()
    .replace(/&[a-z]+;|&#x?[0-9a-f]+;/gi, "")
    .replace(/[^a-z0-9]+/g, "");

const tierTable: [string, Tier][] = [
  // Why someone plays this hack rather than Emerald. This is the page.
  ["Three regions, one game", "play"],
  ["Character customization", "play"],
  ["Riding your Pokémon", "play"],
  // Real, and you will meet it, but it is not why you are here.
  ["Ported features", "extra"],
  ["QoL & gameplay defaults", "extra"],
  // Written for someone building the ROM, not playing it. Kept, moved to the bottom.
  ["Developer additions", "build"],
  ["Tools, libraries & systems", "build"],
  ["Roadmap", "build"],
  ["Inherited from pokeemerald-expansion", "build"],
];
const TIER_OF = new Map(tierTable.map(([h, t]) => [key(h), t] as const));
const DEFAULT_TIER: Tier = "extra";

// The one heading that is navigation rather than content. Its targets are hard-coded #anchors
// that rot the moment a heading is renamed, and the fold summaries below already are the
// page's contents -- each one carries the count that decides whether to open it.
const DROPPED = new Set([key("Table of Contents")]);

/** A section the source marks as not shipping. The guide must never present either as
 *  playable, so the marker survives into the summary line a reader reads while it is shut. */
export const STATUS: Record<string, { chip: string; line: string }> = {
  unreleased: {
    chip: "Not yet",
    line: "This is written down in the game's notes, but it is not switched on. You cannot play it.",
  },
  dormant: {
    chip: "Dormant",
    line: "The code is in the game, but nothing in the game reaches it. You will never see it.",
  },
};
const HINT: Record<string, string> = {
  unreleased: "Not in the game yet",
  dormant: "Built, but switched off",
};

/** A trailing parenthetical that is even a CANDIDATE to be a marker: letters, spaces and hyphens
 *  only, so a generation, a version or a count -- "(Gen 8)", "(v1.3)", "(2 of 3)" -- is not one.
 *  Being a candidate is not being a status. MARKERS below decides that. */
const PAREN_RE = /\s*\(\s*([a-z][a-z -]{0,29})\s*\)\s*$/i;

/** Words that say a section is NOT FINISHED, as opposed to words that say what it covers.
 *
 *  A HEADING'S BRACKETS ARE USUALLY PROSE. `STATUS_RE` used to take any bracket of letters and
 *  spaces as a marker, which is a pattern standing in for a meaning it cannot see: `(beta)` and
 *  `(all three regions)` are the same shape, and the second is a heading describing itself.
 *  Under that rule `### Region switching (all three regions)` published as shipped, playable
 *  content wearing a red "all three regions" chip, a "cannot promise you can play this" warning
 *  and its own heading text cut off -- the guide lying about content that is in the game, which
 *  is decision 42's harm with the sign flipped.
 *
 *  Pattern cannot separate the two, so vocabulary does. THE WARNING IS WHAT KEEPS DECISION 47
 *  WHOLE, not the chip: every candidate the guide does not recognise is still named at the end
 *  of the build, so a re-pin that introduces a genuinely new status word is told about it in the
 *  same breath it would have been before. What changes is only what the PAGE does while the
 *  operator reads that warning -- publish the heading as the source wrote it, rather than
 *  publish a red contradiction of it. Both directions warn; only one of them can ship a lie.
 *
 *  Wider than the two the guide can explain, on purpose: a word here is recognised as a status
 *  even when there is no sentence for it, which is exactly decision 47's case. */
const MARKERS = new Set(
  (
    "alpha, beta, broken, coming soon, deprecated, disabled, dormant, draft, early access, " +
    "experimental, in development, in progress, incomplete, not implemented, not yet, on hold, " +
    "paused, planned, preview, prototype, removed, retired, scrapped, shelved, stub, tbd, " +
    "todo, unfinished, unimplemented, unreleased, unstable, untested, upcoming, wip, " +
    "work in progress"
  ).split(", "),
);

/** Case and separators folded, so "WIP", "Work-In-Progress" and "work in progress" are one word
 *  to the lookup and the source's own spelling is still what reaches the page. */
const norm = (s: string) =>
  s
    .toLowerCase()
    .replace(/[\s-]+/g, " ")
    .trim();

const isStatus = (s: string) => MARKERS.has(norm(s));

/** What the page says about a marker. A word the guide knows gets the sentence it has earned;
 *  an unrecognised one gets the only thing that is actually true about it -- the source wrote
 *  this word, and the guide cannot vouch for what it means. It must not inherit "You cannot
 *  play it", because that is a claim about the game nobody here has checked. */
export const noteOf = (s: string) =>
  STATUS[norm(s)] ?? {
    // The source's own spelling, so "WIP" is not flattened to "Wip".
    chip: s,
    line: `The game's notes mark this "${s}". This guide does not know that word, so it cannot promise you can play this — check the game's own notes first.`,
  };

const hintFor = (s: string) =>
  HINT[norm(s)] ?? `Marked "${s}" in the game's notes`;

const known = (s: string) => norm(s) in STATUS;

const REPO = (() => {
  // Read rather than hard-coded, so the source links follow the submodule the way the content
  // does.
  const conf = fs.readFileSync(path.join(process.cwd(), ".gitmodules"), "utf8");
  const m = conf.match(/^\s*url\s*=\s*(\S+?)(?:\.git)?\s*$/m);
  if (!m) throw new Error(".gitmodules declares no submodule url");
  return m[1];
})();
const COMMIT: string = (maps as any).game_commit;

/** A path inside the game repo, at the pinned commit. */
const fileUrl = (p: string) =>
  `${REPO}/blob/${COMMIT}/${p.replace(/^\.?\/+/, "")}`;

export const SOURCE_URL = fileUrl("FEATURES.md");

const NAMED: Record<string, string> = {
  amp: "&",
  lt: "<",
  gt: ">",
  quot: '"',
  apos: "'",
  nbsp: " ",
};

/** Heading HTML to the plain string a <Fold> label or an <h2> takes. Both forms of escape have
 *  to be undone, not just the ones this file happens to use today: the label is handed to Astro
 *  as TEXT and re-escaped, so a survivor comes out as the literal "&#x26;" on the page. The
 *  markdown compiler spells "&" numerically, which is exactly the case a named-entity-only
 *  decoder misses. */
const plain = (h: string) =>
  h
    .replace(/<[^>]+>/g, "")
    .replace(/&#x([0-9a-f]+);/gi, (_, n) =>
      String.fromCodePoint(parseInt(n, 16)),
    )
    .replace(/&#(\d+);/g, (_, n) => String.fromCodePoint(Number(n)))
    .replace(/&([a-z]+);/gi, (all, n: string) => NAMED[n.toLowerCase()] ?? all)
    .trim();

/** The count a summary line prints. Same derivation as the chapter bodies (decision 38): the
 *  rows a reader can count for themselves after opening it, and nothing else (decision 39). */
const rowsIn = (h: string) =>
  (h.match(/<tbody>[\s\S]*?<\/tbody>/g) ?? []).join("").split("<tr").length -
  1 +
  (h.match(/<li\b/g) ?? []).length;

const statusOf = (text: string) => {
  const m = text.match(PAREN_RE)?.[1].trim();
  return m && isStatus(m) ? m : null;
};

/** A candidate the vocabulary did not claim. Reported at the end of the build so a genuinely new
 *  status word is still caught by the person doing the re-pin -- see MARKERS. */
const proseOf = (text: string) => {
  const m = text.match(PAREN_RE)?.[1].trim();
  return m && !isStatus(m) ? m : null;
};

/** The marker comes off the heading only when it IS a marker. A parenthetical the guide reads as
 *  prose is part of what the heading says, and cutting it changes the heading's meaning. */
const stripStatus = (text: string) =>
  statusOf(text) ? text.replace(PAREN_RE, "") : text;

/** Splits a leading heading off a chunk of compiled markdown. */
function head(chunk: string, tag: "h2" | "h3") {
  const m = chunk.match(new RegExp(`^<${tag}\\b[^>]*>([\\s\\S]*?)</${tag}>`));
  if (!m) return { text: null as string | null, id: null, rest: chunk };
  return {
    text: plain(m[1]),
    id: m[0].match(/\bid="([^"]*)"/)?.[1] ?? null,
    rest: chunk.slice(m[0].length),
  };
}

/** Statuses on headings that stay headings rather than becoming a fold label carry the marker
 *  as a chip, so "(dormant)" is still visible when the section is read inside another fold. */
const chipStatuses = (html: string) =>
  html.replace(
    /(<h[1-6]\b[^>]*>)([\s\S]*?)(<\/h[1-6]>)/g,
    (all, open: string, inner: string, close: string) => {
      const s = statusOf(plain(inner));
      if (!s) return all;
      return `${open}${inner.replace(PAREN_RE, "")} <span class="chip trainer">${noteOf(s).chip}</span>${close}`;
    },
  );

/** A six-column table is wider than a phone. Every table on this site scrolls inside its own
 *  box rather than scrolling the document sideways. */
const scrollTables = (html: string) =>
  html.replace(
    /<table[\s\S]*?<\/table>/g,
    (t) => `<div class="scroll-x">${t}</div>`,
  );

/** FEATURES.md is written to be read on GitHub, so it links to files beside it and to its own
 *  headings. Neither exists here, and tools/qa/Links.mjs cannot see either -- it only checks
 *  hrefs under the site's base path -- so a relative link left alone is a broken link nothing
 *  reports. Repo-relative paths become absolute source links; an in-page anchor is kept when
 *  the heading it names survived onto this page and sent to the source file when it did not,
 *  which degrades to a link that works rather than one that goes nowhere. */
function rewriteLinks(html: string, ids: Set<string>) {
  return (
    html
      .replace(/\shref="([^"]+)"/g, (all, href: string) => {
        if (/^(https?:|mailto:|\/\/)/i.test(href)) return all;
        if (href.startsWith("#"))
          return ids.has(href.slice(1)) ? all : ` href="${SOURCE_URL}${href}"`;
        return ` href="${fileUrl(href)}"`;
      })
      // An image with a repo-relative src would 404 here, and pointing it at
      // raw.githubusercontent would make the page fetch from another host, which this site does
      // not do. It becomes a link to the file instead.
      .replace(
        /<img\b[^>]*?\ssrc="(?!https?:|data:|\/\/)([^"]+)"[^>]*>/gi,
        (_all, src: string) =>
          `<a href="${fileUrl(src)}"><code>${src}</code></a>`,
      )
  );
}

export type Sub = {
  id: string | null;
  label: string;
  status: string | null;
  hint: string | null;
  count: number;
  fold: boolean;
  html: string;
};

export type Section = Sub & {
  tier: Tier;
  /** Prose under the heading, above the first subheading. An open section renders it directly. */
  lede: string;
  kids: Sub[];
};

/** Two subheadings named on the summary at most, and short ones only: the summary line is a
 *  flex row and a long unbreakable hint is how a page starts scrolling sideways on a phone. */
function hintOf(kids: Sub[]) {
  if (!kids.length) return null;
  const shown: string[] = [];
  let len = 0;
  for (const k of kids) {
    if (shown.length >= 2 || len + k.label.length > 32) break;
    shown.push(k.label);
    len += k.label.length + 3;
  }
  if (!shown.length) return `${kids.length} topics`;
  const rest = kids.length - shown.length;
  return shown.join(" · ") + (rest ? ` +${rest} more` : "");
}

export async function featurePage() {
  const mod = Object.values(mods)[0];
  if (!mod)
    throw new Error(
      "game/FEATURES.md not found — is the submodule checked out?",
    );

  const compiled: string = await mod.compiledContent();
  const parts = compiled.split(/(?=<h2[\s>])/);
  // Everything above the first <h2>: the file's own one-paragraph summary of itself, minus the
  // <h1>, which the masthead already prints.
  const introRaw = (parts.shift() ?? "").replace(/<h1\b[\s\S]*?<\/h1>/, "");

  const raw = parts
    .filter((c) => c.trim())
    .map((chunk) => {
      const h = head(chunk, "h2");
      const cut = h.rest.search(/<h3[\s>]/);
      return {
        h,
        label: h.text ?? "",
        // The heading as written first, then the heading with any trailing parenthetical taken
        // off: a section that gains "(unreleased)" between two pins is the same section, and
        // losing its group over the parenthesis would quietly demote it to the default tier at
        // exactly the moment it matters most. Trying the full heading first is what lets a
        // parenthetical that is genuinely part of the name be matched as part of the name.
        tier:
          TIER_OF.get(key(h.text ?? "")) ??
          TIER_OF.get(key((h.text ?? "").replace(PAREN_RE, ""))) ??
          DEFAULT_TIER,
        own: cut < 0 ? h.rest : h.rest.slice(0, cut),
        subs:
          cut < 0
            ? []
            : h.rest
                .slice(cut)
                .split(/(?=<h3[\s>])/)
                .filter((c) => c.trim()),
      };
    })
    .filter((s) => !DROPPED.has(key(s.label)));

  // Every id that survived onto the page, so an in-page anchor can be told from a dead one.
  const ids = new Set<string>();
  for (const s of raw) {
    if (s.h.id) ids.add(s.h.id);
    for (const c of s.subs) {
      const id = head(c, "h3").id;
      if (id) ids.add(id);
    }
  }

  const clean = (h: string) => scrollTables(chipStatuses(rewriteLinks(h, ids)));

  // Markers the guide does not know. Collected rather than thrown: decision 41's judgement that
  // a re-pin must not be able to break the build still holds. But a re-pin IS a scheduled
  // maintenance action, so the person doing it is told, once, at the end of the build.
  const strange: string[] = [];
  const noteStatus = (s: string | null, where: string) => {
    if (s && !known(s)) strange.push(`"${s}" on ${where}`);
    return s;
  };
  // Candidates the vocabulary did not claim. The page publishes these as written; the warning is
  // what keeps decision 47 whole, so it names every one rather than only the surprising ones.
  const prose: string[] = [];
  const noteProse = (where: string) => {
    const p = proseOf(where);
    if (p) prose.push(`"${p}" on ${where}`);
  };

  const sections: Section[] = raw.map((s) => {
    const status = noteStatus(statusOf(s.label), s.label);
    noteProse(s.label);
    const kids: Sub[] = s.subs.map((chunk) => {
      const k = head(chunk, "h3");
      const kstatus = noteStatus(statusOf(k.text ?? ""), k.text ?? "");
      noteProse(k.text ?? "");
      const html = clean(k.rest);
      const count = rowsIn(html);
      return {
        id: k.id,
        label: stripStatus(k.text ?? ""),
        status: kstatus,
        hint: kstatus ? hintFor(kstatus) : null,
        count,
        fold: !!kstatus || count > 0,
        html,
      };
    });

    const lede = clean(s.own);
    // A folded section swallows its own subheadings; an open one hands them to the page as
    // separate blocks so each can fold on its own.
    const whole = clean(s.h.rest);
    const count = rowsIn(whole);
    return {
      tier: s.tier,
      id: s.h.id,
      label: stripStatus(s.label),
      status,
      hint: status ? hintFor(status) : hintOf(kids),
      count,
      // A play-tier section with subheadings opens, so the page reads as prose with its
      // reference lists folded underneath -- the chapter-body rule (decision 38) applied to a
      // page whose lists are the part a ten-year-old skips. Everything else folds, and anything
      // the source marks unreleased or dormant folds whatever it contains.
      fold: s.tier !== "play" || !!status || (!kids.length && count > 0),
      lede,
      html: whole,
      kids,
    };
  });

  if (strange.length)
    console.warn(
      `[features] FEATURES.md carries ${strange.length} status marker(s) this guide does not know: ${strange.join(", ")}. ` +
        `Each is folded, tagged and flagged as unconfirmed rather than published as playable. ` +
        `Teach src/Features.ts the word, or drop the brackets in the source if it was never a status.`,
    );
  if (prose.length)
    console.warn(
      `[features] FEATURES.md carries ${prose.length} trailing parenthetical(s) this guide reads as part of the heading rather than as a status marker: ${prose.join(", ")}. ` +
        `Each is published exactly as the source wrote it. ` +
        `If one of them means the section is not finished, add the word to MARKERS in src/Features.ts; otherwise there is nothing to do.`,
    );

  return { intro: clean(introRaw), sections, sourceUrl: SOURCE_URL };
}
