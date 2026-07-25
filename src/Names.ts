// map.json's `name` is the containing folder name, not a display name, so titles are
// derived from the id instead. Route ids carry no region prefix and never collide --
// Kanto 1-25, Johto 26-48, Hoenn 101-134. See DATA-AUDIT.md 7.

export function slugOf(id: string) {
  return id.replace(/^MAP_/, "").toLowerCase().replaceAll("_", "-");
}

const SMALL = new Set(["of", "the", "and", "in", "to"]);

export function titleOf(id: string) {
  const raw = id.replace(/^MAP_/, "");
  return raw
    .split("_")
    .map((w, i) => {
      if (/^\d+[A-Z]?$/.test(w)) return w; // 1F, B2F, 102
      const l = w.toLowerCase();
      if (i > 0 && SMALL.has(l)) return l;
      return l.charAt(0).toUpperCase() + l.slice(1);
    })
    .join(" ")
    .replace(/\bRoute (\d+)/, "Route $1");
}
