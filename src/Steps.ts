// The chapter `sections:` schema, normalised once for every renderer that consumes it.
// The written contract is content/kanto/PalletToViridianTechnical.md, "Chapter `sections:`
// schema"; M5's three regions, 24 boss pages and three leagues are authored against it.
//
// Bad content degrades, it never throws. A renderer that dies on a malformed step takes the
// whole build down over one line of YAML, which is worse than a step that renders plainly.

export interface Step {
  // Rendered position in the section, 1-based. This is `data-step`, and the map layer reads
  // the same attribute for its pin, so the numeral by the sentence and the numeral on the map
  // cannot drift. Numbering never restarts or collapses inside a choice group: all three
  // starter balls are simultaneously real places on the map and each needs its own pin.
  n: number;
  text: string;
  at: [number, number] | null;
  // Set only on a real group -- two or more consecutive alternatives sharing a slug.
  group: string | null;
  // The renderer's label, on the first member of a group only. Null on an unrecognised
  // `choice` value: the run still groups, it just goes unlabelled, which is what keeps the
  // contract forward compatible.
  label: string | null;
}

const LABELS: Record<string, string> = {
  pick: "Pick one:",
  true: "Pick one:", // deprecated alias for `pick`
  depends: "Depending on your starter:",
};

// `choice: false` is forbidden and treated as absent -- one spelling of "not a choice".
const kindOf = (v: unknown): string | null => {
  if (v === true) return "true";
  if (typeof v !== "string" || !v || v === "false") return null;
  return v;
};

const coord = (v: unknown): [number, number] | null =>
  Array.isArray(v) &&
  v.length === 2 &&
  v.every((c) => Number.isFinite(Number(c)))
    ? [Number(v[0]), Number(v[1])]
    : null;

export function sectionsOf(fm: any): any[] {
  return Array.isArray(fm?.sections) ? fm.sections : [];
}

export function stepsOf(section: any): Step[] {
  const raw: unknown[] = Array.isArray(section?.steps) ? section.steps : [];

  const parsed = raw.map((s: any) => {
    if (typeof s === "string")
      return { text: s, at: null, kind: null, group: null as string | null };
    const kind = kindOf(s?.choice);
    // `choice_group` without `choice` is forbidden and ignored; `choice` without a group has
    // nothing to join, so it degrades to an ordinary step rather than labelling itself.
    const group =
      kind && typeof s?.choice_group === "string" && s.choice_group
        ? s.choice_group
        : null;
    return {
      text: String(s?.text ?? ""),
      at: coord(s?.at),
      kind: group ? kind : null,
      group,
    };
  });

  // A group is a MAXIMAL RUN of consecutive steps sharing one slug, so two adjacent groups
  // with different slugs stay two groups and the same slug used twice with a step between
  // stays two groups. A section boundary ends a run by construction -- this reads one
  // section. A run of one is invalid content ("Pick one:" over a single option); render it as
  // an ordinary step rather than crashing or labelling it.
  const out: Step[] = [];
  for (let i = 0; i < parsed.length; i++) {
    let run = 1;
    if (parsed[i].group)
      while (
        i + run < parsed.length &&
        parsed[i + run].group === parsed[i].group
      )
        run++;
    for (let k = 0; k < run; k++) {
      const p = parsed[i + k];
      const grouped = run > 1;
      out.push({
        n: i + k + 1,
        text: p.text,
        at: p.at,
        group: grouped ? p.group : null,
        label: grouped && k === 0 ? (LABELS[p.kind!] ?? null) : null,
      });
    }
    i += run - 1;
  }
  return out;
}
