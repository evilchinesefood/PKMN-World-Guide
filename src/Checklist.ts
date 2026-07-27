// The departure checklist. Markdown's `- [ ]` compiles to `<input type="checkbox" disabled>` --
// a box drawn on the page that a reader cannot tick. This turns each item into a real control.
//
// IDENTITY IS THE ITEM'S OWN TEXT, NOT ITS POSITION IN THE LIST. Position is the obvious key and
// it is the wrong one: insert an item at the top and every tick below it slides onto the wrong
// line, and the brand-new item inherits whatever was ticked in its slot -- a checklist that
// silently marks work done the reader never did is worse than one that does not persist at all.
// Hashing the text cannot do that. A new item is a new key and starts unticked, and an item that
// merely moves keeps its tick. The cost is that rewording an item resets it: the thing being
// asked has changed, so the reader should look again. Markup-only edits do not count -- tags are
// stripped and whitespace collapsed before hashing -- so bolding a word or repointing a link
// leaves the tick alone.
//
// RESETTING IS NOT THE ONLY FAILURE LEFT, AND CALLING IT "THE HONEST ONE" WOULD BE A LIE. Two
// items with the same sentence are told apart by their position inside that duplicate set
// (decision 48), so deleting one shifts the survivors onto the earlier keys and a survivor can
// inherit its deleted twin's tick. That is FALSE CREDIT -- the dishonest failure, the one this
// whole design exists to avoid -- and it is kept deliberately, because the alternative charges
// the same coin on the commoner edit (chapters gain duplicates far more often than they lose
// them) and charges it to the one line that can already be carrying a reader's tick. It is
// bounded to items whose text is identical, and the build names the sentence so an author can
// reword it away. Bounded and warned is not the same as absent.
//
// The `<input>` survives the rewrite on purpose. `[slug].astro` detects a task list by the
// checkbox it compiles to, and that detection is what keeps this section OUT of a fold.

/** The signal that a body section IS the departure checklist, and the contract every chapter
 *  M5 writes inherits: markdown's `- [ ]` compiles to a checkbox input and nothing else on
 *  these pages does. It lives here rather than in the page because the rewrite below is what
 *  has to keep it true -- the `<input>` survives on purpose, so a section is still detectable
 *  as a task list after being made tickable. tools/qa/Checklist.mjs asserts both halves. */
export const isTaskList = (h: string) => /<input[^>]+type="checkbox"/.test(h);

const text = (h: string) =>
  h
    .replace(/<[^>]+>/g, "")
    .replace(/\s+/g, " ")
    .trim();

// FNV-1a, base36. Short enough to read in devtools, stable across builds, no dependency.
export function keyOf(html: string): string {
  const s = text(html);
  let h = 0x811c9dc5;
  for (let i = 0; i < s.length; i++) {
    h ^= s.charCodeAt(i);
    h = Math.imul(h, 0x01000193);
  }
  return (h >>> 0).toString(36);
}

// An item ends at ITS OWN `</li>`, which is not the first one: a nested list closes its
// children first, so a non-greedy scan to `</li>` stops inside the child and takes the parent's
// closing tag with it. Depth counting finds the right one. Returns the closing tag's bounds.
function closeOf(html: string, from: number): [number, number] | null {
  const tag = /<li\b|<\/li\s*>/gi;
  tag.lastIndex = from;
  for (let depth = 1, m; (m = tag.exec(html));) {
    depth += m[0][1] === "/" ? -1 : 1;
    if (!depth) return [m.index, tag.lastIndex];
  }
  return null;
}

const BOX = /<input[^>]*type="checkbox"[^>]*>/i;

// In a TIGHT item the sentence ends at the item's first BLOCK-level child, and "block" is
// defined here BY EXCLUSION rather than by naming the blocks.
//
// PHRASING IS THE CLOSED SET; BLOCK IS THE OPEN ONE. HTML defines what phrasing content is and
// that definition does not grow when an author writes a `<div>`, a fenced code block or a custom
// element -- but the set of things that can sit under a checklist line does. Naming the blocks is
// what shipped shape six: `<(?:ul|ol)` called itself "the whole set", and a blockquote, an `###`
// heading, a raw `<div>`, a `***` rule and a code fence all walked through it into the `<label>`,
// taking the item's key -- and every tick stored against it -- with them.
//
// An unrecognised tag therefore ENDS the sentence. That is the safe direction: the worst case is
// content moved out of a `<label>` that could not legally have held it anyway.
const PHRASING = new Set(
  (
    "a abbr audio b bdi bdo br button canvas cite code data datalist del dfn em embed i " +
    "iframe img input ins kbd label map mark math meter noscript object output picture " +
    "progress q rp rt ruby s samp script select slot small span strong sub sup svg " +
    "template textarea time u var video wbr"
  ).split(" "),
);

/** Where the checkbox's own block ends: the offset of the first tag that is not phrasing
 *  content, or -1 if the item is a sentence and nothing else. */
function blockAt(html: string) {
  for (const m of html.matchAll(/<\/?([a-z][a-z0-9-]*)/gi))
    if (!PHRASING.has(m[1].toLowerCase())) return m.index;
  return -1;
}

/** An item's own sentence, and whatever the author put after it.
 *
 *  ONE RULE FOR BOTH SHAPES MARKDOWN PRODUCES. A list is LOOSE if there is a blank line
 *  anywhere in it, and a loose list wraps every item's text in a `<p>`; a tight one does not.
 *  An author does not choose between those on purpose -- they add a blank line for room to
 *  read -- so the two must not be two code paths. The sentence is the phrasing content
 *  following the checkbox INSIDE THE CHECKBOX'S OWN BLOCK, and the tail is every block after
 *  that one. Tight: the block is the `<li>` itself, so the sentence ends at the item's first
 *  block-level child, whatever that child is. Loose: the block is the `<p>`, so it ends at
 *  `</p>` and the tail is free to be another paragraph, a table or a list. Neither branch names
 *  a block tag.
 *
 *  Returns null for anything this does not recognise. The caller then leaves that item exactly
 *  as it came in -- the whole item, contents included -- and reports it, because an item this
 *  file declined to rewrite is a box that renders and does nothing, which is the signature of
 *  all five silent failures before it. */
function splitItem(item: string) {
  const box = item.match(BOX);
  if (!box) return null;
  const before = item.slice(0, box.index);
  const after = item.slice(box.index! + box[0].length);
  // Only whitespace, or the `<p>` a loose list adds, may precede the box.
  const wrap = before.match(/^\s*(<p\b[^>]*>)?\s*$/i);
  if (!wrap) return null;
  if (wrap[1]) {
    const end = after.search(/<\/p\s*>/i);
    if (end < 0) return null;
    // The `<p>` itself is dropped, so a checklist looks and behaves the same either way. It
    // wrapped the item's own sentence, and here the label IS the item -- an author must not get
    // a differently spaced checklist for a blank line.
    return {
      lead: after.slice(0, end),
      tail: after.slice(after.indexOf(">", end) + 1),
    };
  }
  const at = blockAt(after);
  return at < 0
    ? { lead: after, tail: "" }
    : { lead: after.slice(0, at), tail: after.slice(at) };
}

// The item's own sentence becomes the label, so the sentence is the hit target -- not a 12px
// box. The box and the tick are drawn in CSS on the <span>; the input itself is only kept for
// the state, the keyboard and the accessibility tree.
//
// TRAILING CONTENT STAYS IN THE ITEM BUT OUTSIDE THE LABEL. Three reasons, and the first alone
// decides it: <label> takes phrasing content, so a <ul> inside one is invalid markup. It is
// also the predictable target -- a reader tapping "Fighting beats Rock" under "Catch a Mankey"
// would otherwise tick the Mankey -- and it keeps the key honest, because the annotation is not
// the thing being ticked and must not change the hash when an author adds or edits it.
//
// TWO ITEMS WITH THE SAME SENTENCE HASH TO THE SAME KEY, and the tick then SPREADS: tick one,
// reload, and both come back ticked. That is the checklist crediting work the reader never did
// -- the exact failure decision 43 exists to prevent, reached by a route it did not consider.
//
// Identical text carries nothing that could tell the two apart, so the tiebreak has to be
// position, and the only real question is which occurrence pays for it. THE FIRST KEEPS THE
// BARE KEY: it is the one that may already be ticked in a reader's browser, and a chapter that
// gains a duplicate must not silently reset the line that was always there. Decision 48 states
// what that costs when a duplicate is later deleted, and the build warns, because rewording the
// duplicate is the only fix that removes the ambiguity rather than ordering it.
type Scope = {
  seen: Map<string, number>;
  repeated: string[];
  skipped: string[];
};

function walk(html: string, s: Scope): string {
  const open = /<li([^>]*\btask-list-item[^>]*)>/g;
  let out = "";
  let last = 0;
  for (let m; (m = open.exec(html));) {
    const from = m.index + m[0].length;
    const bounds = closeOf(html, from);
    // Unbalanced source: there is no end to skip to, so leave the rest of the chunk alone.
    if (!bounds) {
      s.skipped.push(text(html.slice(m.index)).slice(0, 60));
      break;
    }
    const [shut, after] = bounds;
    const split = splitItem(html.slice(from, shut));
    if (!split) {
      // A shape this file does not recognise is left WHOLE. Stepping the scan past the item's
      // own close is what makes that true: without it the scan walks back into the item and
      // rewrites a nested task list inside a parent nobody rewrote, which is half-rewritten,
      // not untouched.
      s.skipped.push(text(html.slice(from, shut)).slice(0, 60));
      open.lastIndex = after;
      continue;
    }
    const lead = split.lead.trim();
    const base = keyOf(lead);
    const n = (s.seen.get(base) ?? 0) + 1;
    s.seen.set(base, n);
    if (n === 2) s.repeated.push(text(lead));
    out +=
      html.slice(last, m.index) +
      // The tail is walked too: a task list nested under a task item is still a checklist, and
      // it shares the scope, so a duplicate across two nesting levels is still caught.
      `<li${m[1]}><label class="check"><input type="checkbox" data-check="${n === 1 ? base : `${base}~${n}`}"><span class="box" aria-hidden="true"></span><span class="lbl">${lead}</span></label>${walk(split.tail, s)}</li>`;
    last = after;
    open.lastIndex = after;
  }
  return out + html.slice(last);
}

export type BodySection = {
  /** The `<h2>`'s plain text, or null for whatever precedes the first heading. */
  label: string | null;
  id: string | null;
  /** The `<h2>` tag itself, re-emitted by the page when the section does not become a fold. */
  head: string;
  /** The section's compiled markdown BEFORE the rewrite. The page reads its fold decision off
   *  this, so making boxes tickable cannot change which sections fold (decision 38). */
  raw: string;
  html: string;
  task: boolean;
};

/** A chapter's compiled body: split at each `<h2>`, with every checklist in it made tickable
 *  UNDER ONE SCOPE.
 *
 *  THE SPLIT LIVES HERE BECAUSE THE SCOPE DOES. A chapter is not one call -- the body is several
 *  sections and a chapter can hold two checklists -- so whoever owns the loop owns the scope, and
 *  when `[slug].astro` owned it, it created a fresh `seen` map per section: two sections sharing
 *  a sentence both took the bare key, the tick spread between them on reload, and the duplicate
 *  warning never fired. Ticks live under one `pw-checked:<chapter-slug>`, so the scope is the
 *  chapter, and the only way to keep saying that is for the loop and the scope to be the same
 *  piece of code. The same reason `isTaskList` lives here rather than in the page.
 *
 *  It is also what `tools/qa/Checklist.mjs` drives, so the fixture tests the path the site runs
 *  instead of a second copy of it -- the copy is what let the scope bug ship.
 *
 *  `repeated` is the sentences seen more than once; `skipped` the items the rewrite declined. */
export function chapterBody(compiled: string): {
  sections: BodySection[];
  repeated: string[];
  skipped: string[];
} {
  const s: Scope = { seen: new Map(), repeated: [], skipped: [] };
  const sections = compiled
    .split(/(?=<h2[\s>])/)
    .filter((chunk) => chunk.trim())
    .map((chunk) => {
      const head = chunk.match(/^<h2\b[^>]*>([\s\S]*?)<\/h2>/);
      const raw = head ? chunk.slice(head[0].length) : chunk;
      const task = isTaskList(raw);
      return {
        label: head ? head[1].replace(/<[^>]+>/g, "").trim() : null,
        id: head?.[0].match(/\bid="([^"]*)"/)?.[1] ?? null,
        head: head?.[0] ?? "",
        raw,
        html: task ? walk(raw, s) : raw,
        task,
      };
    });
  return { sections, repeated: s.repeated, skipped: s.skipped };
}

/** Build-time checks against a chapter's own markdown, so the warning can name a line an author
 *  can go and edit. `- [x]` is the one worth catching: it renders as an ordinary empty box and
 *  says nothing at all, because the departure checklist belongs to the reader and always starts
 *  empty (decision 48). Silence is how this one feature has now gone wrong five times. */
export function checkSource(md: string, file: string): string[] {
  const out: string[] = [];
  md.split("\n").forEach((line, i) => {
    if (/^\s*[-*+]\s+\[[xX]\]/.test(line))
      out.push(
        `${file}:${i + 1}: checklist item written "- [x]" -- it never renders ticked, because the departure checklist belongs to the reader and always starts empty. Write it "- [ ]", or say the fact somewhere other than the checklist.`,
      );
  });
  return out;
}
