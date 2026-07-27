// Rewrites applied to compiled-markdown HTML before it is rendered with set:html. Every page
// that renders a markdown body needs the same ones, so they live here rather than being
// re-typed per page -- a second copy is how the gate label in Names.ts drifted.

/** A six-column table is wider than a phone. Every table on this site scrolls inside its own
 *  box rather than scrolling the document sideways. The wrapper is used rather than
 *  `display: block` on the table itself because `table { width: 100% }` stops applying to a
 *  block-display table, and the reference tables are built to fill the column. */
export const scrollTables = (html: string) =>
  html.replace(
    /<table[\s\S]*?<\/table>/g,
    (t) => `<div class="scroll-x">${t}</div>`,
  );
