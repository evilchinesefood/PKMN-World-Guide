# Data Audit — M0

**Game pin:** `game/` submodule at **`9ee61fbd`** (`master`, 2026-07-24)
**Audited:** 2026-07-24, **re-measured at the new pin 2026-07-25**

> **Re-pinned from `v1.3.6` to `master` on 2026-07-25**, resolving open question Q1. The original
> audit ran at `v1.3.6` (`87a66e89`); §0.4 explains why that pin was abandoned. Every number in
> this document has been re-measured at `9ee61fbd`. Where the two pins differ materially the
> v1.3.6 figure is shown alongside, because the delta is itself informative.
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

### 0.4 RESOLVED — why the pin moved from `v1.3.6` to `master`

**Status: acted on 2026-07-25. The submodule is now pinned to `9ee61fbd`.** Everything below
describes the `v1.3.6` state that forced the move; it is retained because it is the justification
for decision 8 in `DECISIONS.md`, not because it still holds.

Confirmed present at the new pin: `battle_net` (13 files), `BattleNet` (63), `SHARD_PRICE`,
`LeaderSim`, `TowerStreak`, and — decisively — **the Mega Ring is now givable**:
`data/maps/RegionHub_2F/scripts.inc:19` → `giveitem ITEM_MEGA_RING`, guarded by a
`checkitemspace` at :17. `Testing/ValidateGen13.py` also exists again and **passes**
(`families disabled: 339 … OK — no disabled-species references in obtainable content`).

---

**The original v1.3.6 finding**, found independently by three separate audits and verified
directly:

Brief §5 lists what `systems.json` must cover: *"World Transit, shared PC and Pokédex, obedience by
current-region badge count, riding your own Pokémon, **Battle Net terminals, Shard economy and Mega
Stone vendors, sim modes (Scaling Type Trainer, Leader Sim, Tower Streak, Lv50, Monotype, Little
Cup)**, World Championship gauntlet."*

**At `v1.3.6` the bolded half does not exist.** Verified by exhaustive grep over `src/`, `include/`
and `data/`:

| identifier | files matching |
| --- | ---: |
| `battle_net` / `BattleNet` / `BATTLE_NET` | **0** |
| `SHARD_PRICE` | **0** |
| `LeaderSim` | **0** |
| `ScalingType` | **0** |

There is no `src/battle_net.c`, no `RegionHub_2F`, no Pokémon Center terminals, no vendor, no
BP→Shard clerk, and no leader→Mega-Stone table. Shards appear only in the vanilla Route 124
Treasure Hunter's House.

**Worse: Mega Evolution is unusable.** `ITEM_MEGA_RING` has exactly **one** reference outside its
own item/constant definitions — `src/battle_util.c:8428`, inside `CanMegaEvolve()`:

```c
&& !CheckBagHasItem(ITEM_MEGA_RING, 1))
```

No script anywhere gives the ring. All 92 Mega Stones are defined in `items.h` but referenced
outside it **only from `test/battle/**` unit tests**. So at this pin: 92 stones exist, 0 are
obtainable, the ring is unobtainable, and Mega Evolution cannot be used in normal play.

Also absent at the pin, contrary to prior project notes: the Jessie & James ambushes, the Orange
Islands, `Testing/ValidateGen13.py`, and the sim-EXP change.

**Recommendation: re-pin to `master` (or cut a `v1.4.0` from it) before M1.** Documenting v1.3.6
means shipping a guide whose `systems.json` is missing its entire endgame economy, whose Mega
Evolution pages would have to say "unobtainable", and which omits content the game's own
`FEATURES.md` advertises. This is open question **Q1**, and it is now the single decision that
gates everything else.

### 0.5 A live game defect: 22 trainer slots contain the wrong trainer

Found by the trainer audit and **verified here directly** — this is a bug in the game data, not an
extraction artifact.

22 entries in `src/data/trainers.party` occupying ordinary Hoenn/Johto route-trainer ids are
authored with **Kanto boss parties**, byte-identical to their real counterparts in
`trainers_frlg.party`. The clearest case:

```
=== TRAINER_LYLE ===
Name: LORELEI
Class: Elite Four Frlg
Pic: Elite Four Lorelei Frlg
...
Level: 64
```

`TRAINER_LYLE` is the **Bug Catcher in Petalburg Woods** — an early-game Hoenn route — and he is
live: `data/maps/PetalburgWoods/scripts.inc:273` calls
`trainerbattle_single TRAINER_LYLE, …`. A player reaching Petalburg Woods around Lv 8 fights an
Elite Four ice team at Lv 63-66.

The full verified set, each duplicating a real Kanto boss:

| slot | renders as | slot | renders as |
| --- | --- | --- | --- |
| `TRAINER_LYLE` | LORELEI | `TRAINER_SHELBY_2` | BROCK |
| `TRAINER_CALVIN_1` | KOGA | `TRAINER_SHELBY_3` | MISTY |
| `TRAINER_JOSH` | SABRINA | `TRAINER_SHELBY_4` | LT. SURGE |
| `TRAINER_BILLY` | BLAINE | `TRAINER_SHELBY_5` | ERIKA |
| `TRAINER_VICKY`, `TRAINER_DOUG` | AGATHA | `TRAINER_SHELBY_1`, `TRAINER_GREG` | LANCE |
| `TRAINER_JOSE`, `TRAINER_TIMOTHY_5` | BRUNO | `TRAINER_TIMOTHY_4` | LORELEI |
| `TRAINER_JACKI_2` | GIOVANNI | `TRAINER_CLAUDE`, `TRAINER_ELLIOT_1`, `TRAINER_NED`, `TRAINER_JAMES_1`, `TRAINER_JAMES_2`, `TRAINER_KENT` | BLUE |

Consistent with a block of FRLG boss parties being pasted into `trainers.party` and landing on
already-occupied Hoenn ids — the 0-1095 window is documented as frozen and full
(`include/constants/opponents.h:1118-1125`). Ruled out as a preprocessor artifact:
`grep -c '^\s*#' src/data/trainers.party` → **0**, no conditionals, and `gTrainers` is a flat
concatenation with no runtime remap.

**Consequence for the guide: a trainer's constant name is not evidence of who it is.** Render from
`Name:`/`Class:`/`Pic:`. Left alone, the generator will correctly publish "SABRINA, Leader, Lv
37-43" as a Rustboro Gym junior. See open question **Q10**.

---

## 1. Scale

Measured at `9ee61fbd`; the `v1.3.6` column is kept where it differs.

| metric | **master `9ee61fbd`** | v1.3.6 |
| --- | ---: | ---: |
| `data/maps/*/map.json` | **1195** | 1194 |
| distinct layouts referenced by live maps | **966** | 966 |
| layouts defined in `data/layouts/layouts.json` | 1040 | 1040 |
| layout directories on disk | 1058 | 1058 |
| layouts defined but referenced by no live map | 74 | 74 |
| maps with no layout | 0 | 0 |
| layouts referenced but not defined | 0 | 0 |
| map ids unique / total | **1195 / 1195** | 1194 / 1194 |
| MAPSEC entries | 266 | 266 |
| object events | **6925** | 6859 |
| warp events | **3434** | 3432 |
| coord events | 1018 | 1018 |
| bg events | 1589 sign, **304 hidden item**, 75 secret base | 1587 / 298 / 75 |
| map connections | 366 (on **176** maps) | 366 / 176 |
| encounter entries | 479 across 331 maps | 479 / 331 |
| species families enabled / disabled | **200 / 339** | 274 / 265 |

**Map id is a safe primary key** — 1195 unique out of 1195.

**The layout and encounter layers did not move at all** between the two pins — same 966 live
layouts, same three `layout_version` regimes (emerald 441 / frlg 345 / johto 254), same 479
encounter entries, same rate tables. The renderer spec in §7 and the encounter schema are
unaffected by the re-pin.

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

### 2.4 Region-neutral maps — 66, not 30

A first pass identified the hub, the 24 Secret Bases and the 5 FRLG link rooms. The real set is
**66**, because the whole `MAPSEC_DYNAMIC` group falls through too. Verified:

| mapsec | maps |
| --- | ---: |
| `MAPSEC_DYNAMIC` | **37** |
| `MAPSEC_SECRET_BASE` | 24 |
| `MAPSEC_SPECIAL_AREA` | 5 |
| **total** | **66** |

`MAPSEC_DYNAMIC` covers `RegionHub`, `BattlePyramidSquare01..16`, the 6 Contest Halls, the 6
`UnusedContestHall*`, the 3 SS Tidal maps, and the **non-`_Frlg`** twins of the link rooms
(`UnionRoom`, `TradeCenter`, `RecordCorner`, `BattleColosseum_2P/4P`). Note both sets of link rooms
are region-neutral but arrive there by different routes — the `_Frlg` ones via
`MAPSEC_SPECIAL_AREA`, the plain ones via `MAPSEC_DYNAMIC`.

**Clean static predicate:**
`region_map_section ∈ {MAPSEC_DYNAMIC, MAPSEC_SECRET_BASE, MAPSEC_SPECIAL_AREA}` → `shared`.
Adding `MAPSEC_INSIDE_OF_TRUCK` (the Hoenn intro truck) makes 67; that one is arguably genuinely
Hoenn. See open question **Q4**.

Two related traps:
- **`MAPSEC_DYNAMIC` is the only mapsec with no `name` field.** An extractor reading display names
  hits a `KeyError` on 37 maps.
- 11 mapsecs lack `x`/`y`/`width`/`height` (no region-map placement), including Birth Island,
  Faraway Island, Navel Rock and Marine Cave. **Lacking coordinates does not mean region-neutral** —
  those are genuinely Hoenn.

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

### 3.1 Hidden items — 298 total, defaults resolved

The ledger target for the hidden-item overlay is **298**, spread across 121 maps. They are
`bg_events` with `type: "hidden_item"`, carrying `item` and `flag`. All 298 have both, and **all
298 `flag` values are distinct — usable as a stable primary key.**

By region: **Kanto 183, Hoenn 112, Johto 3.**

**The 115 records missing `quantity`/`underfoot` are not a gap.** The build tool supplies the
defaults — `tools/mapjson/mapjson.cpp:345-351`:

```cpp
string quantity = json_to_string(bg_event, "quantity", true);
if (quantity.empty()) { quantity = "1"; }
string underfoot = json_to_string(bg_event, "underfoot", true);
if (underfoot.empty()) { underfoot = "FALSE"; }
```

**Absent `quantity` → 1. Absent `underfoot` → FALSE.** These are engine defaults, so materialising
them is reporting, not inventing. The split tracks provenance: FRLG-sourced maps carry both keys,
native-Emerald and ported-Johto maps omit them.

Observed values: `underfoot` false 177 / **true 6** / absent 115. `quantity` 1×171, 10×8, 20×2,
40×1, 100×1, absent 115.

⚠ **Johto has only 3 hidden items** against Kanto's 183 and Hoenn's 112. A Johto hidden-item
overlay will look broken, but the data really is that sparse. Worth confirming before the ledger
reports it as complete — see open question **Q11**.

### 3.2 Two corrections to the naive reading

- **`connections` is present on 1184 maps but non-empty on only 176.** 764 carry the key with a
  `null`/empty value. Presence of the key means nothing; **only 176 maps actually connect.**
- **`dest_warp_id` is a string 3430 times and an integer 2 times** — both in
  `data/maps/Route29/scripts.inc`'s map, warps 0 and 1. A strictly-typed parser dies on it.
  Same class: `trainer_sight_or_berry_tree_id` and object `flag` are strings throughout,
  including numeric-looking `"0"` and `"2"`.

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

### 5.1 One id space, disjoint ranges, zero collisions

`src/data.c:230` concatenates both files into one flat `gTrainers[DIFFICULTY_COUNT][TRAINERS_COUNT]`
with designated initializers and no runtime remap.

| file | entries | unique ids | id range |
| --- | ---: | ---: | --- |
| `trainers.party` | 1121 | 1099 | **0-1095** (+3 exceptions) |
| `trainers_frlg.party` | 631 | 623 | **1097-1719** |

Kanto ids are rebased by `KANTO_TRAINER_ID_OFFSET 1096` in
`include/constants/opponents_frlg.h`. Name→id is strictly 1:1 across 1722 ids, and the composite
key `(id, difficulty)` is unique across all 1752 entries — **zero collisions**, so no
disambiguation is needed. `opponents.h:1118-1125` documents the 0-1095 window as **frozen and
full**, guarded by `STATIC_ASSERT`.

**But the file does not determine region.** Three late-added Johto rivals
(`TRAINER_RIVAL_INDIGO_{CHIKORITA,CYNDAQUIL,TOTODILE}`, ids 1720-1722) are authored in
`trainers.party` using ids borrowed from the Kanto bank's spare capacity, exactly as `opponents.h`
prescribes, and are reached through an alias in `johto_compat_ids.h`.

**Extractor rule: parse both files into one table keyed by resolved numeric id; derive region from
the map the trainer occupies — never from the source file, the id range, or the constant name**
(see §0.5).

Region of the maps each file's trainers occupy: `trainers.party` → Hoenn 551, Johto 312, **Kanto 0**.
`trainers_frlg.party` → Kanto 261, **Hoenn 0, Johto 0**. So `trainers_frlg.party` is exactly Kanto.

**Exclude** `debug_trainers.party` (`DEBUG_TRAINER_*` prefix, separate `sDebugTrainers` array,
debug-menu only) and the `test/battle/` fixtures. `battle_partners.party` is a separate namespace
entirely (`PARTNER_*` → `gBattlePartners`); only one real entry, `PARTNER_STEVEN`.

### 5.2 HARD is a second entry under the same id

`enum DifficultyLevel { EASY, NORMAL, HARD, TEST }`, selected at runtime by `VAR_DIFFICULTY`.
A HARD variant is a second `=== TRAINER_X ===` block carrying `Difficulty: Hard`.
**Key on `(id, difficulty)`.**

**Exactly 30 HARD entries** = 24 gym leaders + Hoenn's Sidney/Phoebe/Glacia/Drake/Wallace/Steven.
⚠ **Kanto and Johto Elite Four rematches do not use the difficulty system** — they are separate
trainer ids (`TRAINER_KAREN_2_JT` vs `_1_JT`). Two distinct mechanics; presenting them as one
would be wrong.

### 5.3 Optional fields — absent is not zero

| field | default when absent | source |
| --- | --- | --- |
| `Level` | 100 | `tools/trainerproc/main.c:2184` |
| `IVs` | 31 across the board | `main.c:2183` |
| `EVs` | 0 | file header |
| `Nature` | Hardy | file header |
| `Difficulty` | `Normal` | `main.c:1816` |
| moves | last 4 level-up moves at that level | file header |

`Level` and `IVs` are present on all 4334 mons in both files — never defaulted, always safe to
print. **`EVs`, `Nature`, `Ball`, `Happiness`, `Shiny` are used zero times in both trainer files.**
The guide must print **"unspecified"** for EVs: the author never chose 0, the engine did.
Printing "0 EVs" would be inventing a value.

**Dual vocabulary — the same field appears in two forms.** `Class:` is human-readable 1500× and
raw `TRAINER_CLASS_*` 252× (all ported Johto entries); likewise `Music:` and `AI:`. Handle both.

### 5.4 Placement coverage — 97.6%

Of 1721 real trainers: **1258** attributable to a map via
`map.json` → script → `trainerbattle_*`; **421** placeable via `gRematchTable`, which carries a map
per row (`src/battle_setup.c:159`); **7** C-only (Frontier Brains); **36** unreferenced/dead.
So maps + scripts + `gRematchTable` places **1679/1721**.

Separately, all **315** Battle Frontier / Tower / Dome opponents live in a different universe
(`FRONTIER_TRAINERS_COUNT 315`) and are **pool-based with no fixed party** — including the 15
World Championship trainers (`WC_RED` … `WC_CLAIR`, ids 300-314, bracket at
`src/battle_dome.c:1914`, Red force-seeded into the final). Those need a **second extractor path**
that renders a candidate pool, not a team. See open question **Q12**.

Three parser traps: **160** `trainerbattle_*` calls omit the comma between args (GAS
space-separated, all in ported Johto maps) — match `trainerbattle\w*\s+(TRAINER_\w+)` and ignore
the separator; **76** trainer ids appear on 2+ maps (Johto reuses Hoenn ids deliberately, per
`johto_compat_ids.h`); and `TRAINER_NONE` is a real entry (id 0) that must be filtered.

---

## 5B. Progression and gating — the `progression.json` source

Verified directly against source. This is what the spoiler model is built from.

### 5B.1 Badges — 24 leaders, three isolated banks behind one API

**There is no 24-badge flag range.** The vanilla `FLAG_BADGE01..08_GET` constants are **Hoenn
only**. `include/constants/region_flags.h` adds two more banks:

```c
#define FLAG_KANTO_BADGE(i)  (FLAG_KANTO_BASE + 0x0B + (i))   // 0xA4B..0xA52
#define FLAG_JOHTO_BADGE(i)  (FLAG_JOHTO_BASE + 0x3F8 + (i))  // 0x63F8..0x63FF
```

Dispatched by `GetBadgeFlag(region, badgeIndex)` (`src/event_data.c:355-378`), with
`HasCurrentRegionBadge(i)` as the accessor used everywhere else. Kanto badges live inline in
`SaveBlock1.flags[]`; Johto's in `johtoFlags[128]` in SaveBlock3.

Johto badge 8 is awarded at **DragonsDen_Shrine**, not Blackthorn Gym (the HGSS Clair sequence).

### 5B.2 Obedience — by current-region badge index

`src/battle_util.c:5569-5612`:

| badges (current region) | 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| **obeys up to Lv** | 10 | 20 | 30 | 40 | 50 | 60 | 70 | 80 | ∞ |

Two precision points: these are badge **indices** tested by sequential overwriting `if`s, not a
count — a player holding only badge 5 gets Lv 60, and badge 8 alone grants full obedience. And it
applies to **outsider Pokémon only**; with `B_OBEDIENCE_MECHANICS >= GEN_8` the comparison uses
**met level**, not current level.

### 5B.3 Level caps — Hard Mode only

`src/caps.c:8-33`, verified verbatim:

```c
static const u32 sLevelCapPerBadge[NUM_BADGES] = { 15, 19, 24, 29, 31, 33, 42, 46 };
if (!gSaveBlock2Ptr->optionsHardMode) // QoL #16: caps only bind in Hard Mode
    return MAX_LEVEL;
```

| badges | 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 8 + champion |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| **cap** | 15 | 19 | 24 | 29 | 31 | 33 | 42 | 46 | 58 | 100 |

At or over the cap, EXP gain is **zero** (`B_EXP_CAP_TYPE = EXP_CAP_HARD`). The last tier keys on
the **global** `FLAG_IS_CHAMPION`, not a per-region flag — a cross-region asymmetry worth a
footnote.

⚠ **EV caps are dead code.** `B_EV_CAP_TYPE = EV_CAP_NONE`, so `GetCurrentEVCap()` always returns
`MAX_TOTAL_EVS`. The `sEvCapPerBadge` table exists but never fires. **Do not document EV caps.**

**Hard Mode is global and permanent** — a 1-bit `gSaveBlock2Ptr->optionsHardMode`, chosen once at
new game and never exposed in the Options menu again. Do not confuse it with `VAR_DIFFICULTY`,
which **is per-region** and re-synced on every region entry by `SyncDifficultyForRegion()`. They
share the word "difficulty" and are different things.

### 5B.4 There is no region unlock order

**The player may start in any region and switch at any time.** The three hub attendants
(`data/maps/RegionHub/scripts.inc:53, 76, 97`) have **no flag check at all**. Only the Battle
Frontier gate is locked.

The friction is *returning*, not leaving: until you are a two-region champion you must reach that
region's access point. **And obedience and level caps reset per region** — a second region starts
you back at a Lv-15 cap in Hard Mode regardless of prior progress. That is the real cost of
switching and should headline the "which region first" primer.

### 5B.5 Champion flags and the global gates

`FLAG_KANTO_CHAMPION 0xA48 (2632)` · `FLAG_JOHTO_CHAMPION 0xA49` · `FLAG_HOENN_CHAMPION 0xA4A`.

League entry gates differ per region: Kanto checks 8 badge guards on Routes 22/23; Johto requires
**all eight badges plus** `VAR_ECRUTEAK_CITY_THEATER >= 8` (Kimono Girls); Hoenn checks
**`FLAG_BADGE06_GET` only** — the vanilla "Winona's badge is the only one that can be skipped".

`IsNRegionChampion(n)` drives the global gates:

| n | unlocks |
| --- | --- |
| ≥1 | Battle Frontier · Eon Ticket · **DexNav detector mode** |
| ≥2 | PC 2F World Transit pad · Old Sea Map |
| =3 | Mystic Ticket · **World Championship registrar** |

### 5B.6 Proposed gate keys

```
kanto:badge-1..8      johto:badge-1..8      hoenn:badge-1..8
kanto:league-entry    johto:league-entry    hoenn:league-entry
kanto:champion        johto:champion        hoenn:champion
global:champion-any   global:champion-two   global:champion-all
global:world-championship
global:world-tour-4 / -8 / -12 / -16 / -24        (Charm Curator, cross-region badge totals)
global:dex-150 / dex-300 / dex-complete
```

⚠ **`global:battle-net` from brief §5 has no source at this pin** — see §0.4.

### 5B.7 Static vs hand-authored — the honest boundary

**Roughly 60-70% derivable. The ordering layer is not.**

Fully derivable: badge→flag→map (24/24 unambiguous `setflag` sites), champion flags, league entry
gates, item gifts and their conditions, trainer placement, mart stock.

**Hand-author three things:** (a) the ~15 `callnative RegionHub_Scr*` hooks, whose semantics live
in C — an extractor sees `callnative RegionHub_ScrIsTwoRegionChampion` and cannot know it means
`IsNRegionChampion(2)`; (b) the C rule tables (obedience, caps, field-move gates), which appear in
no script; (c) **region-level story ordering**, which lives in `VAR_*_STATE` counters (3106
`setvar`, 524 `switch`) and would need whole-program dataflow to recover.

**Estimate: 60-100 `hand_authored: true` entries, not hundreds.**

### 5B.8 Field-move gates — Kanto's badge mapping differs

`src/field_move.c:15-90`. Kanto maps moves to different badge indices than Hoenn/Johto (Cut is
idx 1 not 0, Flash idx 0 not 1, Fly idx 2 not 5, Waterfall idx 6 not 7), and **Johto's Surf is
idx 3 not 4** — an explicit anti-softlock, since Cianwood is reachable only by surfing.

`QOL_FIELD_MOVES_ITEM_GATE = TRUE`: owning `ITEM_CUT_TOOL`…`ITEM_DIVE_TOOL` **bypasses the badge
gate entirely** for Cut/Rock Smash/Strength/Surf/Dive/Waterfall. **Flash and Fly have no item
bypass — badge only.** `QOL_FIELD_MOVES_NO_TEACH = TRUE`: a Pokémon that merely *could* learn the
HM performs it untaught.

### 5B.9 Sevii Islands are substantially live

**160 maps, 115 with real scripts, 9738 script lines, 141 encounter entries, 3 dedicated
region-map layouts.** That is ~38% of all Kanto maps. `GetKantoSubregion(mapSecId)` gives the
MAPSEC→group mapping for free.

Hack-specific integration worth documenting: **the Vermilion pier is dual-purpose** — it offers the
World Transit hub first, and declining falls through to the vanilla Seagallop destinations
(`data/maps/VermilionCity_Frlg/scripts.inc:57-61`).

**Unknown:** whether Sevii's story beats are playable end to end. `FEATURES.md` and `README.md`
never mention Sevii. Content exists and is scripted; completion was not verified. See **Q5**.

### 5B.10 Other systems confirmed present

**World Transit** — switching regions **boxes your whole party** to the global PC; held mail moves
to the PC mailbox; if the PC fills, the transfer stops partway. The hub is deliberately never a
whiteout target.

**Shared PC and Pokédex** — one global National Dex across all regions. **No regional dex numbers
per species**; only `.natDexNum`. Kanto and Hoenn orders derive from `sKantoToNationalOrder` /
`sHoennToNationalOrder`. **There is no Johto dex** — `JOHTO_DEX_COUNT` is defined but has no order
table, and `SpeciesToRegionalPokedexNum` routes Johto to the **Hoenn** dex.

**Riding your own Pokémon** — one picker for surf and flight: the active follower rides if capable,
else the first capable party member by slot order. Falls back to the generic blob (surf) or Flygon
(flight).

**DexNav** — granted with each region's Pokédex; **detector mode unlocks at your first Hall of
Fame**. ⚠ `USE_DEXNAV_SEARCH_LEVELS = FALSE`, so the whole search-level table is **inert — do not
document it**. Hidden-encounter coverage is total: 400 `land_mons` and 400 `hidden_mons` entries,
**zero land maps without a `hidden_mons` block**.

**Quest system — enabled but empty.** The engine is present (`src/quests.c`, `QUEST_COUNT 30`) but
`sSideQuests[]` is stock upstream demo data ("Side Quest 1", "Description 1") and **no map script
calls `questmenu`**. Zero authored quests. See **Q13**.

### 5B.11 Script and text extraction notes

🔑 **`callnative` is the hack's signature macro.** Every custom system hooks in through it. **An
extractor that only understands `special` misses every hack-specific gate.** There is no
`checkflag` macro — flag reads are `goto_if_set` / `goto_if_unset` / `call_if_*`.

`asm/macros/johto_compat.inc` redefines **18 macros** whose bytecode diverges from the source hack,
mostly re-expressed as `callnative ScrCmd_*_Compat`. Two consequences: every Johto-only command
**is** a `callnative`, and operands trail the pointer inline — so **parse source, not bytecode**.

⚠ **`chooseitem` is a documented stub with gameplay consequences.** The bag-choice UI was never
ported, so it resolves to `ITEM_NONE` and the caller falls through to the "disliked berry" branch.
Named in-file: the **Ice Path / Blackthorn berry puzzle**. The guide must not describe an item
prompt there.

Text: escapes are `\n` (line break), `\l` (wait, scroll one line), `\p` (wait, clear, new
paragraph), `$` (terminator, strip). Consecutive `.string`s concatenate; only the last carries `$`.
`POKé`'s `é` is a real charmap glyph — keep it. **Gender branches have no text-level escape** —
they are done in script via `checkplayergender`, so an extractor scanning `.string`s alone will
miss both variants.

---

## 5A. Species enablement — the roster is 274 families, not 539

This drives `obtainable_via` and the "every obtainable species has a documented acquisition
method" ledger target, so it is settled here rather than left pending.

`include/config/species_enabled.h` defines **539** `P_FAMILY_*` toggles. All nine
`P_GEN_N_POKEMON` macros read `TRUE`, but 265 families are overridden to a literal `FALSE`:

```c
#define P_FAMILY_TURTWIG   FALSE // world-strip: unreferenced in all 3 campaigns (was P_GEN_4_POKEMON)
```

| | **master `9ee61fbd`** | v1.3.6 |
| --- | ---: | ---: |
| **Enabled** | **200** | 274 |
| **Disabled** ("world-strip") | **339** | 265 |
| total `P_FAMILY_*` | 539 | 539 |

**265 + 74 = 339.** The re-pin resolves the count discrepancy noted below: a second strip pass
after v1.3.6 disabled exactly **74** more families, which is where the "74" in the project notes
came from. All three figures were correct for their own commits.

At the new pin the game's own validator agrees and passes:
```
families disabled: 339 | species mapped: 1571 (+1025 names) | wild entries: 9612
OK — no disabled-species references in obtainable content; all Gen 4+ families stripped.
```
**Run `Testing/ValidateGen13.py` as part of `tools/validate/`** — it is the game's own invariant
check and it exists again at this pin. It asserts both that no obtainable content references a
stripped family *and* that every Gen 4+ family is stripped.

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

> **The world-strip is still moving — do not carry counts between commits.** Prior project notes
> record two different figures (an early pass disabling 74 families, and later "339 disabled
> families" describing `master`). At **this pin** the count is **265 disabled / 274 enabled**,
> measured directly. All three numbers can be correct for their respective commits; the strip was
> tightened over time. The guide must recompute from the pinned `species_enabled.h` and never
> inherit a count from notes or from `master`.
>
> Related: those notes cite `Testing/ValidateGen13.py` as the validator. **That file does not
> exist at v1.3.6** — the whole `Testing/` directory is absent. It is `master` content, referenced
> by the `pre-push` hook in the working tree. Any validation the guide wants must be written fresh.

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

## 9. Items, learnsets and evolutions

### 9.1 Ground items use three different mechanisms, one per region

The single highest-risk extraction surface. All **478** item-ball `object_events` resolved:

| region | n | mechanism | item id lives in |
| --- | ---: | --- | --- |
| Hoenn | 162 | `Common_EventScript_FindItem` | **`map.json`** → `trainer_sight_or_berry_tree_id` |
| Hoenn | 48 | `BattlePyramid_FindItemBall` | runtime-random — **exclude** |
| **Kanto** | **168** | bespoke label | **one central `data/scripts/item_ball_scripts_frlg.inc`** |
| Kanto | 2 | bespoke label | per-map `scripts.inc` |
| **Johto** | **78** | bespoke label | **per-map, scattered across 23 dirs** |
| mixed | 19 | ball sprite, not an item | gift mon / static battle — **exclude** |
| Hoenn | 1 | `"script": "0x0"` | ContestHall — exclude |

**410 of 478 resolve to a concrete item.** Three regions, three mechanisms, and the Hoenn one reads
the item id out of a field named `trainer_sight_or_berry_tree_id`. Only safe approach: index every
`^LABEL::` across `data/**/*.inc`, resolve each object event's `script`, then **assert
`resolved == 410`**.

Ground items use **`finditem`** (`STD_FIND_ITEM`); scripted gifts use **`giveitem`**
(`STD_OBTAIN_ITEM`). Different opcodes, so the two sources do not overlap and need no dedup.

### 9.2 Scripted gifts — the Kanto macro is different, and grepping `giveitem` misses it

⚠ **`giveitem_msg` (37 sites) appears only in `_Frlg` maps**, and it wraps `additem`:

```asm
	.macro giveitem_msg msg:req, item:req, amount=1, fanfare=MUS_LEVEL_UP
	additem \item, \amount
```

**The item is argument 2, not argument 1.** A `giveitem` regex reads the *message label* as the
item and still runs clean. Totals: `giveitem` 279, `giveitem_msg` 37, `additem` 26 — **342 gift
call sites** (Hoenn 164, Johto 91, Kanto 66).

**Shop stock is structurally safe** — 63 mart lists across 43 maps, `pokemart <LABEL>` +
`.2byte ITEM_*` terminated by `ITEM_NONE`, no `_frlg` split. But **247 item prices are C ternaries**
on config (`(I_PRICE >= GEN_7) ? 200 : 300`) and must be evaluated, not read literally. See **Q14**.

### 9.3 Items and species data are single-source

`src/data/items.h` has no `_frlg` twin — one `ITEM_*` enum, **893 items** (ITEMS 596, TM_HM 108,
KEY_ITEMS 93, BERRIES 68, POKE_BALLS 28). Species data and learnsets likewise:
`git ls-files 'src/data/pokemon/**' | grep -i frlg` → zero hits.

**So only the `locations` array carries region-split risk, not the item or species fields.**

Description decoding: the only escape is `\n` (1551), the only non-ASCII is `é` (163), the only
brace tokens are `{POKEBLOCK}` ×17 and `{PKMN}` ×5. Concatenate adjacent literals, `\n` → `<br>`,
expand the two tokens, keep `é`, HTML-escape, then **assert no residual `\[a-zA-Z]` or
`{[A-Z_]+}`**.

### 9.4 TMs and tutors are distinguishable — but tutor *location* is a real gap

`src/data/pokemon/teachable_learnsets.h` **does not exist** — gitignored build artifact
(`.gitignore:64`), generated by `tools/learnset_helpers/make_teachables.py` from
`all_learnables.json` and friends.

The teachable array is flat, but the sets are **disjoint**, verified on real data: TM/HM 58 moves,
tutor 31, universal 10, **TM ∩ tutor = empty**. So:
`move ∈ FOREACH_TM/FOREACH_HM` → TM column, else `∈ gTutorMoves` → tutor column. Separate columns
are safe.

**The real gap: there are three tutor rosters and the data flattens them into one union.**

| roster | file | moves |
| --- | --- | ---: |
| Hoenn/Johto | `data/scripts/move_tutors.inc` | 10 |
| **Kanto** | `data/scripts/move_tutors_frlg.inc` | **15** |
| Battle Frontier (BP) | `data/maps/BattleFrontier_Lounge7/scripts.inc` | 20 |

Only **5** moves are shared between Kanto and Hoenn/Johto; **10 are Kanto-exclusive**, **5
Hoenn-exclusive**. The compatibility data says "Bulbasaur can learn Seismic Toss from *a* tutor"
with no location. **The guide must re-parse the three scripts** and label
"Tutor (Kanto)" / "Tutor (Hoenn/Johto)" / "Tutor (Frontier, BP)" — one merged column tells the
reader they can learn a move in a region that has no such tutor. See **Q15**.

**The TM list is 50 TMs + 8 HMs, not 100+.** `ITEM_TM01..ITEM_TM100` enum slots exist but only
01-50 bind to a move. TM number = 1-based index into `FOREACH_TM`; the item's `.name` is literally
`"TM01"`, so **the move must come from the macro index, never the name**.

Egg moves are present: `src/data/pokemon/egg_moves.h`, **418 learnsets**.

### 9.5 Evolutions — 9 methods, and the conditions carry the meaning

Expansion's format is `{method, param, targetSpecies, CONDITIONS(...)}`. Counts:
`EVO_LEVEL` 436 · `EVO_ITEM` 104 · `EVO_SPIN` 63 · `EVO_TRADE` 30 · `EVO_NONE` 9 ·
`EVO_SCRIPT_TRIGGER` 3 · `EVO_SPLIT_FROM_EVO` 2 · `EVO_LEVEL_BATTLE_ONLY` 2 · `EVO_BATTLE_END` 1.

**An extractor reading only method + param renders most evolutions wrong.** Two traps:

- **`EVO_LEVEL` with `param == 0` means "no level gate — the conditions carry the trigger"**, and
  it covers friendship, time-of-day, location, step-count and stat-comparison evolutions across
  436 uses. 32 distinct `IF_*` conditions exist; the commonest are `IF_HOLD_ITEM` 83, `IF_TIME` 79,
  `IF_MIN_FRIENDSHIP` 20.
- **`EVO_NONE` is not an evolution** — it is a breeding-only link. Rendering it draws phantom
  arrows. Must be excluded.

Every trade evolution has an `EVO_ITEM` single-player twin (Kadabra → `ITEM_LINKING_CORD`,
Onix → `ITEM_METAL_COAT`). See **Q16**.

⚠ Parser requirement: `#if` branches sit *inside* `EVOLUTION(...)`, and in `SPECIES_NINCADA` the
closing paren is inside the `#if`. A brace-balancing parser handles it; a line-based one will not.

### 9.6 `obtainable_via` must model four states

1. **Enabled with a source** → normal page.
2. **Enabled, evolution-only** (cross-gen evos, Megas) — uncatchable, reachable only by evolving.
   Needs the parent named, or completeness reports false gaps.
3. **Enabled but unreachable** — the ~381 species in Gen 4-9 families that survived the strip but
   nothing references. Compile fine, will not crash, **must not be listed as obtainable**.
   Distinguishing (2) from (3) requires the encounter/trainer/script cross-reference, not the
   species table.
4. **Disabled** — crashes at send-out if a player holds one from an old save. Nothing marks these;
   only the family test finds them.

**Zero trainer parties reference a disabled species** at this pin — verified across all 4334 mons.

---

## 10. Open questions for the human

Numbered for reference from `DECISIONS.md` and commit messages.

**Q1 — ✅ ANSWERED 2026-07-25: re-pinned to `master` (`9ee61fbd`).**
Everything §0.4 reported missing is present at the new pin, including a givable Mega Ring. The
`v1.3.6` tag remains on the remote and is still a valid anchor if a stable release is ever wanted.
**Follow-on, not blocking:** `master` is a moving branch. The pin is a specific SHA so builds stay
deterministic, but if you want the brief's "pinned release" principle back, tag `v1.4.0` at
`9ee61fbd` and I will repoint the submodule at the tag — one command, no rework.

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

**Q4 — Adopt the `shared` region bucket?**
66 maps are region-neutral by design and fall through to Hoenn. Clean static predicate:
`region_map_section ∈ {MAPSEC_DYNAMIC, MAPSEC_SECRET_BASE, MAPSEC_SPECIAL_AREA}`. Recommend
`region: "shared"` and excluding them from the three atlases. Does `MAPSEC_INSIDE_OF_TRUCK` (the
Hoenn intro truck, making 67) join them, or stay Hoenn?

**Q5 — Does Sevii get its own atlas, and is it playable end to end?**
**160 maps, 115 scripted, 9738 script lines, 141 encounter tables, 3 dedicated region-map
layouts** — about 38% of all Kanto maps. This is not a rounding error; the brief's three-region
scope does not cover it. But neither `README.md` nor `FEATURES.md` mentions Sevii, so whether its
story beats complete is **unknown and needs a human playtest answer** before the guide commits.

*(Q6 — hidden-item defaults — is **answered and closed**: `tools/mapjson/mapjson.cpp:345-351` sets
absent `quantity` → 1 and absent `underfoot` → FALSE. See §3.1.)*

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

**Q10 — The 22 hijacked trainer slots (§0.5): publish, suppress, or fix upstream? ⚠ STILL OPEN**
**Re-verified at the new pin `9ee61fbd`: all 22 are still present.** `TRAINER_LYLE` is still
authored as LORELEI. So this is a live defect on current `master`, not something the re-pin fixed.
Left alone the guide will correctly publish "LORELEI, Elite Four, Lv 64" as the Petalburg Woods Bug
Catcher, and similar on ~12 map pages including Rustboro Gym. Options: publish as-is (accurate to
the data, absurd to a player), suppress the 22 behind the `anomaly` field, or fix
`trainers.party` in the game repo. **This is a genuine bug worth fixing at the source** — the
guide surfacing it is arguably the most valuable thing M0 produced. Until it is decided, the
extractor sets `anomaly: "frlg_boss_in_hoenn_slot"` and the site can choose.

**Q11 — Is Johto's 3 hidden items intentional?**
Kanto 183, Hoenn 112, **Johto 3**. The Johto overlay will look broken. If this is a content gap
rather than a design choice, the ledger should flag it rather than report Johto complete.

**Q12 — Do the 15 World Championship trainers get pages?**
They are pool-based (`monSet` candidate lists), not fixed parties, and live in a different data
universe from every other trainer. Rendering them needs a **second extractor path** that presents
a candidate pool. In scope, or defer to M5 with the boss pages?

**Q13 — Mention the quest system?**
The engine is present and wired into the Start menu, but `sSideQuests[]` is stock upstream demo
data ("Side Quest 1") and no script calls `questmenu`. Omit entirely, or note that the menu entry
exists with placeholder content?

**Q14 — How should config-dependent values be evaluated?**
247 item prices and assorted species fields are C ternaries on config macros
(`(I_PRICE >= GEN_7) ? 200 : 300`). Either run `cpp` against the real config headers — which makes
a C preprocessor a hard dependency of the extractor — or hand-evaluate against the pinned config.
Recommend `cpp`: hand-evaluation silently rots the moment a config toggle changes.

**Q15 — How should region-specific tutors be presented?**
Three rosters (Kanto 15 moves, Hoenn/Johto 10, Frontier 20) flattened into one union in the data.
10 moves are Kanto-exclusive, 5 Hoenn-exclusive. Three columns, or one column with region badges?
Either way the guide must re-parse the three scripts — the compatibility data alone would tell a
reader to look for a tutor that does not exist in their region.

**Q17 — Commit the 32 MB of rendered map PNGs, or regenerate them at build time?**
`tools/porymap/Render.py` produces all 966 images in **22 seconds**, fully deterministically from
the pinned submodule. Committing them costs ~32 MB of repo (and grows on every re-pin); not
committing means CI and any fresh clone must run Python + Pillow before building the site.
Recommend **not** committing — they are a build product with a 22-second reproduction, and the
manifest's `content_hash` already tracks whether a re-render is needed. Currently gitignored
pending your call, since the brief says to ask before committing binary assets over a few
megabytes.

**Q18 — 19 markers sit outside their own map, in the source data.**
Not an extractor bug — verified against raw `map.json`. `SSAqua_RoomNW` authors two trainers at
**y = -5**; `MAP_TIN_TOWER_8F` has a warp at x = -1; several Battle Frontier and Slateport Harbor
warps sit exactly one tile past the edge; and the six `MAP_UNUSED_CONTEST_HALL*` maps are 1×1
stubs that inherit events from the full-size `ContestHall`, so the inherited coordinates land off
their own tiny layout. Markers drawn off-image silently vanish on the site. Suppress them, clamp
them, or leave them — but the six Contest Halls are already known-dead content, so the real
question is only about the ~13 live ones.

**Q16 — Trade evolutions: one row or two?**
Every trade evolution has an `EVO_ITEM` single-player twin. Render both (accurate, doubles the
table) or fold into one "Trade, or use Metal Coat" row?
