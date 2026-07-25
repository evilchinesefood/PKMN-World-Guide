# Data Audit — M0

**Game pin:** `game/` submodule at tag **v1.3.6** = commit `87a66e89`
**Audited:** 2026-07-24
**Method:** every number below was produced by running code against the pinned tree. Nothing here
is inferred from vanilla Pokémon knowledge or from the game's documentation. Where something could
not be confirmed from a real file it is marked **unknown** rather than guessed.

> **Read §0 first.** Two of the brief's stated decisions turn out to be wrong against the real
> repo, and one failure mode can produce a guide that is missing an entire region while every
> completeness check reads 100%.

---

## 0. Headline findings

### 0.1 The tag `v1.3.6` did not exist — it was created for this project

The brief says pin to "the current tag, `v1.3.6`". The repo carried only `v1.0-beta` and four
`backup/*` tags. `v1.3.6` was named in `README.md` and `CHANGELOG.md` but never git-tagged.

It was created at `87a66e89` ("docs: polish README + FEATURES for public release", 2026-07-13),
which is the exact boundary: at that commit `README.md` reads `**v1.3.6**` and the top
`CHANGELOG.md` section is `## v1.3.6 — 2026-07-13` with nothing unreleased above it.

**Consequence: the pin is ~30 commits behind `master`.** Content merged after it — the Orange
Islands, the Jessie & James region ambushes, the World Championship Dome entry, save format v7 —
is **out of scope for the guide at this pin**. See open question **Q1**.

### 0.2 Kanto lives in parallel source files — the project's top correctness hazard

**3166 tracked files match `frlg`.** This hack did not merge Kanto into the Hoenn data; it keeps
Kanto in parallel `*_frlg` files:

- `src/data/trainers_frlg.party` (14,300 lines) alongside `src/data/trainers.party` (24,669)
- `data/scripts/`: `item_ball_scripts_frlg.inc`, `move_tutors_frlg.inc`, `trainers_frlg.inc`,
  `day_care_frlg.inc`, `cable_club_frlg.inc`, `fame_checker_frlg.inc`, `hall_of_fame_frlg.inc`,
  `pkmn_center_nurse_frlg.inc`, `trainer_card_frlg.inc`
- `data/text/`: `ingame_trade_frlg.inc`, `new_game_intro_frlg.inc`, and others
- large sets under `data/tilesets/` and `graphics/`

Johto arrived by a different route again — see `asm/macros/johto_compat.inc`.

**The failure mode:** an extractor that reads only the obvious file for an entity emits a guide
missing all of Kanto — **and `docs/COMPLETENESS.md` still reads 100%**, because every map it knew
about had its data. The ledger as specified in brief §9 cannot detect this.

**Required mitigation:** `tools/validate/` must carry **per-region cardinality assertions**
("Kanto has ≥ N trainers", "each region has ≥ 1 gym leader page") or the ledger is decorative.
This is not optional and should land with the first extractor, not at M4.

Encounters are the exception: single-source, confirmed. See §4.

### 0.3 Porymap cannot render this project — brief decision #4 is wrong

Not "no batch export" — **no correct export at all in a single configuration.**

`data/layouts/layouts.json` carries a `layout_version` per layout, and the engine switches the
tileset geometry on it at runtime (`src/fieldmap.c:429-441`):

```c
u32 GetNumMetatilesInPrimary(struct MapLayout const *mapLayout)
{
    return (mapLayout->isFrlg || mapLayout->isJohto) ? NUM_METATILES_IN_PRIMARY_FRLG : NUM_METATILES_IN_PRIMARY;
}
```

| `layout_version` | layouts | primary split (tiles/metatiles/pals) | attr bytes/metatile |
| --- | ---: | --- | ---: |
| `emerald` | 441 | 512 / 512 / 6 | 2 |
| `frlg` | 345 | 640 / 640 / 7 | 4 |
| `johto` | 254 | 640 / 640 / 7 | **2** |

Verified from real file sizes (`metatiles.bin` is 16 B per metatile):

```
primary/general        8192 B ( 512 mt)   attrs 1024 B  => 2 B/mt
primary/general_frlg  10240 B ( 640 mt)   attrs 2560 B  => 4 B/mt
primary/johto_general 10240 B ( 640 mt)   attrs 1280 B  => 2 B/mt
```

Attribute size branches on `isFrlg` **only** — `ExtractMetatileAttribute(u32, u8, bool32 isFrlg)`
at `src/fieldmap.c:492`, called `TRUE` at :522 and `FALSE` at :548. So **Johto = the FRLG split
with the Emerald attribute size**, and Porymap models both as *global* project settings.

The repo ships `.dev_scripts/PorymapFrlg.sh` and `PorymapEmerald.sh` to flip that config, and
**neither produces the Johto combination**. On top of that, Porymap 6.3.1 has no CLI
(`src/main.cpp` is 22 lines, `argv` straight to `QApplication`, no parser) and its scripting API
has **no export function and no way to open a different map**, so a scripted loop is impossible in
principle.

**Conclusion: the Python renderer is required, not deferred.** This *removes* M4's human hand-off
rather than adding work — see §7 for the renderer spec and open question **Q2**.

---

## 1. Scale

| metric | value |
| --- | ---: |
| `data/maps/*/map.json` | **1194** |
| distinct layouts referenced by live maps | **966** |
| layouts defined in `data/layouts/layouts.json` | 1040 |
| layout directories on disk | 1058 |
| layouts defined but referenced by no live map | 74 |
| maps with no layout | 0 |
| layouts referenced but not defined | 0 |
| map ids unique / total | **1194 / 1194** |
| MAPSEC entries | 266 |
| object events | 6859 |
| warp events | 3432 |
| coord events | 1018 |
| bg events | 1960 (1587 sign, **298 hidden item**, 75 secret base) |
| map connections | 366 |
| encounter entries | 479 across 331 distinct maps |

The brief's "~1200 maps / 1061 layouts" describes `master`, not this pin.

**Map id is a safe primary key** — 1194 unique out of 1194.

**966 images cover all 1194 map pages.** 49 layouts are shared by 277 maps
(`LAYOUT_POKEMON_CENTER_2F_FRLG` ×18, `LAYOUT_POKEMON_CENTER_1F_FRLG` ×17,
`LAYOUT_POKEMON_CENTER_2F` ×17, `LAYOUT_HOUSE3_FRLG` ×15, `LAYOUT_MART` ×13, …). This confirms
brief decision #6: **marker coordinates must stay local to each map**, because one image backs up
to 18 different maps carrying different NPCs, warps and items.

---

## 2. Region partitioning — SOLVED, 100% static coverage

This was the brief's hardest open question. It is not a heuristic and does not need hand-authoring.

**The game computes it**, `include/regions.h`:

```c
static inline enum Region GetRegionForSectionId(u32 sectionId)
{
    if (sectionId >= KANTO_MAPSEC_START && sectionId < MAPSEC_SPECIAL_AREA)
        return REGION_KANTO;
    if (sectionId >= JOHTO_MAPSEC_START && sectionId <= JOHTO_MAPSEC_END)
        return REGION_JOHTO;
    return REGION_HOENN;
}
```

Ranges from `src/data/region_map/region_map_sections.constants.json.txt`:
`KANTO_MAPSEC_START = MAPSEC_PALLET_TOWN` (ordinal 88), Kanto's upper bound is
`MAPSEC_SPECIAL_AREA` (192) **exclusive**; `JOHTO_MAPSEC_START = MAPSEC_NEW_BARK_TOWN` (209) to
`JOHTO_MAPSEC_END = MAPSEC_JOHTO_INDIGO_PLATEAU` (265) **inclusive**; everything else Hoenn.

**Extractor recipe:** read `src/data/region_map/region_map_sections.json` (the MAPSEC enum is
generated from it in array order, so ordinal = index), then apply the ranges to each map's
`region_map_section`.

**Result: Hoenn 524, Kanto 416, Johto 254 = 1194/1194, zero unassigned.**

### 2.1 Three traps

1. **`KANTO_MAPSEC_END` is not the Kanto bound.** It is deliberately defined *inclusive* of
   `MAPSEC_SPECIAL_AREA` for the map-name-popup discard range, while `GetRegionForSectionId` uses
   an *exclusive* bound. The source comment says so explicitly. Using `KANTO_MAPSEC_END` is a bug.
2. **Do not use `map.json`'s `region` field.** It exists on 1032/1194 maps and looks like the
   obvious answer. It is **absent on 162 maps — all Johto** — so it would drop the entire ported
   region. Where present it agrees with the MAPSEC rule on 1027/1032; the 5 disagreements are the
   FRLG link rooms (`MAP_UNION_ROOM_FRLG`, `MAP_TRADE_CENTER_FRLG`, `MAP_RECORD_CORNER_FRLG`,
   `MAP_BATTLE_COLOSSEUM_2P_FRLG`, `MAP_BATTLE_COLOSSEUM_4P_FRLG`), which is precisely the case
   the `MAPSEC_SPECIAL_AREA` comment documents. The MAPSEC rule matches runtime; the field does not.
3. **A tileset-based rule is wrong.** Bucketing by primary tileset disagrees on 35 maps —
   `MAP_JOHTO_VICTORY_ROAD_{1F,B1F,B2F}` use a Hoenn tileset, `MAP_NATIONAL_PARK_*` use an FRLG
   tileset — and leaves the 24 Secret Bases unassigned. Recorded so nobody retries it.

### 2.2 Two different region concepts — do not conflate

- `GetCurrentRegion()` — derived from the map you are standing on. **This is what the guide wants.**
- `GetActiveRegion()` / `gCurrentRegion` / `SaveBlock2.currentRegion` — the active *campaign*,
  whose badges and obedience govern the travelling party. Differs only inside the hub.
  Gated on `#if ALL_REGIONS`.

### 2.3 Kanto has sub-regions — Sevii is present

`enum KantoSubRegion { KANTO, SEVII123, SEVII45, SEVII67 }` with `GetKantoSubregion(mapSecId)`,
and region-map layouts `region_map_layout_sevii{123,45,67}.h`. **The atlas may need more than three
views.** See open question **Q5**.

### 2.4 Region-neutral maps fall through to Hoenn

`MAP_REGION_HUB` (the World Transit hub), the 24 `MAP_SECRET_BASE_*` (`MAPSEC_SECRET_BASE`), and
the 5 FRLG link rooms all classify as Hoenn because they fall through. None are single-player guide
content. Recommend the extractor emit a fourth value, `shared`. See open question **Q4**.

---

## 3. `map.json` — confirmed shape

Census across all 1194 files.

**Universal (1194/1194):** `id`, `name`, `layout`, `music`, `region_map_section`, `requires_flash`,
`weather`, `map_type`, `allow_cycling`, `allow_escaping`, `allow_running`, `show_map_name`,
`battle_scene`

**Optional:** `connections` 1184 · `object_events` / `warp_events` / `coord_events` / `bg_events`
1183 each · `region` 1032 (do not use — §2.1) · `floor_number` 422 · `shared_scripts_map` 50 ·
`shared_events_map` 11 · `connections_no_include` 1

| array | total | fields and discriminator |
| --- | ---: | --- |
| `object_events` | 6859 | `graphics_id`,`x`,`y` universal; `elevation`, `movement_type`, `movement_range_x/y`, `trainer_type`, `trainer_sight_or_berry_tree_id`, `script`, `flag` on 6850; `type` on only 1675 (**1666 `object` + 9 `clone`** — absence means `object`); `local_id` 742; `target_local_id`/`target_map` 9 |
| `warp_events` | 3432 | `x`, `y`, `elevation`, `dest_map`, `dest_warp_id` — all universal |
| `coord_events` | 1018 | **932 `trigger`** (`var`, `var_value`, `script`) + **86 `weather`** (`weather`) |
| `bg_events` | 1960 | **1587 `sign`** (`player_facing_dir`, `script`) + **298 `hidden_item`** (`item`, `flag`; 183 also `quantity` + `underfoot`) + **75 `secret_base`** (`secret_base_id`) |
| `connections` | 366 | `map`, `offset`, `direction` — left 91, right 91, up 85, down 85, **dive 7, emerge 7** |

### 3.1 Hidden items — 298 total

The ledger target for the hidden-item overlay is **298**. They are `bg_events` with
`type: "hidden_item"`, carrying `item` and `flag`.

**Only 183 of 298 carry `quantity` and `underfoot`.** The extractor must not invent defaults for
the other 115 — see open question **Q6**.

### 3.2 `shared_events_map` / `shared_scripts_map` — an extractor trap

50 maps borrow another map's scripts and 11 borrow its events. An extractor reading only each
map's own arrays renders those 11 as empty.

All 11 `shared_events_map` users are Contest Halls inheriting from **`ContestHall`** — and note
that is a *directory* name, not a `MAP_*` id, so the reference resolves by folder:
`MAP_CONTEST_HALL_{COOL,BEAUTY,CUTE,SMART,TOUGH}` plus `MAP_UNUSED_CONTEST_HALL{1..6}`.
Six of the eleven are dead Emerald content. Small blast radius, but must be handled.

---

## 4. Wild encounters — single-source, rates fully data-driven

**`src/data/wild_encounters.json` is the only encounter source.** `src/data/wild_encounters.h`
does not exist; it is an `AUTO_GEN_TARGET` produced by
`tools/wild_encounters/wild_encounters_to_header.py` (`Makefile:257-265`), which also consumes
`include/config/overworld.h` and `include/config/dexnav.h`.

**That generator is the reference implementation — the extractor should mirror it rather than
reinvent the parse.** The §0.2 region-split hazard does **not** apply here.

### 4.1 Rates are in the data, not hardcoded in C

They live in the JSON's own `fields` array (generator line 96), so brief §9's "rates summing to
100 percent per method" is directly satisfiable. Verified:

| method | slots | rates | sum |
| --- | ---: | --- | ---: |
| `land_mons` | 12 | 20, 20, 10, 10, 10, 10, 5, 5, 4, 4, 1, 1 | **100** |
| `water_mons` | 5 | 60, 30, 5, 4, 1 | **100** |
| `rock_smash_mons` | 5 | 60, 30, 5, 4, 1 | **100** |
| `fishing_mons` | 10 | see below | 300 |
| `hidden_mons` | 3 | 60, 35, 5 | **100** |

Fishing carries an explicit `groups` mapping, so **no hardcoded rod split is needed**:
`old_rod` slots `[0,1]` = 100 · `good_rod` `[2,3,4]` = 100 · `super_rod` `[5,6,7,8,9]` = 100.

Slot counts (`include/constants/wild_encounter.h`): `LAND_WILD_COUNT 12`, `WATER_WILD_COUNT 5`,
`ROCK_WILD_COUNT 5`, **`FISH_WILD_COUNT 10`** (not vanilla's 12), `HIDDEN_WILD_COUNT 3`.

### 4.2 Johto IS covered — the brief's explicit question

| region | maps with encounter data | of total maps |
| --- | ---: | ---: |
| Kanto | 124 | 416 |
| **Johto** | **91** | 254 |
| Hoenn | 116 | 524 |

All five methods appear in all three regions. Zero references to maps that do not exist.

### 4.3 Groups and per-entry shape

Three groups: `gWildMonHeaders` (479 entries, `for_maps: true` — the only map-linked one),
`gBattlePyramidWildMonHeaders` (7), `gBattlePikeWildMonHeaders` (4).

```json
{ "map": "MAP_ROUTE102", "base_label": "gRoute102",
  "land_mons": { "encounter_rate": 20,
    "mons": [ { "min_level": 3, "max_level": 3, "species": "SPECIES_POOCHYENA" }, … ] },
  "water_mons": { "encounter_rate": 4, "mons": [ … ] },
  "fishing_mons": { … } }
```

`encounter_rate` is the per-method step-encounter chance and is **distinct from** the slot
percentages in §4.1. Both are needed to present a correct table.

### 4.4 125 maps have more than one encounter entry

479 entries resolve to 331 distinct maps. Duplicates are disambiguated by `base_label`:
`MAP_SIX_ISLAND_ALTERING_CAVE` ×18 (9 tables × FireRed/LeafGreen), `MAP_ALTERING_CAVE` ×9, the
Tanoby Ruins chambers ×2 each. See open question **Q7**.

---

## 5. Trainers — authoritative source settled

**`src/data/trainers.h` does not exist at this tag.** It is a build artifact:
`trainer_rules.mk:4` lists it under `AUTO_GEN_TARGETS`, `.gitignore:65` ignores it, and the rule is

```make
%.h: %.party $(TRAINERPROC)
	$(CPP) $(CPPFLAGS) -traditional-cpp - < $< | $(TRAINERPROC) -o $@ -i $< -
```

So **`.party` is the source**, compiled by `tools/trainerproc/`. The brief's "verify which" is
answered.

> Note: an `ls` against the `/mnt/c` working tree *does* show `trainers.h`. That is an untracked
> build output in a dirty tree, not repo content. **Audit against the pinned checkout only.**

Authored trainer sources:

| file | lines |
| --- | ---: |
| `src/data/trainers.party` | 24,669 |
| `src/data/trainers_frlg.party` | 14,300 |
| `src/data/battle_partners.party` | 44 |
| `src/data/debug_trainers.party` | 68 |
| `test/battle/trainer_control.party` | 295 |
| `test/battle/partner_control.party` | 69 |

*(Party grammar, id-space, map linkage, HARD rematches and roster enumeration: pending — see §9.)*

---

## 5A. Species enablement — the roster is 274 families, not 539

This drives `obtainable_via` and the "every obtainable species has a documented acquisition
method" ledger target, so it is settled here rather than left pending.

`include/config/species_enabled.h` defines **539** `P_FAMILY_*` toggles. All nine
`P_GEN_N_POKEMON` macros read `TRUE`, but 265 families are overridden to a literal `FALSE`:

```c
#define P_FAMILY_TURTWIG   FALSE // world-strip: unreferenced in all 3 campaigns (was P_GEN_4_POKEMON)
```

| | families |
| --- | ---: |
| **Enabled** | **274** |
| — via `P_GEN_1_POKEMON` | 77 |
| — via `P_GEN_2_POKEMON` | 51 |
| — via `P_GEN_3_POKEMON` | 72 |
| — Gen 4-9 survivors | **74** |
| **Disabled** ("world-strip") | **265** |
| — was Gen 4 / 5 / 6 | 32 / 76 / 32 |
| — was Gen 7 / 8 / 9 | 38 / 22 / 65 |

**Extractor test:** a species is enabled iff its `P_FAMILY_*` is not literal `FALSE`. Parse
`include/config/species_enabled.h`; treat any `P_GEN_N_POKEMON` value as enabled (all nine are
`TRUE` at this tag — re-check if the pin moves).

**The carve-out is broader than "cross-generation evolutions."** The comment's rule is
*referenced anywhere in the three campaigns*, so the 74 survivors include every generation's
starter lines (Froakie; Rowlet, Litten, Popplio; Grookey, Scorbunny, Sobble) and a large
legendary set (Dialga, Palkia, Arceus, the four Tapus, Necrozma, Eternatus, Calyrex, Ogerpon,
Terapagos, …). The guide's species index therefore covers **274 families**, and a disabled
species must never be presented as obtainable — referencing one crashes the game at battle
send-out.

> **Correction to prior project notes.** Those notes record "disabling 74 unreferenced Gen 4-9
> families". At this tag the disabled count is **265**; **74** is the number of Gen 4-9 families
> that *survived*. The notes also cite `Testing/ValidateGen13.py` — **that file does not exist at
> v1.3.6**; the whole `Testing/` directory is absent. It is `master` content, referenced by the
> `pre-push` hook in the working tree. Any validation the guide wants must be written fresh.

## 6. Connections compose correctly — brief decision #6 validated

Offsets are in **blocks**, measured along the axis perpendicular to the connection direction, and
reciprocal pairs negate:

```
MAP_ROUTE1        up(-12) -> MAP_VIRIDIAN_CITY
MAP_VIRIDIAN_CITY down(12) -> MAP_ROUTE1
```

Checked all 366: **360 are perfectly reciprocal and negated.** Leaflet `CRS.Simple` composition
from these offsets is sound.

**All 6 anomalies are one cluster — Saffron City — and it is not a data bug:**

| map | layout | size | events |
| --- | --- | --- | --- |
| `MAP_SAFFRON_CITY` | `LAYOUT_SAFFRON_CITY` | 66×55 | 15 objects, 15 warps, 9 bg |
| `MAP_SAFFRON_CITY_CONNECTION` | `LAYOUT_SAFFRON_CITY_CONNECTION` | 48×40 | **0 / 0 / 0** |

Both carry `MAPSEC_SAFFRON_CITY` and both declare the same four outbound connections to Routes
5/6/7/8 — but Routes 5-8 connect *back* to the `_CONNECTION` stub. This is the stock FRLG
placeholder standing in for Saffron before the player can enter. It is the only `*_CONNECTION` map
in the repo. See open question **Q8**.

---

## 7. Map images — renderer specification

Since Porymap is ruled out (§0.3), here is what a Python renderer needs. Reference implementation
is Porymap's own source: `src/core/maplayout.cpp` (`Layout::render`, ~line 362) and
`src/ui/imageproviders.cpp` (`getMetatileImage`, ~line 56).

Output is **1:1 at 16 px per block** — `Metatile::pixelWidth() == 16`, so a 30-block-wide map
produces exactly a 480 px PNG. That matches the brief's requirement with no scaling.

- **blockdata** `data/layouts/<Name>/map.bin` — flat `width * height` little-endian `uint16`,
  row-major, no header. Masks: metatile `0x03FF`, collision `0x0C00`, elevation `0xF000`.
  Only the metatile id matters for rendering.
- **block → metatile** — `id < NUM_METATILES_PRIMARY` → primary at `id`, else secondary at
  `id - NUM_METATILES_PRIMARY`. **The split depends on `layout_version`** (§0.3); hardcoding it
  corrupts roughly two thirds of the maps.
- **metatile** — 16 bytes at `index * 16` = 8 tiles. Triple-layer is off.
- **tile word** (LE `uint16`) — `tileId` bits 0-9, `xflip` bit 10, `yflip` bit 11,
  `palette` bits 12-15.
- **compositing** — 3 layers × 4 quadrants = **12 draws from 8 stored tiles**. The missing 4 come
  from `layerType` in `metatile_attributes.bin`: Normal `[unused, 0-3, 4-7]`,
  Covered `[0-3, 4-7, unused]`, Split `[0-3, unused, 4-7]`. Draw 0→1→2, quadrant at `(x*8, y*8)`.
- **transparency** — colour index 0 draws fully transparent.
- **palettes** — JASC-PAL text. The 4-bit palette field indexes a **globally concatenated** list,
  so `secondary/<name>/palettes/07.pal` *is* global palette 7.
- **tiles.png** — 4bpp indexed, 128 px wide, 16 tiles per row. Read the raw *index*, never the
  PNG's own palette.
- Skip `border.bin` — the guide does not want borders.

The renderer needs only the **966** live layouts; the other 74 defined-but-unreferenced are dead.

---

## 8. Build and repo mechanics

- **`git push` on the game repo is slow, not broken.** `.git/hooks/pre-push` runs
  `Testing/ValidateGen13.py` and `Testing/GenObstacleTable.py --check`; on `/mnt/c` that exceeds
  three minutes. `gh api` is sub-second — use the REST API for ref writes. The `v1.3.6` tag was
  created that way (tag object `64331bad`).
- **The game repo is public** (`private: false`), contrary to older project notes. CI can clone the
  submodule with no deploy token.
- Several data files are **generated, not committed**: `src/data/trainers.h`,
  `src/data/trainers_frlg.h`, `src/data/wild_encounters.h`, `src/data/battle_partners.h`,
  `src/data/debug_trainers.h`. Extractors must read the `.party` / `.json` sources.
  **Never audit against a dirty working tree**, which contains these as untracked artifacts.

---

## 9. Sections still pending

These were dispatched but had not reported at the time of writing. They do not block the M0
conclusions above.

- **Trainers** — `.party` grammar and optional-field semantics, `TRAINER_*` id space across the two
  files, trainer→map linkage chain and coverage count, HARD rematch representation, leader→Mega
  Stone mapping, gym/E4/champion/World Championship rosters.
- **Species and items** — evolution parameter semantics, TM-vs-tutor distinguishability, item
  `locations` sourcing difficulty, Mega Stone vendor prices. *(Disabled-species mechanism is
  settled — see §5A.)*
- **Systems and progression** — badge flags, obedience formula, Hard Mode level caps, region unlock
  order, league/champion gates, the non-vanilla system inventory, flag/var census, charmap decoding,
  and the static-vs-hand-authored gating boundary.

---

## 10. Open questions for the human

Numbered for reference from `DECISIONS.md` and commit messages.

**Q1 — Which commit should the guide track?**
`v1.3.6` is ~30 commits behind `master`. Documenting a release is the defensible choice and matches
the brief, but it means the guide ships without the Orange Islands, the Jessie & James ambushes and
the World Championship Dome entry, all of which are live on `master`. Options: stay at v1.3.6 and
advance the pin at a later release; move the pin to `master` now and accept a moving target; or cut
a `v1.4.0` tag from `master` and pin to that. **This choice should be made before M1**, because it
changes which maps and trainers exist.

**Q2 — Confirm the Porymap decision reversal.**
Brief decision #4 says images come from Porymap exports and that a headless renderer "may be built
later". §0.3 shows Porymap cannot render this project correctly at all. Recommend replacing decision
#4 with "images are produced by `tools/porymap/render.py`". This is strictly less work — it deletes
M4's manual export hand-off and makes the atlas reproducible in CI. Needs your sign-off since it
changes section 3.

**Q3 — What should `tools/validate/` assert per region?**
Per §0.2 the completeness ledger cannot detect a whole missing region. I propose hard minimums per
region (maps, trainers, gym leaders, encounter tables) that fail the build when unmet. I need your
expected counts, or permission to snapshot the current numbers as the baseline.

**Q4 — Should region-neutral maps get a `shared` bucket?**
`MAP_REGION_HUB`, the 24 Secret Bases and the 5 FRLG link rooms classify as Hoenn by fall-through.
Recommend a fourth `region` value, `shared`, and excluding them from the three region atlases.

**Q5 — How much Sevii Islands content is live, and does it get its own atlas?**
`enum KantoSubRegion` has `SEVII123`, `SEVII45`, `SEVII67` with dedicated region-map layouts. The
brief scopes the guide to three regions. If Sevii is playable it needs pages, and that is a scope
increase to confirm.

**Q6 — What do the 115 hidden items without `quantity`/`underfoot` default to?**
298 hidden items exist; 183 carry those fields. Rather than invent defaults, this needs the engine
behaviour confirmed, or the fields marked `null` with a `gap` reason per the brief's rule.

**Q7 — How should Altering Cave's 18 tables be presented?**
`MAP_SIX_ISLAND_ALTERING_CAVE` has 9 tables × FireRed/LeafGreen variants; `MAP_ALTERING_CAVE` has 9.
This game is neither FireRed nor LeafGreen, so it is unclear which are live. Publishing 18 tables
for one cave is not a guide. Needs the runtime selection rule, then an editorial call.

**Q8 — How should Saffron City be rendered in the atlas?**
`MAP_SAFFRON_CITY_CONNECTION` is an empty 48×40 stub that the surrounding routes actually connect
to, while the real 66×55 city connects outward but is not connected back to. Without a rule, the
region view places an empty rectangle where Saffron belongs and floats the real city unconnected.
Recommend rendering `MAP_SAFFRON_CITY` as the page and treating `_CONNECTION` as a positioning alias.

**Q9 — Deploy target confirmation.**
Per your instruction the site deploys to `dev.jdayers.com/pkmn-world` rather than GitHub Pages
(brief decision #2). Two consequences to lock in now: Astro needs `base: '/pkmn-world'`, and every
asset and link reference must be subpath-relative rather than root-absolute. Confirm whether CI
should deploy over SSH to that host, or whether you will deploy manually.
