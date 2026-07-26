// map.json's `name` is the containing folder name, not a display name, so titles are
// derived from the id instead. Route ids carry no region prefix and never collide --
// Kanto 1-25, Johto 26-48, Hoenn 101-134. See DATA-AUDIT.md 7.

export function slugOf(id: string) {
  return id.replace(/^MAP_/, "").toLowerCase().replaceAll("_", "-");
}

const SMALL = new Set(["of", "the", "and", "in", "to"]);

export function titleOf(id: string) {
  // ROUTE1 is one token, so split letter/digit before word-splitting or it renders "Route1".
  const raw = id.replace(/^MAP_/, "").replace(/([A-Z])(\d)/g, "$1_$2");
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

// SPECIES_POOCHYENA -> "Poochyena", MAP_TYPE_ROUTE -> "Route", land_mons -> "Land".
// Display names for species and moves come from battledata.json where a real one exists;
// this is only for constants the game never gives a display string.
export function prettyConst(v: string, prefix: string) {
  const s = (
    prefix && v.startsWith(prefix) ? v.slice(prefix.length) : v
  ).replace(/_mons$/, "");
  return s
    .split("_")
    .filter(Boolean)
    .map((w) => w.charAt(0).toUpperCase() + w.slice(1).toLowerCase())
    .join(" ");
}

// A gate is a FLOOR, never a sufficient condition (DATA-AUDIT Q19). Victory Road B1F
// carries hoenn:badge-2 only because the room is dark and Flash needs that badge, while
// the league's real eight-badge requirement lives on another map. So labels read "from X
// onwards" -- "requires X" would tell a reader with two badges that Victory Road is open.
export function gateLabel(gate: any) {
  if (!gate) return "Later in the game";
  const region = String(gate.region ?? "Global");
  const cap = region.charAt(0).toUpperCase() + region.slice(1);
  if (gate.always_available) return `${cap} — from the start`;
  // gate.label already carries the region ("Kanto badge 1"), so strip it to avoid
  // "Kanto — from Kanto badge 1 onwards".
  const what = String(gate.label ?? "").replace(
    new RegExp(`^${cap}\\s+`, "i"),
    "",
  );
  return `${cap} — from ${what} onwards`;
}
