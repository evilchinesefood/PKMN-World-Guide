---
title: "Technical notes: Pallet Town to Route 22"
region: kanto
technical_to: content/kanto/PalletToViridian.md
severity: story
---

# Technical notes

Everything on this page was traced to the pinned game tree at `9ee61fbd`. It is here so the
walkthrough chapter can stay readable; nothing has been dropped, only moved. If you want to know
_why_ a claim on the chapter page is true, it is below.

**Coordinates** throughout the guide are block coordinates local to the named map, as authored in
that map's `map.json`. Two step pins in the chapter — Route 1 (12, 37) and Route 22 (36, 11) — are
the centres of grass patches rather than discrete authored events; the patch rectangles they sit
inside are recorded below.

**Gating provenance.** The chapter carries `gate: kanto:entry`, the `always_available` gate
`progression.json` authors at `data/maps/RegionHub/scripts.inc:53` — "No flag guards the hub
attendants; all three regions are selectable from a new save." Nothing gates this segment, and the
gate key is what the page's subtitle and its Insider Tips reveal button are both built from, so an
ordering-only key like `kanto:badge-1` would have printed "from Kanto badge 1 onwards" on a chapter
that needs no badge. A gate is a floor, and the floor here is arriving in Kanto.

## Sources

`data/maps/PalletTown_Frlg/`, `data/maps/PalletTown_ProfessorOaksLab_Frlg/`,
`data/maps/PalletTown_PlayersHouse_1F_Frlg/`, `data/maps/PalletTown_RivalsHouse_Frlg/`,
`data/maps/Route1_Frlg/`, `data/maps/ViridianCity_Frlg/`, `data/maps/ViridianCity_Mart_Frlg/`,
`data/maps/ViridianCity_Gym_Frlg/`, `data/maps/Route22_Frlg/`,
`data/maps/Route22_NorthEntrance_Frlg/`, `data/maps/RegionHub/scripts.inc`,
`data/scripts/route23.inc`, `data/scripts/item_ball_scripts_frlg.inc`,
`data/scripts/move_tutors_frlg.inc`, `data/layouts/Route1_Frlg/map.bin`,
`data/layouts/Route22_Frlg/map.bin`, `data/layouts/ViridianCity_Frlg/map.bin`, `src/new_game.c`, `src/region_switch.c`,
`src/battle_setup.c`, `src/field_move.c`, `src/starter_choose.c`, `src/data/trainers_frlg.party`,
`src/data/types_info.h`, `src/post_battle_event_funcs.c`, `src/birch_pc.c`,
`include/constants/region_flags.h`,
`include/config/dexnav.h`, `include/config/qol_field_moves.h`, `include/config/item.h`, plus
`data/generated/encounters.json`, `trainers.json`, `species.json` and `maps.json`.

## Why the FireRed tables and not LeafGreen

Every Kanto map in `wild_encounters.json` carries two entries, `*_FireRed` and `*_LeafGreen`. The
generator (`tools/wild_encounters/wild_encounters_to_header.py`) emits FireRed tables under
`#ifdef EMERALD` and LeafGreen tables under `#ifdef LEAFGREEN`; this project builds with
`GAME_VERSION ?= EMERALD` and `ALL_REGIONS ?= 1`, so **only the FireRed tables are compiled in.**
Route 1 and Route 2 are identical either way, but Route 22 and Viridian differ (Psyduck under
FireRed, Slowpoke under LeafGreen) and Pallet's rod tables differ too. Every water and fishing
figure in this chapter is the FireRed table.

## The World Transit hub and region switching

`WarpToTruck()` in `src/new_game.c:155` sends every new save to `MAP_REGION_HUB` under this build's
`ALL_REGIONS` path, landing the player on the departure concourse at (16, 4). The starting region
stays unset until a gate attendant is spoken to.

Four attendants stand on the concourse: Kanto at (11, 2), Johto at (16, 2), Hoenn at (21, 2) and
the Battle Frontier gate at (4, 2). **None of the three region attendants checks a flag** — all
three regions are open on turn one. The Frontier attendant _is_ gated.

The Kanto attendant hands over the Hub Pass (`ITEM_HUB_RETURN`), a key item that warps one way back
to the hub from the field, then drops the player into `MAP_PALLET_TOWN_PLAYERS_HOUSE_2F` at (6, 6).
Stepping into that room for the first time sets the respawn point to Pallet Town.

- **Shared storage.** The PC boxes are shared across all three regions — a Pokémon deposited in
  Viridian City can be withdrawn in Johto or Hoenn. The hub script calls this "the headline
  feature", and it is the same box a party lands in when it crosses a region gate.
- **Party deposit.** `RegionHub_ScrEnterRegion` calls `DepositPartyToPC()` any time the target
  region differs from the current one (`src/region_switch.c`). Confirmed by the defensive comment
  at `data/maps/PalletTown_ProfessorOaksLab_Frlg/scripts.inc:1122`, which is why Oak's starter flow
  still works on a returning champion.
- **The gate remembers.** Once Kanto's intro is done, `RegionHub_EventScript_ReturnKanto` routes the
  same attendant to Vermilion City instead of Pallet Town.
- **Arrival scene.** A one-shot scene armed by `RegionHub_ScrArmArrival` fires on Pallet Town's frame
  table for players arriving from another region — Mom's "our new home in Pallet Town, Kanto" line.
  It never plays twice.

## Pallet Town

`MAP_PALLET_TOWN` · 24 × 20 blocks · no wild grass anywhere on the map.

| Warp     | Leads to            |
| -------- | ------------------- |
| (6, 7)   | Your house, 1F      |
| (15, 7)  | Rival's house       |
| (16, 13) | Professor Oak's Lab |

Mom's free heal (`data/maps/PalletTown_PlayersHouse_1F_Frlg/scripts.inc`) is gated on
`FLAG_BEAT_RIVAL_IN_OAKS_LAB`. After that it is unlimited.

Two coordinate triggers at **(12, 1)** and **(13, 1)** — the whole width of the Route 1 exit — fire
`PalletTown_EventScript_OakTrigger` while `VAR_MAP_SCENE_PALLET_TOWN_OAK` is 0.

The sign lady wanders near (3, 10); reading the Trainer Tips sign at (5, 14) silences her trigger at
(13, 2). Pure flavour.

## Oak's Lab

Kanto does not use the game's `ChooseStarter` selection screen at all — that special is called from
exactly one place in the entire game, `data/maps/Route101/scripts.inc:228`, which is Hoenn's. In
Kanto the three balls are ordinary object events and the pick is a physical interaction.

| Ball       | `VAR_STARTER_MON` | You get          | Blue takes |
| ---------- | :---------------: | ---------------- | ---------- |
| Bulbasaur  |         0         | Bulbasaur, Lv 5  | Charmander |
| Squirtle   |         1         | Squirtle, Lv 5   | Bulbasaur  |
| Charmander |         2         | Charmander, Lv 5 | Squirtle   |

Each ball script sets `RIVAL_STARTER_SPECIES` in the same breath as `VAR_STARTER_MON`, which is what
decides every rival battle in the Kanto campaign, including both fights on Route 22.

**Rival battle 1.** One Pokémon, Level 5, IVs authored flat at **0** across all six stats. EVs and
Nature are unset in the source, so the engine supplies them — read nothing into them.

| Your starter | Blue leads | Level | Moves             |
| ------------ | ---------- | :---: | ----------------- |
| Bulbasaur    | Charmander |   5   | Scratch, Growl    |
| Squirtle     | Bulbasaur  |   5   | Tackle, Growl     |
| Charmander   | Squirtle   |   5   | Tackle, Tail Whip |

The script passes `RIVAL_BATTLE_TUTORIAL`, which carries the heal-after bit
(`RIVAL_BATTLE_HEAL_AFTER`); `src/battle_setup.c` heals the party and continues instead of whiting
the player out. Compare Route 22 below.

## Route 1

`MAP_ROUTE1` · 24 × 40 blocks · connects down to Pallet Town, up to Viridian City.

**178 tiles of tall grass**, more than any other map in this segment. Working north from the Pallet
end: a narrow column at **(12–13, 35–39)** at the entrance, then a wide double band across rows
32–35 — west side **(2–10, 32–35)**, east side **(15–21, 32–35)** — then **(12–17, 24–28)** in the
middle, **(16–21, 13–17)**, and the big top patch at **(10–21, 6–10)** just short of Viridian.

`sRoute1_FireRed` `land_mons`, step-encounter rate 21. Slot percentages are the engine's standard
land spread and sum to exactly 100.

| Species    | Total | Levels | Slots                                         |
| ---------- | ----: | ------ | --------------------------------------------- |
| Rattata    |   40% | 2–4    | 20% Lv 3, 10% Lv 2, 5% Lv 3, 4% Lv 4, 1% Lv 4 |
| Pidgey     |   30% | 3–5    | 20% Lv 3, 5% Lv 3, 4% Lv 4, 1% Lv 5           |
| Bulbasaur  |   10% | 3      | 10% Lv 3                                      |
| Charmander |   10% | 3      | 10% Lv 3                                      |
| Squirtle   |   10% | 2      | 10% Lv 2                                      |

No item ball and no hidden item anywhere on the route. One sign at (9, 31), two NPCs:

- **Poké Mart clerk, (6, 28)** — `Route1_EventScript_MartClerk`, free Potion once, guarded by
  `FLAG_GOT_POTION_ON_ROUTE_1`. A plain overworld NPC with no marker of any kind.
- **Boy, (19, 16)** — ledge hint. All **61** jump tiles on Route 1 face **south**, in bands at rows
  5, 10, 15, 20, 26 and 31. Metatile behaviours in `data/layouts/Route1_Frlg/map.bin`:
  61 × `MB_JUMP_SOUTH`, zero facing any other direction.

## Viridian City

`MAP_VIRIDIAN_CITY` · 48 × 40 blocks · Route 1 south, Route 2 north, Route 22 west. **Zero tall
grass tiles**; the wild table is water and fishing only.

| Warp     | Leads to       |
| -------- | -------------- |
| (26, 26) | Pokémon Center |
| (36, 19) | Poké Mart      |
| (25, 18) | Trainer School |
| (25, 11) | House (SPEARY) |
| (36, 10) | Viridian Gym   |

**The road north.** The only way to Route 2 is a three-tile neck at **x = 20–22, y = 11**, with an
impassable ledge row sealing the eastern half of the city at y = 12. While
`VAR_MAP_SCENE_VIRIDIAN_CITY_OLD_MAN` is 0, all three tiles are plugged at once: the old man is
repositioned to lie down at **(21, 11)** (his authored placement is (21, 6)); the woman is placed at
**(20, 12)** on `MOVEMENT_TYPE_FACE_UP`, the only tile you could step north from to reach the left
one; and a coordinate trigger at **(22, 11)** fires `ViridianCity_EventScript_RoadBlocked` — _"I
absolutely forbid you from going through here! This is private property!"_ — and walks the player
back down. The variable goes to 1 the moment Oak's Parcel is handed over.

**The Gym lock.** `ViridianCity_EventScript_TryUnlockGym` runs on every map transition and checks
six flags: `FLAG_KANTO_BADGE_2` through `FLAG_KANTO_BADGE_7` — Cascade, Thunder, Rainbow, Soul,
Marsh and Volcano (badge names from `data/scripts/route23.inc`). Miss any one and the check bails
immediately. The Boulder Badge is not checked, and neither is the Earth Badge, which is the badge
this Gym awards. Until all six are set, stepping onto (36, 11) fires
`ViridianCity_EventScript_GymDoorLocked` and jumps the player two tiles back down the ledge. The
Leader is **Giovanni**; beating him sets `FLAG_KANTO_BADGE_8` and hands over TM26. The old man at
(34, 11) — a different old man — reports the Gym closed until that same six-flag check passes, at
which point he switches to _"Viridian Gym's Leader returned!"_

**The Potion at (17, 5).** `ViridianCity_EventScript_ItemPotion` → `ITEM_POTION`
(`data/scripts/item_ball_scripts_frlg.inc`). A cuttable tree at (18, 5) sits directly beside it,
sealing the short approach from the middle of town, which is why it reads as Cut-gated. It is not.
Blockdata and metatile collision in `data/layouts/ViridianCity_Frlg/map.bin` confirm row 5 runs west
to x = 8 and the column at x = 8 runs south to the western footpath, open from the first visit. The
full walking route is **(23, 31) → (22, 31) → (22, 17) → (8, 17) → (8, 5) → (16, 5)**, then face
east. A second cuttable tree sits at (11, 24).

**The move tutor at (8, 26).** `EventScript_DreamEaterTutor` in `data/scripts/move_tutors_frlg.inc`
teaches Dream Eater free to any eligible Pokémon, with no flag and no gate. Because this build sets
`I_REUSABLE_TMS` to `TRUE` (`include/config/item.h:28`), the tutor's one-time lock is compiled out
of the script entirely and it is repeatable indefinitely.

**The Mart.** First entry runs a scene in which the clerk hands over Oak's Parcel before the shop
opens. Stock afterwards: Poké Ball, Potion, Antidote, Paralyze Heal.

**The catching tutorial.** On the second visit the old man stands at (21, 8) in the wide band north
of the neck. Coordinate triggers at **(20, 8)** and **(22, 8)** fire the demonstration, and talking
to him directly does the same. `StartOldManTutorialBattle` builds a **Weedle, Level 5** in C under
`BATTLE_TYPE_CATCH_TUTORIAL` — not a wild encounter, so it is not caught and it counts for nothing.
He then sets his variable to 2.

## The Parcel payout

Handing Oak the Parcel is the largest single block of progression in the opening segment. It gives
the Pokédex (`FLAG_SYS_POKEDEX_GET`), the DexNav (`FLAG_SYS_DEXNAV_GET`, set by the same script) and
five Poké Balls, and silently flips four scene variables:

| Variable                                     | Effect                                       |
| -------------------------------------------- | -------------------------------------------- |
| `VAR_MAP_SCENE_VIRIDIAN_CITY_OLD_MAN` → 1    | Old man gets up; Viridian's road north opens |
| `VAR_MAP_SCENE_PALLET_TOWN_RIVALS_HOUSE` → 1 | Daisy will now give you the Town Map         |
| `VAR_MAP_SCENE_ROUTE22` → 1                  | Arms the Route 22 rival ambush               |
| `VAR_MAP_SCENE_VIRIDIAN_CITY_MART` → 2       | Mart clerk goes back to selling              |

Daisy's Town Map lives in `data/maps/PalletTown_RivalsHouse_Frlg/scripts.inc` and is keyed to
`VAR_MAP_SCENE_PALLET_TOWN_RIVALS_HOUSE` = 1 — nothing before the Parcel, nothing after it is taken.

**Detector mode is not included.** DexNav's hidden-encounter half is gated on
`DN_FLAG_DETECTOR_MODE` (`include/config/dexnav.h`), set in `src/post_battle_event_funcs.c` on the
first Hall of Fame in any region. Route 1's hidden table is Bulbasaur 60% / Squirtle 35% /
Caterpie 5% at Lv 6–8.

## Route 22

`MAP_ROUTE22` · 48 × 24 blocks · enter from Viridian's west edge · exits north to Route 23.

`sRoute22_FireRed` `land_mons`, step-encounter rate 21.

| Species | Total | Levels |
| ------- | ----: | ------ |
| Rattata |   45% | 2–5    |
| Mankey  |   45% | 2–5    |
| Spearow |   10% | 3, 5   |

Two grass patches, both narrow: **(15–21, 9–13)** west of the pond and **(34–39, 9–13)** just below
the rival's ambush point. Mankey's learnset (`data/generated/species.json`) gives Low Kick at Level 8
and Seismic Toss at Level 12; Fighting hits Rock for double damage on this build's type chart
(`src/data/types_info.h`).

The pond at (22–27, 8–11) — 24 water tiles — holds Psyduck at Lv 20–40 on the surf table. Fishing
runs Magikarp on the Old Rod; Poliwag / Magikarp / Goldeen on the Good Rod; Poliwag / Poliwhirl /
Gyarados / Psyduck on the Super Rod.

**North gate.** `MAP_ROUTE22_NORTH_ENTRANCE` (warps at (8, 5) and (9, 5) on Route 22) is guarded by
`Route22_NorthEntrance_EventScript_BoulderBadgeGuard`, which checks `FLAG_KANTO_BADGE_1`. This is
the first of eight badge checks on the road to the League; the rest are on Route 23.

**Rival battle 2.** Coordinate triggers at **(33, 4)**, **(33, 5)** and **(33, 6)** fire
`Route22_EventScript_EarlyRivalTrigger*` at `VAR_MAP_SCENE_ROUTE22` = 1. Both mons are **Level 9**
with IVs authored at **6** flat; EVs and Nature are unspecified in the source. The lead is
**Pidgey, Lv 9 — Tackle, Sand-Attack** in all three versions.

| Your starter | `VAR_STARTER_MON` | Blue's second    | Moves             |
| ------------ | :---------------: | ---------------- | ----------------- |
| Bulbasaur    |         0         | Charmander, Lv 9 | Scratch, Growl    |
| Squirtle     |         1         | Bulbasaur, Lv 9  | Tackle, Growl     |
| Charmander   |         2         | Squirtle, Lv 9   | Tackle, Tail Whip |

Blue's starter is authored with its **Level 1 moves only**, at Level 9, in all three versions —
explicit move lists in `src/data/trainers_frlg.party` (via `data/generated/trainers.json`), not
engine defaults. Charmander therefore lacks Ember (Level 4), Bulbasaur lacks Vine Whip (Level 3) and
Squirtle lacks Water Gun (Level 3), so none of Blue's three possible starters can attack with its
own type. The player's starter, at Level 9, has learned its type move.

This battle is called with flags of **0** through `src/battle_setup.c`'s
`TRAINER_BATTLE_EARLY_RIVAL` handling, which sends a defeated player straight to `CB2_WhiteOut` —
the opposite of the lab battle above, where `RIVAL_BATTLE_HEAL_AFTER` is set.

Winning sets `VAR_MAP_SCENE_ROUTE22` to 2, which is one of **three** conditions on Oak's second
five Poké Balls — a pity mechanic, not a reward, which is why the chapter does not send anyone back
for it. All of `data/maps/PalletTown_ProfessorOaksLab_Frlg/scripts.inc`:

| Condition                           | Where                                                   |
| ----------------------------------- | ------------------------------------------------------- |
| Kanto caught count is **exactly 1** | `RatePokedexOrTryGiveBalls`, `goto_if_eq VAR_0x8009, 1` |
| The bag holds **zero** Poké Balls   | `CheckIfPlayerNeedsBalls`, `checkitem ITEM_POKE_BALL`   |
| `VAR_MAP_SCENE_ROUTE22` **>= 2**    | `PlayerOutOfBalls`, `goto_if_ge`                        |

`VAR_0x8009` is `GetKantoPokedexCount(FLAG_GET_CAUGHT)`, copied from `VAR_0x8006` by
`GetFrlgPokedexCount` (`src/birch_pc.c:92-98`). Any other caught count goes to `RatePokedex`
instead, and a player who is holding even one ball goes to `MonsAroundWorldWait`. Only then does
`GivePlayerMoreBalls` run and set `FLAG_GOT_POKEBALLS_FROM_OAK_AFTER_22_RIVAL`, once. The chapter's
own steps catch two starters and a Mankey, which is four caught with balls in the bag, so following
this guide makes the gift unreachable by construction.

**The rematch.** The same three trigger tiles carry `Route22_EventScript_LateRivalTrigger*` at
`VAR_MAP_SCENE_ROUTE22` = 3, set on defeating Giovanni in Viridian Gym. Blue returns with six
Pokémon in the mid-40s to low-50s — Pidgeot 47, Rhyhorn 45, Alakazam 47 and a fully evolved starter
at 53, with the middle two slots varying by the player's pick.

## Field-move gating

- **Cut** unlocks in Kanto on the **Cascade Badge** (badge index 1, Cerulean City), or immediately
  while carrying the **Cut Tool** item, which bypasses the badge gate entirely
  (`src/field_move.c`, `include/config/qol_field_moves.h`). This build also lets any Pokémon that
  merely _could_ learn Cut perform it untaught.
- **Surf** is gated on the **Soul Badge** (badge index 4) or the Surf Tool.

## Route 2 (lookahead)

`sRoute2_FireRed` `land_mons`, step-encounter rate 21: Rattata 45% and Pidgey 45% at Lv 2-5,
Caterpie 5% and Weedle 5% at **Lv 4-5** (4% at Lv 4, 1% at Lv 5 each). The chapter's "where you go
next" section states the bug levels separately for this reason.

## Chapter `sections:` schema

The contract every chapter inherits. A chapter's frontmatter carries an ordered `sections:` list.
Each section is one map. Sections follow play order; a map may appear in more than one section
(Viridian City appears three times in this chapter).

| Key     | Required | Meaning                                                                                             |
| ------- | -------- | --------------------------------------------------------------------------------------------------- |
| `id`    | yes      | Stable slug, unique within the chapter. Anchor target.                                              |
| `map`   | yes      | One `MAP_*` id. Every `at:` in the section is local to this map. Never mix maps in a section.       |
| `title` | yes      | Section heading.                                                                                    |
| `note`  | no       | One paragraph of plain text. Scene-setting and facts that are not actions. No code, no coordinates. |
| `steps` | yes      | Ordered list. One action per step.                                                                  |

A step is either a plain string, or a mapping:

| Key            | Required                              | Meaning                                                                                                                                                        |
| -------------- | ------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `text`         | yes                                   | The instruction. Second person, one action.                                                                                                                    |
| `at`           | no                                    | `[x, y]` block coordinate on the section's `map`. Becomes a numbered pin whose number is the step's number. Omit when the step has no single meaningful point. |
| `choice`       | no                                    | Marks the step as one alternative in a group. Value is the group's kind — see below.                                                                           |
| `choice_group` | **yes, whenever `choice` is present** | Free-form slug naming the group this alternative belongs to.                                                                                                   |

The chapter itself carries **no** key pointing at this page. The relation is declared in one
direction only, by `technical_to:` here, exactly as the Insider Tips file declares `companion_to:`.
The renderer finds this page by scanning for a `technical_to` that resolves to the chapter.

### `choice:` — mutually exclusive steps

A **group** is a maximal run of consecutive steps sharing the same `choice_group` slug. Every step
in a group must carry the same `choice` value; a mismatch is invalid content. The reader does
exactly one step in the group, then continues at the next step outside it.

Grouping is **explicit, never positional.** `choice_group` is required on every step that carries
`choice`, which costs one line and removes the only failure class the schema had: if grouping were
inferred from adjacency, an author who forgot to separate two neighbouring same-kind groups would
silently get one group of four alternatives, and no validator could catch it, because a group of
four is legal content. With the slug required, the two groups are distinct by construction and a
mismatch is a detectable error rather than a silent one.

`choice` takes a **string**, not a boolean, because two different relations need two different
labels:

| Value     | Means                                   | Renderer label               | Example                                           |
| --------- | --------------------------------------- | ---------------------------- | ------------------------------------------------- |
| `pick`    | Choose one, here, now.                  | "Pick one:"                  | The three starter balls                           |
| `depends` | Whichever you already chose, hours ago. | "Depending on your starter:" | "If you picked Bulbasaur, Blue leads Charmander…" |
| `true`    | Deprecated alias for `pick`.            | "Pick one:"                  | —                                                 |

`depends` is not a decision the reader makes at that step; it is the consequence of one made
earlier, and "Pick one:" is the wrong words for it. That shape recurs on every rival page, every
gym counter table and every league page, which is why the kind is part of the value rather than
hard-coded to a single flag.

Rules:

- Numbering does **not** restart or collapse. Each alternative keeps its own step number and its
  own pin, because the alternatives are simultaneously real places on the map — the three starter
  balls sit side by side at (8, 4), (9, 4) and (10, 4) and a reader needs to see all three before
  choosing.
- The label is supplied by the renderer, keyed off the `choice` value. There is no label key.
- One level only. A `choice` step may not contain nested steps.
- A renderer that ignores both keys still emits correct, readable output: the alternatives render
  as ordinary consecutive steps. The keys add grouping; they never change step identity, numbering
  or pins.

**Adjacent groups** need no special handling: the slugs differ, so the groups differ. A fork that
immediately forks again with no meaningful action between is a real shape (Victory Road's stairs
then doors; the Safari Zone), and it needs no filler step to express. `choice_group` is scoped to
its section and its value is never displayed:

```yaml
- text: Take the left stairs.
  choice: pick
  choice_group: stairs
- text: Take the right stairs.
  choice: pick
  choice_group: stairs
- text: Go through the upper door.
  choice: pick
  choice_group: doors
- text: Go through the lower door.
  choice: pick
  choice_group: doors
```

A **section boundary also ends a run**, structurally — a group never spans two sections.

**The four edge cases, specified:**

| Case                                        | Ruling                                                                                                                                                                                                                                                                                                                                 |
| ------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| A group of one (a lone `choice` step)       | **Invalid content.** "Pick one:" over a single option is nonsense. A validator should reject it; a renderer that meets one anyway must render it as an ordinary step with no label, never crash.                                                                                                                                       |
| A group that is the last thing in a section | **Legal.** The continuation is the next section. The renderer closes the group at the section boundary.                                                                                                                                                                                                                                |
| `choice: false`                             | **Forbidden.** Omit the key instead — one spelling of "not a choice", not two. A renderer must treat it as absent.                                                                                                                                                                                                                     |
| A plain-string step inside a group          | **Impossible by construction.** Plain strings carry no keys, so every alternative is necessarily a mapping with `text`.                                                                                                                                                                                                                |
| `choice_group` present without `choice`     | **Forbidden, and ignored if met.** The key only has meaning as a grouping for alternatives. Without this rule, two ordinary steps sharing a slug would form a "group" of non-choices, and a `choice_group` step next to a real alternative would fail to join it. A renderer must treat the key as absent and render an ordinary step. |
| An unrecognised `choice` value              | **Group it, do not label it.** A value from a future revision still groups its run by `choice_group` and renders with no label — never crash, never drop the step. This is what keeps the contract forward compatible for three regions writing against it.                                                                            |

Used once in this chapter: `choice: pick` with `choice_group: starter` on the three starter balls
in Oak's Lab.

### Two house rules for pins

1. **When the data cannot confirm a pin, ship the step without one.** The step still gets its
   number; it just gets no pin. This is why the step leaving Viridian for Route 22 is unpinned —
   no collision data exists to confirm which tile on the city's west edge is walkable.
2. **A pin the data _does_ confirm still has to be checked against approach direction.** A
   coordinate can be a real, verified feature and still be the wrong pin. Route 22's western grass
   patch centre (18, 11) is a genuine grass tile, and it was wrong: the player arrives from
   Viridian on Route 22's **east** edge, so the patch they meet first is the eastern one at
   (34-39, 9-13). Pinning (18, 11) also made the section run backwards, since the rival trigger at
   x = 33 is east of x = 18 but the step said "keep going west".

### The markdown body, and what may not go in it

Everything in `sections:` renders **above** the whole markdown body, and the body cannot be split
around it. That is deliberate — it is how a printed chapter is set: the walk, then the reference
material a reader consults while walking, then what you cannot reach yet, then where you go next,
then the departure checklist — but it makes one authoring rule binding rather than stylistic:

> **An instruction belongs in `sections:` as a step. The body opens with scene-setting and never
> tells the reader to do anything.**

A sentence in the body that says "go and do X" is printed after every step in the chapter, however
early in the walk it belongs, and it gets no number and no pin. There is no renderer setting that
rescues it; move it into `sections:`. The body's job is the things that are true of the whole
segment: what lives in the grass, what the badges gate, what is ahead.

The body's `<h2>` sections then fold or stay open **mechanically**, so no per-chapter list has to
be kept:

| Section                           | Renders                                                                               |
| --------------------------------- | ------------------------------------------------------------------------------------- |
| Contains table rows or any `<li>` | **Closed fold**, its summary counting exactly those rows.                             |
| Prose only                        | **Open.** There is no count to summarise.                                             |
| Contains a `- [ ]` task list      | **Open**, and made tickable. The checklist is the chapter's exit gate, not reference. |
| Last section before the checklist | **Open**, whatever it contains — see below.                                           |

**The handoff never folds, and it is chosen by position, not by its heading.** The section that
tells the reader where to go next must never sit behind a click, and the fold rule above would put
it there the moment it carried two bullet points — silently, because a fold looks exactly like an
open section until you notice the chevron. So the renderer exempts **the last body section before
the departure checklist**, or the last section outright in a chapter that has no checklist.

It is positional because it cannot be lexical: this chapter's handoff is headed "What is ahead on
Route 2", and across 45-58 chapters that heading will be named after wherever the reader is being
sent. A vocabulary of headings would have failed on the only chapter that existed when the rule was
written. **Put the handoff last, before the checklist**, and it is protected without you doing
anything; put a reference section after it and the handoff folds again while that reference section
stays open — which is more scrolling, not a hidden instruction.

## Derived step pins

Three `at:` pins in the chapter are not authored coordinates. The source records these places as
rectangles or as a span, never as a point, so each pin is derived by an explicit rule:

**The rule: floor of the midpoint.** For a rectangle `(x0-x1, y0-y1)` the pin is
`((x0+x1)//2, (y0+y1)//2)`, integer division, so it is reproducible and checkable rather than
eyeballed.

| Pin                    | Derived from                                        | Rule applied            | Traceable to                                                                                                                               |
| ---------------------- | --------------------------------------------------- | ----------------------- | ------------------------------------------------------------------------------------------------------------------------------------------ |
| Route 1 (12, 37)       | grass column (12-13, 35-39)                         | (12+13)//2, (35+39)//2  | `data/layouts/Route1_Frlg/map.bin`                                                                                                         |
| Route 22 (36, 11)      | eastern grass patch (34-39, 9-13)                   | (34+39)//2, (9+13)//2   | `data/layouts/Route22_Frlg/map.bin`                                                                                                        |
| Viridian City (21, 11) | the three-tile road-north neck at x = 20-22, y = 11 | middle tile of the span | `data/layouts/ViridianCity_Frlg/map.bin`, plus the trigger at (22, 11) and the woman at (20, 12) in `data/maps/ViridianCity_Frlg/map.json` |

**Caveat.** These centres are _assumed_ walkable because the source records the enclosing rectangle
or span as grass or as open road. No collision or blockdata exists anywhere in `data/generated/` —
the full key set per map is dimensions, warps, object_events, signs, hidden_items, coord_triggers,
connections, encounters and metadata — so the individual tile cannot be confirmed from generated
data. Confirming one requires the layout `map.bin` files cited above.

Two further checks were made on the derived pins that the rule alone does not cover:

- **Route 1 (12, 37) approach.** Pallet Town connects `up -> MAP_ROUTE1, offset 0`, and Pallet's
  north-exit triggers are at (12, 1) and (13, 1), so the player enters Route 1 at x = 12-13,
  y = 39 — inside the (12-13, 35-39) column. "The first tall grass is right at the town's edge" is
  literally true.
- **Route 22 (36, 11) approach.** Viridian connects `left -> MAP_ROUTE22, offset 10` and Route 22
  connects `right -> MAP_VIRIDIAN_CITY, offset -10`. Both agree, so the player arrives on Route
  22's east edge and meets (34-39, 9-13) first, eight tiles in; the western patch is twenty-six
  tiles in, past the rival.

Every other pin in the chapter lands on a warp, object event, sign or coordinate trigger, or is one
of the six waypoints on the Viridian Potion walking route recorded above.
