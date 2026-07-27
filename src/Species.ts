// The one place that answers "which species IS dex N".
//
// It used to be answered three times -- here, on the Pokédex index, and again in Python in
// tools/sprites/Extract.py -- by testing the id against a denylist of form suffixes
// (_MEGA, _ALOLA, _GMAX, ...). The three copies drifted, and dex 386 published a page titled
// Deoxys next to an index row and a sprite that were both Deoxys (Attack). The denylist was
// never sound anyway: six dex numbers have more than one id that survives it (25 Pikachu,
// 133 Eevee, 172 Pichu, 201 Unown, 901 Ursaluna, 982 Dudunsparce), so their base form was
// decided by the order species.json happened to list them in.
//
// `is_base_form` comes from the game's own `formSpeciesIdTable`, whose first entry is the
// base form (tools/extract/Species.py). The extractor asserts exactly one per dex number.

export function dexSlug(n: number) {
  return String(n).padStart(3, "0");
}

/** The base form among the enabled species sharing one national dex number. */
export function baseForm(forms: any[]) {
  const bases = forms.filter((s) => s.is_base_form);
  if (bases.length !== 1)
    throw new Error(
      `dex ${forms[0]?.national_dex}: ${bases.length} base forms among ${forms.map((s) => s.id).join(", ")}`,
    );
  return bases[0];
}
