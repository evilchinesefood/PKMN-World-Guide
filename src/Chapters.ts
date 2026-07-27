// Three kinds of file live under content/ and only one of them is a chapter. An Insider Tips
// file declares `companion_to:` and a Technical notes file declares `technical_to:`; both name
// their chapter by repo path, and neither may generate a page of its own under /walkthrough/.
// Every page that walks the content tree goes through here so the three filters cannot drift.
//
// The relation is declared in ONE direction, by the companion. A chapter carries no forward
// key, so a chapter's companions are found by scanning for a pointer that resolves back to it.

const mods = import.meta.glob("/content/**/*.md", { eager: true }) as Record<
  string,
  any
>;

// Full paths, never basenames: kanto/RouteOne.md and johto/RouteOne.md are different files and
// a basename compare silently pairs the wrong ones the moment two regions share a chapter name.
const norm = (p: string) => "/" + String(p).replace(/^\/+/, "");

export const slugOfPath = (p: string) =>
  p.split("/").pop()!.replace(/\.md$/, "").toLowerCase();

export const isChapter = (m: any) =>
  !m?.frontmatter?.companion_to && !m?.frontmatter?.technical_to;

export function chapterEntries(): [string, any][] {
  return Object.entries(mods).filter(([, m]) => isChapter(m));
}

export function chapterBySlug(slug: string) {
  return chapterEntries().find(([p]) => slugOfPath(p) === slug);
}

function pointingAt(key: string, chapterPath: string) {
  const want = norm(chapterPath);
  return Object.entries(mods).filter(
    ([, m]) => m?.frontmatter?.[key] && norm(m.frontmatter[key]) === want,
  );
}

export function companionOf(chapterPath: string) {
  return pointingAt("companion_to", chapterPath)[0]?.[1] ?? null;
}

export function technicalOf(chapterPath: string) {
  return pointingAt("technical_to", chapterPath)[0]?.[1] ?? null;
}

// Every technical notes file, paired with the chapter it belongs to. The route lives at the
// CHAPTER's slug (/technical/pallettoviridian/), not the notes file's own.
export function technicalPages(): { slug: string; chapter: any; mod: any }[] {
  return Object.entries(mods)
    .filter(([, m]) => m?.frontmatter?.technical_to)
    .map(([, m]) => {
      const target = norm(m.frontmatter.technical_to);
      const chapter = chapterEntries().find(([p]) => norm(p) === target);
      // A dangling pointer would publish nothing and orphan the notes, silently.
      if (!chapter)
        throw new Error(
          `technical_to: ${m.frontmatter.technical_to} does not resolve to a chapter`,
        );
      return { slug: slugOfPath(chapter[0]), chapter: chapter[1], mod: m };
    });
}

// Two notes files pointing at one chapter would publish one and orphan the other, with no
// error anywhere. Checked at import so it fails the build, not a page.
{
  const seen = new Map<string, number>();
  for (const [, m] of Object.entries(mods)) {
    const t = m?.frontmatter?.technical_to;
    if (!t) continue;
    seen.set(norm(t), (seen.get(norm(t)) ?? 0) + 1);
  }
  const dupes = [...seen].filter(([, n]) => n > 1);
  if (dupes.length)
    throw new Error(
      `more than one technical_to resolves to: ${dupes.map(([p]) => p).join(", ")}`,
    );
}
