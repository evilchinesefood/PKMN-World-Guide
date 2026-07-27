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

// The whole item becomes the label, so the sentence is the hit target -- not a 12px box. The
// box and the tick are drawn in CSS on the <span>; the input itself is only kept for the state,
// the keyboard and the accessibility tree.
export function checklist(html: string): string {
  return html.replace(
    /<li([^>]*\btask-list-item[^>]*)>\s*<input[^>]*type="checkbox"[^>]*>([\s\S]*?)<\/li>/g,
    (_m, attrs, item) =>
      `<li${attrs}><label class="check"><input type="checkbox" data-check="${keyOf(item)}"><span class="box" aria-hidden="true"></span><span class="lbl">${item.trim()}</span></label></li>`,
  );
}
