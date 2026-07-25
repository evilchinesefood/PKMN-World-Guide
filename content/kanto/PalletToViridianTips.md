---
title: "Insider Tips: Pallet Town to Route 22"
region: kanto
maps:
  - MAP_PALLET_TOWN
  - MAP_PALLET_TOWN_PLAYERS_HOUSE_1F
  - MAP_PALLET_TOWN_RIVALS_HOUSE
  - MAP_PALLET_TOWN_PROFESSOR_OAKS_LAB
  - MAP_ROUTE1
  - MAP_VIRIDIAN_CITY
  - MAP_ROUTE22
gate: kanto:badge-1
gate_note: >-
  Pre-badge content. Ordered before kanto:badge-1, not gated by it; progression.json
  at 9ee61fbd has no pre-badge-1 gate key.
severity: story
companion_to: content/kanto/PalletToViridian.md
---

# Insider Tips

## You can catch all three starters on Route 1

Route 1's grass runs **Bulbasaur at 10% (Lv 3), Charmander at 10% (Lv 3) and Squirtle at 10%
(Lv 2)** — 30% of every encounter on the route is a starter, in the very first patch of grass in the
game. Come back the moment Oak hands you your five Poké Balls and you can be carrying the whole trio
before you have fought a single trainer outside the lab.

_`data/generated/encounters.json`, `sRoute1_FireRed` land table._

## There is a free Potion on Route 1 and nothing marks it

The Poké Mart employee standing at **(6, 28)** gives you a Potion, once, for talking to him. He is an
ordinary wandering NPC with no exclamation mark, no item ball and no prompt, and he is easy to walk
straight past on the way north.

_`data/maps/Route1_Frlg/scripts.inc`, `FLAG_GOT_POTION_ON_ROUTE_1`._

## Blue's sister hands you the Town Map — but only in one window

Daisy, in the Rival's House at (15, 7) in Pallet Town, gives you the **Town Map** for free. She will
not do it before you have delivered Oak's Parcel, and nothing in the Pokédex scene tells you to go
next door afterwards. Her giveaway is keyed to a variable that Oak flips silently.

_`data/maps/PalletTown_RivalsHouse_Frlg/scripts.inc`, `VAR_MAP_SCENE_PALLET_TOWN_RIVALS_HOUSE` = 1._

## Go back to Oak after the Route 22 rival for five more Poké Balls

Beating Blue on Route 22 sets `VAR_MAP_SCENE_ROUTE22` to 2. Talk to Oak with that variable at 2 or
higher and he hands over a **second batch of five Poké Balls**. It is buried behind a
"you've added nothing to the Pokédex yet" line, it fires once, and nothing suggests the trip.

_`data/maps/PalletTown_ProfessorOaksLab_Frlg/scripts.inc`,
`FLAG_GOT_POKEBALLS_FROM_OAK_AFTER_22_RIVAL`._

## Blue's starter is stuck on its Level 1 moves

At Level 9 on Route 22, Blue's Charmander has Scratch and Growl — no Ember, which it learns at
Level 4. His Bulbasaur has Tackle and Growl, no Vine Whip (Level 3). His Squirtle has Tackle and
Tail Whip, no Water Gun (Level 3). These are explicit authored move lists, not defaults. **He picked
the starter that beats yours and cannot use the advantage.** Your starter has its type move; his
does not.

_`src/data/trainers_frlg.party` via `data/generated/trainers.json`;
level-up learnsets in `data/generated/species.json`._

## The lab battle is a free loss. The Route 22 battle is not.

The Oak's Lab rival is called with `RIVAL_BATTLE_TUTORIAL`, which carries the heal-after bit — lose
and the game heals your party and carries on. The **Route 22** rival is called with flags of **0**,
and a defeated player goes straight to `CB2_WhiteOut`. Same NPC, same music, completely different
stakes. Heal in Viridian before you walk west.

_`src/battle_setup.c`, `TRAINER_BATTLE_EARLY_RIVAL` handling; `RIVAL_BATTLE_HEAL_AFTER`._

## Mom is your Pokémon Center until Viridian

Pallet Town has no Pokémon Center and no Mart. Once you have beaten Blue inside the lab, Mom heals
your entire party on request, free, unlimited — which makes the Pallet Town / Route 1 grass a much
cheaper place to train than it looks.

_`data/maps/PalletTown_PlayersHouse_1F_Frlg/scripts.inc`, gated on `FLAG_BEAT_RIVAL_IN_OAKS_LAB`._

## Route 1's ledges are a one-way slide home

All **61** jump tiles on Route 1 face south, in bands across rows 5, 10, 15, 20, 26 and 31.
Northbound they are walls. Southbound they are a shortcut, and the return trip to Pallet Town with
Oak's Parcel takes a fraction of the time the trip up did.

_Metatile behaviours in `data/layouts/Route1_Frlg/map.bin` — 61 × `MB_JUMP_SOUTH`, zero facing any
other direction._

## Detour west before Pewter: Route 22 has Mankey

**Mankey is 45% of Route 22's grass** and appears on no other map in this segment. It learns Low Kick
at Level 8 and Seismic Toss at Level 12, and Fighting is double damage against Rock. Route 22 is a
dead end you have no story reason to visit — which is exactly why most players reach Pewter Gym
without the best counter in the region sitting two screens from Viridian.

_`data/generated/encounters.json`, `sRoute22_FireRed`; learnset from `data/generated/species.json`;
`src/data/types_info.h`._

## The Viridian Potion does not need Cut

The item ball at **(17, 5)** has a cuttable tree parked right next to it at (18, 5), which reads as
"come back later" and is why almost nobody has it before Cerulean. The tree is only a shortcut. Row
5 continues west to x = 8 and drops down the column at x = 8 to the western footpath, which is open
on your first visit. Go **(23, 31) → (22, 31) → (22, 17) → (8, 17) → (8, 5) → (16, 5)** and face
east.

_Blockdata and metatile collision in `data/layouts/ViridianCity_Frlg/map.bin`; object placements in
`data/maps/ViridianCity_Frlg/map.json`; item from
`data/scripts/item_ball_scripts_frlg.inc`, `ViridianCity_EventScript_ItemPotion` → `ITEM_POTION`._

## There is an unmarked, unlimited move tutor in Viridian City

The man at **(8, 26)** teaches **Dream Eater**, free, to any eligible Pokémon. He has no flag, no
gate and no queue — he is standing there from your very first visit. And because this build sets
`I_REUSABLE_TMS` to `TRUE`, the tutor's one-time lock is compiled out of the script entirely: **you
can come back and teach it again, as often as you like.**

_`data/scripts/move_tutors_frlg.inc`, `EventScript_DreamEaterTutor`; `include/config/item.h:28`._

## You get the DexNav early — but not the half that matters yet

The Pokédex hand-off sets `FLAG_SYS_DEXNAV_GET` in the same script, so DexNav is in your Start menu
from Pallet Town onwards. **Detector mode is separate.** It unlocks on your first Hall of Fame in
any region, and until then the hidden-encounter tables are closed to you — which on Route 1 means a
60% Bulbasaur / 35% Squirtle / 5% Caterpie spread at Lv 6–8 that you will not touch for the entire
campaign.

_`data/maps/PalletTown_ProfessorOaksLab_Frlg/scripts.inc`; `include/config/dexnav.h`,
`DN_FLAG_DETECTOR_MODE`; set in `src/post_battle_event_funcs.c`._

## Crossing a region gate empties your party into the PC

`RegionHub_ScrEnterRegion` calls `DepositPartyToPC()` whenever the region you are entering differs
from the one you were in. On a new save that costs nothing. If you arrive in Kanto later with a
finished team from Hoenn or Johto, **that team goes to the box and you start Pallet Town with an
empty party** — which is why Oak's starter flow still works on a returning champion.

_`src/region_switch.c`; confirmed by the defensive comment at
`data/maps/PalletTown_ProfessorOaksLab_Frlg/scripts.inc:1122`._

## Viridian Gym's lock skips two badges

The unlock check reads `FLAG_KANTO_BADGE_2` through `FLAG_KANTO_BADGE_7` — Cascade, Thunder,
Rainbow, Soul, Marsh, Volcano. **Six flags.** It does not check the Boulder Badge, and it does not
check the Earth Badge, which is the badge this Gym awards. Worth knowing precisely, because "come
back with seven badges" is the wrong rule here.

_`data/maps/ViridianCity_Frlg/scripts.inc`, `ViridianCity_EventScript_TryUnlockGym`; badge names from
`data/scripts/route23.inc`._
