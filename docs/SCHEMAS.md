# Generated JSON Schemas

Output contract for `tools/extract/` → `data/generated/`. One file per entity, per brief §5.

**Rules that apply to every file here.**

- **Determinism.** Same submodule commit in, byte-identical JSON out. Sort every array by a stable
  key, sort object keys, use `indent=1`, `ensure_ascii=False`, and never emit a timestamp or a
  wall-clock value.
- **Traceability.** Every record carries `source` — the file it came from, plus a line or key where
  that is meaningful. This is how the guide gets audited; it is not optional.
- **Never invent.** When source data is missing or ambiguous, emit `null` and add a `gap` entry
  naming the reason. Write the question to `DATA-AUDIT.md`. Do not fill from vanilla Pokémon
  knowledge — this game deviates from vanilla in many places and a plausible guess is worse than a
  visible hole.
- **Gating.** Every content chunk carries `gate` (a key from `progression.json`) and `severity`
  (`routine` | `story` | `endgame`). CI fails the build on any chunk without a gate.

## Shared types

```jsonc
// Attached to every record.
"source": {
  "file": "data/maps/Route102/map.json",  // repo-relative, inside game/
  "key":  "bg_events[3]",                  // JSON pointer-ish, or a line number for C/asm
  "line": null                             // int when the source is text, else null
}

// Attached wherever a value could not be determined.
"gap": {
  "field":  "underfoot",
  "reason": "absent from source; engine default not confirmed",
  "audit":  "Q6"                           // open-question id in DATA-AUDIT.md
}

// Region. `shared` covers maps that are region-neutral by design and would otherwise
// fall through to hoenn — the hub, secret bases, FRLG link rooms. See DATA-AUDIT.md Q4.
"region": "kanto" | "johto" | "hoenn" | "shared"

// Local to the map it belongs to, in blocks. Never global. Brief decision #6.
"coord": { "x": 12, "y": 7, "elevation": 3 }
```

**Why coordinates stay local:** 49 layouts are shared by 277 maps — one
`LAYOUT_POKEMON_CENTER_1F_FRLG` image backs 18 different maps with different NPCs and warps. Marker
positions must belong to the map, never to the image.

---

## `maps.json` — FINAL

Derived from 1194 `map.json` files. Key: `id` (verified unique 1194/1194).

```jsonc
{
  "id": "MAP_ROUTE102",
  "name": "Route 102",                  // display name, charmap-decoded
  "region": "hoenn",                    // via GetRegionForSectionId — see below
  "region_map_section": "MAPSEC_ROUTE_102",
  "layout": "LAYOUT_ROUTE102",
  "floor_number": null,                 // present on 422/1194
  "dimensions": { "width": 40, "height": 20 },   // blocks, from the layout
  "music": "MUS_ROUTE101",
  "weather": "WEATHER_SUNNY",
  "map_type": "MAP_TYPE_ROUTE",
  "battle_scene": "MAP_BATTLE_SCENE_NORMAL",
  "requires_flash": false,
  "allow_cycling": true, "allow_escaping": false, "allow_running": true,
  "show_map_name": true,

  "connections": [
    { "direction": "up", "offset": -12, "map": "MAP_VIRIDIAN_CITY" }
  ],

  "warps":        [ { "coord": {…}, "dest_map": "MAP_PETALBURG_CITY", "dest_warp_id": 0 } ],
  "object_events":[ { "local_id": 1, "graphics_id": "OBJ_EVENT_GFX_YOUNGSTER",
                      "coord": {…}, "movement_type": "MOVEMENT_TYPE_LOOK_AROUND",
                      "movement_range": { "x": 1, "y": 1 },
                      "trainer_type": "TRAINER_TYPE_NORMAL",
                      "trainer_sight_or_berry_tree_id": 4,
                      "script": "Route102_EventScript_Calvin", "flag": "0",
                      "kind": "object" } ],          // "object" | "clone"
  "signs":        [ { "coord": {…}, "player_facing_dir": "BG_EVENT_PLAYER_FACING_NORTH",
                      "script": "Route102_EventScript_RouteSign" } ],
  "hidden_items": [ { "coord": {…}, "item": "ITEM_POTION", "flag": "FLAG_HIDDEN_ITEM_ROUTE_102_POTION",
                      "quantity": 1, "underfoot": false } ],
  "secret_bases": [ { "coord": {…}, "secret_base_id": "SECRET_BASE_RED_CAVE1_1" } ],
  "coord_triggers":[{ "coord": {…}, "var": "VAR_TEMP_1", "var_value": "0",
                      "script": "…" } ],
  "weather_triggers":[{ "coord": {…}, "weather": "COORD_EVENT_WEATHER_RAIN" } ],

  "encounters": "MAP_ROUTE102",         // join key into encounters.json, or null
  "shared_events_from":  null,          // 11 maps inherit events; resolve before emitting
  "shared_scripts_from": null,          // 50 maps inherit scripts
  "gate": "hoenn:badge1",
  "severity": "routine",
  "source": {…}
}
```

**`region` is computed, never copied.** Replicate `GetRegionForSectionId` (`include/regions.h`):
read `src/data/region_map/region_map_sections.json` for ordinals (array order = enum order), then
Kanto if `[MAPSEC_PALLET_TOWN, MAPSEC_SPECIAL_AREA)` **exclusive**, Johto if
`[MAPSEC_NEW_BARK_TOWN, MAPSEC_JOHTO_INDIGO_PLATEAU]` **inclusive**, else Hoenn.
Do **not** use `map.json`'s `region` field (absent on all 162 Johto maps) and do **not** use
`KANTO_MAPSEC_END` (deliberately inclusive of `MAPSEC_SPECIAL_AREA` for an unrelated purpose).

**Flattening rules.** The source's four event arrays are split by discriminator into the seven
arrays above: `bg_events` → `signs` (1587) / `hidden_items` (298) / `secret_bases` (75);
`coord_events` → `coord_triggers` (932) / `weather_triggers` (86). `object_events` keeps its
discriminator as `kind`, defaulting to `"object"` when `type` is absent (present on only 1675/6859).

**`shared_events_from` must be resolved**, not passed through. The 11 Contest Halls reference a
*directory* name (`ContestHall`), not a `MAP_*` id.

---

## `encounters.json` — FINAL

One record per `(map, base_label)` pair — **not per map**: 479 entries resolve to 331 maps, and 125
maps carry more than one table (`MAP_SIX_ISLAND_ALTERING_CAVE` has 18). See `DATA-AUDIT.md` Q7.

```jsonc
{
  "map": "MAP_ROUTE102",
  "base_label": "gRoute102",            // disambiguates multi-table maps; part of the key
  "region": "hoenn",
  "methods": {
    "land": {
      "encounter_rate": 20,             // per-step chance; distinct from slot percentages
      "slots": [
        { "slot": 0, "percent": 20, "species": "SPECIES_POOCHYENA",
          "min_level": 3, "max_level": 3, "species_enabled": true }
      ],
      "percent_total": 100              // asserted == 100 by tools/validate
    },
    "fishing": {
      "encounter_rate": 30,
      "rods": {                         // from the JSON's own `groups` map — never hardcode
        "old_rod":   { "slots": [ … ], "percent_total": 100 },
        "good_rod":  { "slots": [ … ], "percent_total": 100 },
        "super_rod": { "slots": [ … ], "percent_total": 100 }
      }
    }
  },
  "gate": "hoenn:badge1",
  "severity": "routine",
  "source": {…}
}
```

Methods: `land` 12 slots · `water` 5 · `rock_smash` 5 · `fishing` 10 (2/3/5 by rod) ·
`hidden` 3 (DexNav). Percentages come from the `fields` array in `wild_encounters.json` itself —
`[20,20,10,10,10,10,5,5,4,4,1,1]` for land, `[60,30,5,4,1]` for water and rock smash,
`[60,35,5]` for hidden.

`tools/wild_encounters/wild_encounters_to_header.py` is the reference implementation; mirror it
rather than reinventing the parse. Only `gWildMonHeaders` is map-linked — skip
`gBattlePyramidWildMonHeaders` and `gBattlePikeWildMonHeaders`.

`species_enabled` guards against the disabled-species set: a species that is disabled must never be
presented as catchable.

---

## `map-manifest.json` — FINAL

`data/manifest/map-manifest.json`. The interface between image producer and site, per brief
decision #5. **Swapping the producer must require zero site changes**, so nothing here names
Porymap or the renderer.

One entry per map (1194) — but `image` is keyed by *layout*, so **966 distinct images** back them.

```jsonc
{
  "generator": { "name": "tools/porymap/render.py", "version": "1.0.0" },
  "game": { "tag": "v1.3.6", "commit": "87a66e89666da1621a869ba51b0bd7c76d1ea015" },
  "maps": [
    {
      "map_id": "MAP_ROUTE102",
      "layout_id": "LAYOUT_ROUTE102",
      "region": "hoenn",
      "block_width": 40, "block_height": 20,
      "pixel_width": 640, "pixel_height": 320,   // == block * 16, asserted
      "image": "maps/LAYOUT_ROUTE102.png",       // relative to public/; shared across maps
      "content_hash": "sha256:…"                 // of the source blockdata + tilesets, not the PNG
    }
  ]
}
```

`content_hash` covers the **inputs** (blockdata, both tilesets, palettes), not the output PNG, so
it stays stable across encoder changes and tells you when a re-render is genuinely needed.

`pixel_* == block_* * 16` is an invariant — assert it, don't trust it.

---

## Pending schemas

Shapes are not yet settled; the audits are still open. Deliberately left unwritten rather than
guessed, since a schema invented here would be exactly the "fill from general Pokémon knowledge"
failure the brief warns against.

- **`trainers.json`** — blocked on the `.party` grammar, the `TRAINER_*` id space across
  `trainers.party` and `trainers_frlg.party`, the trainer→map linkage chain, and how a HARD
  rematch is distinguished from a base trainer. **Must read both `.party` files** — see
  `DATA-AUDIT.md` §0.2.
- **`species.json`** — blocked on the disabled-species mechanism (which drives `obtainable_via`)
  and on evolution parameter semantics.
- **`items.json`** — blocked on the four `locations` sources and whether item data is region-split.
  Hidden items are already settled: 298 records, from `maps.json`.
- **`progression.json`** — blocked on badge flags, the obedience formula and the Hard Mode cap
  table. Partly hand-authored by design; entries carry `hand_authored: true`.
- **`systems.json`** — blocked on the `include/config/` inventory and the non-vanilla system
  survey.
