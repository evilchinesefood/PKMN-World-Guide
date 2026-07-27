// The departure checklist. Markdown's `- [ ]` compiles to `<input type="checkbox" disabled>` --
// a box drawn on the page that a reader cannot tick. This turns each item into a real control.
//
// IDENTITY IS THE ITEM'S OWN TEXT, NOT ITS POSITION IN THE LIST. Position is the obvious key and
// it is the wrong one: insert an item at the top and every tick below it slides onto the wrong
// line, and the brand-new item inherits whatever was ticked in its slot -- a checklist that
// silently marks work done the reader never did is worse than one that does not persist at all.
// Hashing the text cannot do that. A new item is a new key and starts unticked, and an item that
// merely moves keeps its tick. The cost is that rewording an item resets it, which is the honest
// failure of the two: the thing being asked has changed, so the reader should look again.
// Markup-only edits do not count -- tags are stripped and whitespace collapsed before hashing --
// so bolding a word or repointing a link leaves the tick alone.
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

// In a TIGHT item the sentence ends where the first nested list begins, and `<ul>`/`<ol>` is
// the whole set -- any other block under a checklist line forces the list LOOSE instead.
const NESTED = /<(?:ul|ol)\b/i;

/** An item's own sentence, and whatever the author put after it.
 *
 *  ONE RULE FOR BOTH SHAPES MARKDOWN PRODUCES. A list is LOOSE if there is a blank line
 *  anywhere in it, and a loose list wraps every item's text in a `<p>`; a tight one does not.
 *  An author does not choose between those on purpose -- they add a blank line for room to
 *  read -- so the two must not be two code paths. The sentence is the phrasing content
 *  following the checkbox INSIDE THE CHECKBOX'S OWN BLOCK, and the tail is every block after
 *  that one. Tight: the block is the `<li>` itself, so the sentence ends at the first nested
 *  list. Loose: the block is the `<p>`, so it ends at `</p>` and the tail is free to be another
 *  paragraph, a table or a list without any of those being named here.
 *
 *  Returns null for anything this does not recognise, which is then left exactly as it came in
 *  rather than half-rewritten. */
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
  const at = after.search(NESTED);
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
function walk(
  html: string,
  seen: Map<string, number>,
  twice: string[],
): string {
  const open = /<li([^>]*\btask-list-item[^>]*)>/g;
  let out = "";
  let last = 0;
  for (let m; (m = open.exec(html));) {
    const from = m.index + m[0].length;
    const bounds = closeOf(html, from);
    if (!bounds) continue; // Unbalanced source: leave the item exactly as it came in.
    const [shut, after] = bounds;
    const split = splitItem(html.slice(from, shut));
    if (!split) continue;
    const lead = split.lead.trim();
    const base = keyOf(lead);
    const n = (seen.get(base) ?? 0) + 1;
    seen.set(base, n);
    if (n === 2) twice.push(text(lead));
    out +=
      html.slice(last, m.index) +
      // The tail is walked too: a task list nested under a task item is still a checklist, and
      // it shares `seen`, so a duplicate across two nesting levels is still caught.
      `<li${m[1]}><label class="check"><input type="checkbox" data-check="${n === 1 ? base : `${base}~${n}`}"><span class="box" aria-hidden="true"></span><span class="lbl">${lead}</span></label>${walk(split.tail, seen, twice)}</li>`;
    last = after;
    open.lastIndex = after;
  }
  return out + html.slice(last);
}

/** The rewritten markup, plus any sentence that appears more than once in it -- the caller
 *  turns those into a build warning. One chapter is one `seen` scope, which is exactly the
 *  scope of the `pw-checked:<slug>` key the ticks live under. */
export function checklist(html: string): { html: string; repeated: string[] } {
  const repeated: string[] = [];
  return { html: walk(html, new Map(), repeated), repeated };
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
