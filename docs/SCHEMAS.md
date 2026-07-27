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

## `trainers.json` — FINAL

Key: **`(trainer_id, difficulty)`** — verified unique across all 1752 entries. Read **both**
`src/data/trainers.party` and `src/data/trainers_frlg.party` into one table.

```jsonc
{
  "trainer_id": 616,                    // resolved numeric id, the real key
  "constant": "TRAINER_LYLE",           // provenance only — NOT evidence of identity, see below
  "difficulty": "normal",               // "normal" | "hard"
  "name": "LORELEI",                    // from Name: — this is the truth
  "class": "Elite Four Frlg",
  "pic": "Elite Four Lorelei Frlg",
  "gender": "Male",
  "music": "Elite Four",
  "double_battle": false,
  "items": ["ITEM_FULL_RESTORE", "ITEM_FULL_RESTORE"],
  "ai_flags": ["Check Bad Move", "Try To Faint", "Check Viability"],
  "mugshot": "Purple",

  "placement": {
    "map": "MAP_PETALBURG_WOODS",       // via map.json -> script -> trainerbattle_*
    "region": "hoenn",                  // from the MAP, never from the source file or id range
    "coord": { "x": 7, "y": 32, "elevation": 3 },
    "via": "map_script"                 // "map_script" | "rematch_table" | "c_code" | "unreferenced"
  },

  "party": [
    { "species": "SPECIES_DEWGONG", "level": 64,
      "ivs": { "hp": 31, "atk": 31, "def": 31, "spa": 31, "spd": 31, "spe": 31 },
      "evs": null,                      // NEVER 0 — see below
      "nature": null, "ability": "Thick Fat", "held_item": null,
      "moves": ["MOVE_SURF", "…"], "moves_are_default": false }
  ],

  "flags": { "defeat_flag": "…" },      // computed by TrainerIdToDefeatFlag(), not stored
  "anomaly": "frlg_boss_in_hoenn_slot", // null normally; set for the 22 hijacked slots
  "gate": "hoenn:badge1", "severity": "routine",
  "source": { "file": "src/data/trainers.party", "line": 15234 }
}
```

**`evs` and `nature` must be `null`, never `0`/`"Hardy"`.** Those keys are used **zero times** in
both trainer files, so the values a naive reader would print come from the engine, not the author.
`level` and `ivs` are present on all 4334 mons and are always safe.

**`constant` is not identity.** 22 entries carry a Kanto boss party under an ordinary route-trainer
constant (`DATA-AUDIT.md` §0.5). Render from `name`/`class`/`pic`; set `anomaly` so the site can
suppress or annotate them per Q10.

**Exclude** `debug_trainers.party` (`DEBUG_TRAINER_*`, separate array) and `test/battle/*.party`.
`battle_partners.party` is a different namespace (`PARTNER_*`). The 315 Battle Frontier trainers —
including the 15 World Championship ids — are **pool-based with no fixed party** and need a
separate record shape; do not force them into this one.

Parser notes: 160 `trainerbattle_*` calls omit the comma between arguments — match
`trainerbattle\w*\s+(TRAINER_\w+)`. `Class:`, `Music:` and `AI:` each appear in two vocabularies
(human-readable and raw `TRAINER_CLASS_*`/`AI_FLAG_*`). Filter `TRAINER_NONE` (id 0).

## `progression.json` — FINAL

Drives every `gate` key in every other file. Partly hand-authored by design.

```jsonc
{
  "gates": [
    { "key": "hoenn:badge1", "region": "hoenn", "order": 1, "severity": "routine",
      "label": "Stone Badge",
      "flag": "FLAG_BADGE01_GET",
      "earned_at": { "map": "MAP_RUSTBORO_CITY_GYM", "trainer_id": 265 },
      "hand_authored": false,
      "source": { "file": "data/maps/RustboroCity_Gym/scripts.inc", "line": 88 } },

    { "key": "global:champion-any", "region": null, "order": 100, "severity": "endgame",
      "label": "Champion of any region",
      "rule": "IsNRegionChampion(1)",
      "unlocks": ["Battle Frontier", "Eon Ticket", "DexNav detector mode"],
      "hand_authored": true,          // semantics live in C, not in any script
      "source": { "file": "src/region_switch.c" } }
  ],

  "badge_banks": {                    // three isolated banks behind one API — NOT one 24-flag range
    "hoenn": { "base": "FLAG_BADGE01_GET", "storage": "SaveBlock1.flags" },
    "kanto": { "base": "0xA4B", "storage": "SaveBlock1.flags" },
    "johto": { "base": "0x63F8", "storage": "SaveBlock3.johtoFlags" }
  },

  "obedience": {                      // by CURRENT-REGION badge INDEX, outsider mons only
    "levels": [10, 20, 30, 40, 50, 60, 70, 80, null],
    "note": "index-tested, not counted; badge 8 alone grants full obedience",
    "hand_authored": true,
    "source": { "file": "src/battle_util.c", "line": 5569 } },

  "level_caps": {                     // HARD MODE ONLY — MAX_LEVEL otherwise
    "per_badge": [15, 19, 24, 29, 31, 33, 42, 46],
    "eight_badges": 58, "champion": 100,
    "hard_mode_only": true,
    "exp_at_cap": 0,
    "hand_authored": true,
    "source": { "file": "src/caps.c", "line": 10 } },

  "region_order": null                // there is none — any region, any time. See DATA-AUDIT 5B.4
}
```

**Do not emit EV caps.** `B_EV_CAP_TYPE = EV_CAP_NONE`; the `sEvCapPerBadge` table never fires.

**Do not conflate Hard Mode with `VAR_DIFFICULTY`.** Hard Mode is global and permanent (a 1-bit
save field chosen once at new game); `VAR_DIFFICULTY` is per-region and re-synced on region entry.

Expect **60-100** `hand_authored: true` entries: the ~15 `callnative RegionHub_Scr*` semantics, the
C rule tables above, and region-level story ordering (which lives in `VAR_*_STATE` counters and
would need whole-program dataflow to recover).

## Still pending

- **`species.json`** — mostly determined (enablement test in `DATA-AUDIT.md` §5A, evolution
  semantics in §9.5), but `obtainable_via` needs the encounter/trainer/script cross-reference built
  first to separate "evolution-only" from "unreachable". Write it after the first extractor pass.
  One field is settled and load-bearing: **`is_base_form`** (bool) is true for the species that
  *is* its national dex number — the first entry of the `formSpeciesIdTable` it points at, or the
  species itself when it has no alternate forms. Exactly one enabled species per dex number
  carries it (asserted in `Species.verify`), and it is the ONLY source for that choice; do not
  re-derive it from a denylist of id suffixes, which is what published Deoxys (Attack) as dex 386.
- **`items.json`** — field data is settled and single-source; the `locations` array is blocked on
  Q14 (config ternaries) and needs the three-mechanism ground-item resolver in §9.1.
- **`systems.json`** — **blocked on Q1.** More than half the systems brief §5 lists do not exist at
  the current pin; the schema depends on which commit the guide tracks.
