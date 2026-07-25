---
title: "Pallet Town to Route 22"
region: kanto
maps:
  - MAP_PALLET_TOWN
  - MAP_PALLET_TOWN_PLAYERS_HOUSE_1F
  - MAP_PALLET_TOWN_PLAYERS_HOUSE_2F
  - MAP_PALLET_TOWN_RIVALS_HOUSE
  - MAP_PALLET_TOWN_PROFESSOR_OAKS_LAB
  - MAP_ROUTE1
  - MAP_VIRIDIAN_CITY
  - MAP_VIRIDIAN_CITY_MART
  - MAP_VIRIDIAN_CITY_POKEMON_CENTER_1F
  - MAP_VIRIDIAN_CITY_HOUSE
  - MAP_VIRIDIAN_CITY_SCHOOL
  - MAP_VIRIDIAN_CITY_GYM
  - MAP_ROUTE22
  - MAP_ROUTE22_NORTH_ENTRANCE
entry_from: MAP_REGION_HUB
gate: kanto:badge-1
gate_note: >-
  Pre-badge content. It is ordered before kanto:badge-1 but is not gated by it;
  progression.json at 9ee61fbd has no pre-badge-1 gate key.
severity: story
---

# Pallet Town to Route 22

## Before anything else: you do not start in Pallet Town

A new game does not open in a bedroom. It opens in the **World Transit hub**, on the departure
concourse at tile (16, 4) — `WarpToTruck()` in `src/new_game.c:155` sends every new save to
`MAP_REGION_HUB` under this build's `ALL_REGIONS` path. Your starting region stays unset until you
talk to a gate attendant. Three of them stand shoulder to shoulder on the concourse — Kanto at
(11, 2), Johto at (16, 2), Hoenn at (21, 2) — and **none of them checks a flag.** All three regions
are open on turn one. The fourth attendant on that row, at (4, 2), is the Battle Frontier gate, and
that one _is_ locked.

Talk to the Kanto attendant. He hands you the **Hub Pass** (`ITEM_HUB_RETURN`) — a key item that
warps you one way back to the hub from the field — then drops you into
`MAP_PALLET_TOWN_PLAYERS_HOUSE_2F` at (6, 6). That is your bedroom, and stepping into it for the
first time sets your respawn point to Pallet Town.

Two things to understand before you commit:

- **Crossing a gate empties your party.** `RegionHub_ScrEnterRegion` calls `DepositPartyToPC()` any
  time the target region differs from your current one (`src/region_switch.c`). On a brand-new save
  your party is already empty, so it costs you nothing. If you come to Kanto later carrying a Hoenn
  or Johto team, that team goes to the PC and you walk into Pallet Town with nothing.
- **The gate remembers.** Once Kanto's intro is done, the same attendant stops routing you to Pallet
  Town and drops you at **Vermilion City** instead (`RegionHub_EventScript_ReturnKanto`). Your first
  arrival is the only one that starts here.

Walk downstairs. Mom delivers the "all boys leave home someday" line and points you at Oak. If you
came in from another region, she opens with a different line first — a one-shot arrival scene fires
on Pallet Town's frame table and she tells you this is _our new home in Pallet Town, Kanto_. That
scene is armed by `RegionHub_ScrArmArrival` and never plays twice.

## Pallet Town

`MAP_PALLET_TOWN` · 24 × 20 blocks · no wild grass anywhere on the map

Three doors, all on the east and centre of town:

| Warp     | Leads to            |
| -------- | ------------------- |
| (6, 7)   | Your house, 1F      |
| (15, 7)  | Rival's house       |
| (16, 13) | Professor Oak's Lab |

There is **no Poké Mart and no Pokémon Center in Pallet Town.** The nearest of either is Viridian
City, a full route north. Your only free heal here is Mom, and she does not offer it until you have
beaten your rival inside the lab (`FLAG_BEAT_RIVAL_IN_OAKS_LAB`). After that she heals your whole
party on demand, forever, for nothing.

Try to leave north and you will be stopped. Two coordinate triggers sit at **(12, 1)** and
**(13, 1)** — the whole width of the Route 1 exit — and while `VAR_MAP_SCENE_PALLET_TOWN_OAK` is 0
they fire `PalletTown_EventScript_OakTrigger`. Oak shouts, walks on screen, tells you the tall grass
is unsafe, and marches you into the lab. You cannot skip it and there is no reason to try.

The woman wandering near (3, 10) is the sign lady. Read the Trainer Tips sign at (5, 14) yourself
and she stops bothering you about it. She is pure flavour.

## Oak's Lab: pick your starter

`MAP_PALLET_TOWN_PROFESSOR_OAKS_LAB`

Three Poké Balls sit on the table. **This is a physical pick, not a menu.** Kanto does not use the
game's `ChooseStarter` selection screen at all — that special is called from exactly one place in the
entire game, `data/maps/Route101/scripts.inc:228`, which is Hoenn's. In Kanto you walk up to a ball
and talk to it.

Each ball sets an index that the whole campaign reads back:

| Ball       | `VAR_STARTER_MON` | You get          | **Blue takes** |
| ---------- | :---------------: | ---------------- | -------------- |
| Bulbasaur  |         0         | Bulbasaur, Lv 5  | **Charmander** |
| Squirtle   |         1         | Squirtle, Lv 5   | **Bulbasaur**  |
| Charmander |         2         | Charmander, Lv 5 | **Squirtle**   |

Blue always takes the one that beats yours. That pairing is hard-wired in the ball scripts — each
one sets `RIVAL_STARTER_SPECIES` in the same breath as yours — and it decides every rival battle you
will fight for the rest of the Kanto campaign, including both fights on Route 22.

Say yes and you get your Pokémon at **Level 5**, plus the offer to nickname it. Blue then walks to
his ball, takes it, and challenges you on the spot.

### Rival battle 1 — Oak's Lab

One Pokémon, Level 5, IVs authored flat at **0** across all six stats. EVs and Nature are unset in
the source, so the engine supplies them — do not read anything into them.

| Your starter | Blue leads | Level | Moves             |
| ------------ | ---------- | :---: | ----------------- |
| Bulbasaur    | Charmander |   5   | Scratch, Growl    |
| Squirtle     | Bulbasaur  |   5   | Tackle, Growl     |
| Charmander   | Squirtle   |   5   | Tackle, Tail Whip |

**You cannot lose this one.** The script passes `RIVAL_BATTLE_TUTORIAL`, which carries the
heal-after bit; `src/battle_setup.c` heals your party and continues instead of whiting you out.
Swing away.

Now leave. Oak has nothing more for you until you have been to Viridian.

## Route 1

`MAP_ROUTE1` · 24 × 40 blocks · connects down to Pallet Town, up to Viridian City

**178 tiles of tall grass**, more than any other map in this segment. Working north from the Pallet
end: a narrow column at **(12–13, 35–39)** right at the entrance, then a wide double band across
rows 32–35 — west side **(2–10, 32–35)**, east side **(15–21, 32–35)** — then **(12–17, 24–28)** in
the middle, **(16–21, 13–17)**, and the big top patch at **(10–21, 6–10)** just short of Viridian.

### What is in the grass

`land_mons`, step-encounter rate 21. Slot percentages are the engine's standard land spread and sum
to exactly 100.

| Species        | Total | Levels | Slots                                         |
| -------------- | ----: | ------ | --------------------------------------------- |
| **Rattata**    |   40% | 2–4    | 20% Lv 3, 10% Lv 2, 5% Lv 3, 4% Lv 4, 1% Lv 4 |
| **Pidgey**     |   30% | 3–5    | 20% Lv 3, 5% Lv 3, 4% Lv 4, 1% Lv 5           |
| **Bulbasaur**  |   10% | 3      | 10% Lv 3                                      |
| **Charmander** |   10% | 3      | 10% Lv 3                                      |
| **Squirtle**   |   10% | 2      | 10% Lv 2                                      |

Read that table again. **All three Kanto starters are wild on Route 1**, at a combined 30% of every
grass encounter. This is not FireRed. You can own the entire trio before you have seen Viridian
City. They come in under-levelled — Bulbasaur and Charmander at Level 3, Squirtle at Level 2,
against the Level 5 you were handed — but a few trips through the same grass closes that instantly.

The catch: you have no Poké Balls. Oak does not hand them over until you come back with his Parcel.
So on the way north, note where the grass is and keep walking. Come back for the starters after the
lab pays out.

### Items and people

There is **no item ball and no hidden item on Route 1.** The whole route carries one sign, two NPCs
and nothing else. What it does have is a giveaway:

- **Poké Mart clerk, (6, 28)** — hands you a free **Potion**, once, guarded by
  `FLAG_GOT_POTION_ON_ROUTE_1`. Talk to him. He is a plain overworld NPC with no marker of any kind
  and it is trivially easy to walk past him.
- **Boy, (19, 16)** — tells you about the ledges. He is right. All **61** jump tiles on Route 1 face
  **south**, in bands at rows 5, 10, 15, 20, 26 and 31. Northbound they are walls; southbound they
  are a slide. Coming back to Pallet is far faster than going up.
- **Route sign, (9, 31)**.

## Viridian City

`MAP_VIRIDIAN_CITY` · 48 × 40 blocks · Route 1 south, Route 2 north, Route 22 west

Viridian has **zero tall grass tiles.** Its wild table is water and fishing only, and you have
neither Surf nor a rod, so there is nothing to catch here yet. Do not waste steps looking.

| Warp     | Leads to                  |
| -------- | ------------------------- |
| (26, 26) | Pokémon Center            |
| (36, 19) | Poké Mart                 |
| (25, 18) | Trainer School            |
| (25, 11) | House (the Spearow)       |
| (36, 10) | **Viridian Gym — locked** |

### The road north is closed, and it is closed properly

The only way to Route 2 is a three-tile neck at **x = 20–22, y = 11**, with an impassable ledge row
sealing the eastern half of the city at y = 12. While `VAR_MAP_SCENE_VIRIDIAN_CITY_OLD_MAN` is 0,
the game plugs all three tiles at once:

- The old man is repositioned to lie down at **(21, 11)**, taking the middle tile.
- The woman is placed at **(20, 12)** on `MOVEMENT_TYPE_FACE_UP`, which is the only tile you could
  step north from to reach the left one.
- A coordinate trigger at **(22, 11)** fires `ViridianCity_EventScript_RoadBlocked` — _"I absolutely
  forbid you from going through here! This is private property!"_ — and walks you back down.

Three tiles, three obstructions, no gap. The road opens when Oak sets that variable to 1, which
happens the moment you hand over his Parcel.

### The Gym is not your problem yet

`ViridianCity_EventScript_TryUnlockGym` runs on every map transition and checks **six flags**:
`FLAG_KANTO_BADGE_2` through `FLAG_KANTO_BADGE_7` — Cascade, Thunder, Rainbow, Soul, Marsh and
Volcano. Miss any one and the check bails immediately. Note what is _not_ in the list: the Boulder
Badge is not checked, and neither is the Earth Badge, which is the one this Gym awards.

Until all six are set, stepping onto (36, 11) tells you the doors are locked and jumps you two tiles
back down the ledge. The Gym Leader is **Giovanni**, and beating him sets `FLAG_KANTO_BADGE_8` and
hands over TM26. That is a long way from here.

The old man at (34, 11) — a different old man, do not confuse them — will keep telling you the Gym
is always closed until that six-badge check passes, at which point he switches to "Viridian Gym's
Leader returned!"

### The Poké Mart, and your actual objective

Walk in for the first time and the clerk stops you before you can shop. He mistakes you for Oak's
delivery and hands you **Oak's Parcel**. That is the errand. Everything else in this town waits on
it.

Once the scene is done he sells:

| Viridian Poké Mart |
| ------------------ |
| Poké Ball          |
| Potion             |
| Antidote           |
| Paralyze Heal      |

Four items. That is the whole list. You will not have much money yet, but Poké Balls are the entire
point of coming back here.

### Worth the detour while you are in town

- **Pokémon Center, (26, 26)** — your first heal point and your first PC access outside your own
  bedroom. The PC is shared across all three regions; the hub script calls it "the headline
  feature", and it is the same box your party lands in when you cross a region gate.
- **Trainer School, (25, 18)** — two blackboards, a notebook and a Pokémon journal, all read-only
  text. Free refresher, no items.
- **House, (25, 11)** — a Spearow named SPEARY and a nickname lecture. Flavour only.
- **The man at (8, 26) is a move tutor.** See the tips sheet. He is not marked, he is standing in the
  open from the moment you arrive, and almost nobody talks to him.

### The Potion nobody picks up

There is an **item ball at (17, 5)** holding a **Potion**. It sits on the far west end of a one-tile
corridor along row 5, and a **cuttable tree at (18, 5)** stands directly beside it, sealing the
short approach from the middle of town. Every instinct says _come back with Cut_.

**Don't.** The tree is a shortcut, not a gate. Row 5 runs all the way west to x = 8, and the column
at x = 8 runs south to the city's western footpath, which is open from your first visit. The long
way round works with no badges, no HMs and no tools:

> From the Route 1 entrance, head north up the east side to about **(23, 31)**, step west to
> **(22, 31)**, then north through the gap in the ledge row to **(22, 17)**. Turn west along the
> footpath to **(8, 17)**, north up the western column to **(8, 5)**, then east along the top
> corridor to **(16, 5)**. Face east and open the ball.

The tree at (18, 5) only saves you the walk. Cut it later if you like; the Potion is yours now.

## Back to Pallet Town: the payout

Take the Parcel to Oak. This one scene is the largest single block of progression in the opening
segment. Handing it over gives you:

- The **Pokédex** — sets `FLAG_SYS_POKEDEX_GET`.
- **DexNav** — the same script sets `FLAG_SYS_DEXNAV_GET`, so DexNav appears in your Start menu
  immediately. Detector mode, which finds hidden Pokémon, does _not_ unlock here.
- **5 Poké Balls.**

and it silently flips four scene variables at once:

| Variable                                     | Effect                                       |
| -------------------------------------------- | -------------------------------------------- |
| `VAR_MAP_SCENE_VIRIDIAN_CITY_OLD_MAN` → 1    | Old man gets up; Viridian's road north opens |
| `VAR_MAP_SCENE_PALLET_TOWN_RIVALS_HOUSE` → 1 | **Daisy will now give you the Town Map**     |
| `VAR_MAP_SCENE_ROUTE22` → 1                  | Arms the Route 22 rival ambush               |
| `VAR_MAP_SCENE_VIRIDIAN_CITY_MART` → 2       | Mart clerk goes back to selling              |

**Go next door before you leave town.** Blue's sister Daisy hands over the **Town Map** for free,
and she does it only in this window — she says nothing useful before the Parcel scene and nothing
useful after you have taken it. Nothing in the game tells you to visit her.

Then take your five Poké Balls straight back to Route 1's grass and catch the two starters you
passed on.

## Viridian City, second visit: the catching tutorial

The old man is now standing at (21, 8), in the wide-open band north of the neck. Walk past him at
either **(20, 8)** or **(22, 8)** and he grabs you for the catching demonstration. He borrows the
screen and catches a **Weedle, Level 5** — a scripted mon built in C for this one battle
(`StartOldManTutorialBattle`, `BATTLE_TYPE_CATCH_TUTORIAL`), not a wild encounter, so it is not
yours and it does not count for anything. Then he sets his variable to 2. Talking to him directly
does the same thing.

It costs you nothing and it is unskippable if you walk the middle of the road, so take it. After
that the road north to Route 2 and Viridian Forest is genuinely clear.

## Route 22

`MAP_ROUTE22` · 48 × 24 blocks · enter from Viridian's west edge · exits north to Route 23

This is a side trip. The League is up there and you are not going. Go anyway — there is a rival
battle here that is worth real experience, and it is easy to miss because nothing points you west.

### What is in the grass

`land_mons`, step-encounter rate 21.

| Species     | Total | Levels |
| ----------- | ----: | ------ |
| **Rattata** |   45% | 2–5    |
| **Mankey**  |   45% | 2–5    |
| **Spearow** |   10% | 3, 5   |

Two grass patches, both narrow: **(15–21, 9–13)** west of the pond, and **(34–39, 9–13)** just below
the rival's ambush point. **Mankey is the reason to come.** It appears nowhere on Route 1 and
nowhere in Viridian, and at 45% you will have one inside a couple of minutes. It learns **Low Kick
at Level 8** and **Seismic Toss at Level 12**, and Fighting hits Rock for double damage on this
build's type chart — which makes a Route 22 Mankey the best answer available to Pewter Gym, and you
can have it before you have ever set foot in Viridian Forest.

The pond at (22–27, 8–11) — 24 water tiles — holds **Psyduck at Lv 20–40** on the surf table, and the
fishing table runs Magikarp on the Old Rod, Poliwag / Magikarp / Goldeen on the Good Rod, and
Poliwag / Poliwhirl / Gyarados / Psyduck on the Super Rod. You need Surf or a rod for any of it, and
you have neither.

### The north gate is shut

The building at the top-left, `MAP_ROUTE22_NORTH_ENTRANCE`, is guarded by a policeman who checks
`FLAG_KANTO_BADGE_1` — the **Boulder Badge**. Without it he plays the rejection sound and walks you
back out. This is the first of eight badge checks on the road to the League; the rest are on
Route 23.

### Rival battle 2 — Route 22

Cross **(33, 4)**, **(33, 5)** or **(33, 6)** and Blue jogs in from the west. He has two Pokémon now.

Both mons are **Level 9** with IVs authored at **6** flat. EVs and Nature are unspecified in the
source. His lead is the same in all three versions:

**Pidgey, Lv 9 — Tackle, Sand-Attack.**

Only the second slot changes, and it is the one Blue took from the lab:

| Your starter   | `VAR_STARTER_MON` | Blue's second    | Moves             |
| -------------- | :---------------: | ---------------- | ----------------- |
| **Bulbasaur**  |         0         | Charmander, Lv 9 | Scratch, Growl    |
| **Squirtle**   |         1         | Bulbasaur, Lv 9  | Tackle, Growl     |
| **Charmander** |         2         | Squirtle, Lv 9   | Tackle, Tail Whip |

**How the matchup actually plays.** Look at the move lists, not the type chart. Blue's starter is
authored with its **Level 1 moves only**, at Level 9, in all three versions. Charmander has Scratch
and Growl and _not_ Ember, which it learns at Level 4. Bulbasaur has Tackle and Growl and not Vine
Whip, learned at Level 3. Squirtle has Tackle and Tail Whip and not Water Gun, learned at Level 3.
These are explicit move lists in `trainers_frlg.party`, not engine defaults.

The consequence: **not one of Blue's three possible starters can hit you with its own type.** Every
attack he has is a Normal-type physical move. The type advantage he holds over you exists only on
the roster sheet, and he cannot use it. Meanwhile _your_ starter has its own type move — Vine Whip
at 3, Water Gun at 3, Ember at 4 — and can.

What that means per pick:

- **You picked Bulbasaur.** Blue's Charmander throws Scratch and nothing else that matters. Vine
  Whip is neutral into a Fire type but it is a real attack against his Normal chip damage. Cleanest
  of the three.
- **You picked Charmander.** Blue's Squirtle throws Tackle. Ember out-damages it outright and you win
  the straight race. Tail Whip only matters if you let it stack three or four deep.
- **You picked Squirtle.** The slowest of the three. Water Gun is resisted by Grass, so you are
  grinding a Bulbasaur down while it stacks Growl on you. Bring a second Pokémon — a Route 1 Pidgey
  or Rattata, or better, a Mankey — and let it do the work.

In every version, **Sand-Attack from the Pidgey is the actual threat.** It is the only move in
Blue's party that can lose you the fight, and it does it by stacking accuracy drops until your
attacks stop landing. Kill the Pidgey first, and if you take two Sand-Attacks early, switch out
rather than swing through it.

> **This one white-outs you.** The lab battle carried the heal-after flag. This one is called with
> flags of **0**, and `src/battle_setup.c` sends a defeated player straight to `CB2_WhiteOut`.
> Heal at the Viridian Pokémon Center before you walk west.

Beat him and `VAR_MAP_SCENE_ROUTE22` goes to 2. That does two things: it retires the ambush, and it
unlocks a second gift from Oak. **Go back and talk to him** — with the variable at 2 or higher he
hands over another **5 Poké Balls**, once, on `FLAG_GOT_POKEBALLS_FROM_OAK_AFTER_22_RIVAL`. It is
buried behind a "you've added nothing to the Pokédex" line and nothing in the game suggests the trip.

### The rematch you are not seeing yet

The same three trigger tiles carry a **second** rival battle at `VAR_MAP_SCENE_ROUTE22` = 3, which
is set when you defeat Giovanni in Viridian Gym. Blue comes back with six Pokémon in the mid-40s to
low-50s — Pidgeot 47, Rhyhorn 45, Alakazam 47 and a fully evolved starter at 53, with the middle two
slots varying by your pick. Note it and come back much later.

## What you cannot reach yet

An honest ledger of everything in this segment that is visible and locked:

| Thing                          | Where                                              | Needs                                                                                                                                                                                                                                                                                                                                                 |
| ------------------------------ | -------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Shortcut to the row-5 corridor | Viridian City, (18, 5)                             | **Cut** — which in Kanto unlocks on the **Cascade Badge** (badge index 1, Cerulean City), or immediately if you are carrying the **Cut Tool** item, which bypasses the badge gate entirely. This build also lets any Pokémon that merely _could_ learn Cut perform it untaught. The Potion behind it is reachable now; only the short walk is locked. |
| Route 22 pond, Viridian water  | Psyduck Lv 20–40                                   | Surf — Kanto's Surf is gated on the **Soul Badge** (badge index 4) or the Surf Tool                                                                                                                                                                                                                                                                   |
| All fishing tables             | Pallet, Viridian, Route 22                         | A rod                                                                                                                                                                                                                                                                                                                                                 |
| Route 1 hidden encounters      | Bulbasaur 60% / Squirtle 35% / Caterpie 5%, Lv 6–8 | **DexNav detector mode**, which unlocks on your first Hall of Fame in any region. You have the DexNav from the Pokédex, but not this.                                                                                                                                                                                                                 |
| Viridian Gym                   | (36, 10)                                           | Kanto badges 2–7                                                                                                                                                                                                                                                                                                                                      |
| Route 22 north gate → Route 23 | (8–9, 5)                                           | Boulder Badge                                                                                                                                                                                                                                                                                                                                         |
| Second cuttable tree           | Viridian City, (11, 24)                            | Cut                                                                                                                                                                                                                                                                                                                                                   |

## Where you go next

North out of Viridian City to **Route 2** and **Viridian Forest**, heading for Pewter City and the
Boulder Badge. Route 2's grass runs **Rattata 45%, Pidgey 45%, Caterpie 5%, Weedle 5%** at levels
2–5. No starters, no Mankey — everything genuinely new on Route 2 sits in the two 5% slots, so if
you want a bug, the Forest is the place to go looking, not the route.

Before you leave, make sure you have:

- [ ] Your starter, and ideally the other two off Route 1
- [ ] A Mankey off Route 22 — you will want it in Pewter
- [ ] The Town Map from Daisy
- [ ] The free Potion from the Route 1 clerk
- [ ] Both batches of Poké Balls from Oak (Pokédex scene, and after the Route 22 rival)
- [ ] A shopping trip to the Viridian Mart

---

### Data notes

**Sources.** Every number above comes from the pinned game tree at `9ee61fbd`:
`data/maps/PalletTown_Frlg/`, `data/maps/PalletTown_ProfessorOaksLab_Frlg/`,
`data/maps/PalletTown_RivalsHouse_Frlg/`, `data/maps/Route1_Frlg/`, `data/maps/ViridianCity_Frlg/`,
`data/maps/ViridianCity_Mart_Frlg/`, `data/maps/ViridianCity_Gym_Frlg/`, `data/maps/Route22_Frlg/`,
`data/maps/Route22_NorthEntrance_Frlg/`, `data/maps/RegionHub/scripts.inc`,
`data/scripts/route23.inc`, `data/scripts/item_ball_scripts_frlg.inc`,
`data/scripts/move_tutors_frlg.inc`, `src/new_game.c`, `src/region_switch.c`, `src/battle_setup.c`,
`src/field_move.c`, `src/starter_choose.c`, `include/constants/region_flags.h`,
`include/config/dexnav.h`, `include/config/qol_field_moves.h`, `include/config/item.h`, plus
`data/generated/encounters.json`, `trainers.json` and `maps.json`.

**Why the FireRed tables and not LeafGreen.** Every Kanto map in `wild_encounters.json` carries two
entries, `*_FireRed` and `*_LeafGreen`. The generator
(`tools/wild_encounters/wild_encounters_to_header.py`) emits FireRed tables under `#ifdef EMERALD`
and LeafGreen tables under `#ifdef LEAFGREEN`; this project builds with `GAME_VERSION ?= EMERALD`
and `ALL_REGIONS ?= 1`, so **only the FireRed tables are compiled in.** Route 1 and Route 2 are
identical either way, but Route 22 and Viridian differ (Psyduck under FireRed, Slowpoke under
LeafGreen) and Pallet's rod tables differ too. Every water and fishing figure on this page is the
FireRed table.

**Coordinates** are block coordinates local to the named map, as authored in that map's `map.json`.
