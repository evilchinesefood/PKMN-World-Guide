---
title: "Pallet Town to Route 22"
region: kanto
order: 1
summary: >-
  Arrive in Kanto, pick a starter, run Oak's errand, beat Blue twice, and catch the one
  Pokémon that wins you your first badge.
maps:
  - MAP_REGION_HUB
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
gate_note: Available from the start of Kanto; nothing gates it.
severity: story
sections:
  - id: world-transit
    map: MAP_REGION_HUB
    title: World Transit
    note: >-
      A new game opens here, on the departure floor, not in a bedroom. Three attendants stand
      in a row and none of them is locked, so you could start in Kanto, Johto or Hoenn on your
      very first turn — Kanto is the one this guide walks you through. The attendant standing
      on his own over to the west is the Battle Frontier gate, and that one really is locked.
      One thing to know before you go: crossing a region gate puts your whole party into the
      PC. On a new save that costs you nothing, because your party is empty, but come back to
      Kanto later with a finished team and that team goes in the box. You also only arrive in
      Pallet Town once — after Kanto's opening, this same attendant drops you in Vermilion City.
    steps:
      - text: You land here. Walk north to the row of attendants.
        at: [16, 4]
      - text: Talk to the Kanto attendant. He gives you the Hub Pass — a key item that warps you straight back here — and sends you to Pallet Town.
        at: [11, 2]
  - id: pallet-town
    map: MAP_PALLET_TOWN
    title: Pallet Town
    note: >-
      Stepping into your bedroom sets your respawn point, so Pallet Town is where you wake up
      if you ever get knocked out. There is no Poké Mart and no Pokémon Center here — the
      nearest of each is a whole route north, in Viridian City. Once you have beaten Blue in
      the lab, Mom heals your whole party for free, any time you ask, forever. That makes the
      grass near home cheap to train in.
    steps:
      - Go downstairs.
      - Talk to Mom. She tells you to go and see Professor Oak.
      - text: Head out of your front door.
        at: [6, 7]
      - text: Read the Trainer Tips sign. Once you have, the woman wandering nearby stops bothering you about it.
        at: [5, 14]
      - text: Look at Blue's house, the other door along the same row over to the east. Nothing inside for you yet, but you will be back.
        at: [15, 7]
      - text: Try to walk north out of town. Oak runs on screen, says the tall grass is dangerous, and walks you to his lab. You cannot skip it.
        at: [12, 1]
  - id: oaks-lab
    map: MAP_PALLET_TOWN_PROFESSOR_OAKS_LAB
    title: Oak's Lab — pick your starter
    note: >-
      This is a physical pick, not a menu. Walk up to the ball you want and talk to it. All
      three come at Level 5.
    steps:
      - text: Bulbasaur is in the left-hand ball. Blue will take Charmander.
        at: [8, 4]
        choice: pick
        choice_group: starter
      - text: Squirtle is in the middle ball. Blue will take Bulbasaur.
        at: [9, 4]
        choice: pick
        choice_group: starter
      - text: Charmander is in the right-hand ball. Blue will take Squirtle.
        at: [10, 4]
        choice: pick
        choice_group: starter
      - Say yes, then give it a nickname if you want one.
      - text: Blue takes the ball that beats yours and challenges you on the spot. Fight him. You cannot lose this one — if your Pokémon faints, the game heals your party and the story carries on. Swing away.
        at: [5, 4]
      - text: Leave. Oak has nothing else for you until you have been to Viridian City.
        at: [6, 12]
  - id: route1
    map: MAP_ROUTE1
    title: Route 1
    note: >-
      Route 1 has 178 tiles of tall grass, more than any other map in this chapter, and all
      three Kanto starters live in it. You have no Poké Balls yet, so remember where the grass
      is on the way north and come back for them after the lab pays out.
    steps:
      - text: Head north. The first tall grass is right at the town's edge, and there is far more further up.
        at: [12, 37]
      - text: Talk to the Poké Mart man standing in the middle of the route. He gives you a free Potion, once. Nothing marks him — no exclamation mark, no item ball — and he is very easy to walk past.
        at: [6, 28]
      - text: The boy further north tells you about the ledges, and he is right. Every ledge on Route 1 faces south. Going up, you have to walk around them. Coming home, you jump straight down. The trip back to Pallet Town is much quicker than the trip up.
        at: [19, 16]
      - text: Read the route sign if you like. There are no item balls and no hidden items anywhere on Route 1.
        at: [9, 31]
  - id: viridian-city
    map: MAP_VIRIDIAN_CITY
    title: Viridian City
    note: >-
      There is no tall grass anywhere in Viridian City, so there is nothing to catch here yet.
      Do not waste steps looking. What you came for is inside the Poké Mart.
    steps:
      - text: Go into the Poké Mart. The clerk stops you before you can shop, mistakes you for Oak's delivery boy and hands you Oak's Parcel. That is your job for this chapter.
        at: [36, 19]
      - text: Heal at the Pokémon Center. It is the first Pokémon Center in Kanto, and its PC is the same box in all three regions — anything you leave here you can pull back out in Johto or Hoenn.
        at: [26, 26]
      - text: Go into the Trainer School if you want a refresher. Blackboards, a notebook and a journal, no items.
        at: [25, 18]
      - text: Look in the house near the top of town for a Spearow called SPEARY and a lecture about nicknames. Just for fun.
        at: [25, 11]
      - text: Walk up to the Gym door and you get bumped back down the ledge. You need six Kanto badges before it opens, and the badge you win here is not one of those six. It stays shut for a long time.
        at: [36, 10]
      - text: Talk to the man on the west side of town. He teaches Dream Eater free to anything that can learn it, and he will do it again and again, as often as you like. Nothing marks him and almost nobody talks to him.
        at: [8, 26]
      - text: Try the road north. The old man is lying across it and there is no way round. Deliver the Parcel first.
        at: [22, 11]
      - text: Now go and get the Potion on the top row of the city. You do not need Cut. Start back at the Route 1 entrance, at the bottom of the city.
        at: [23, 31]
      - text: Step west one tile.
        at: [22, 31]
      - text: Walk north through the gap in the ledge row. Keep going until the path stops.
        at: [22, 17]
      - text: Turn west and follow the footpath to the far side of town.
        at: [8, 17]
      - text: Walk north up the western edge of the city.
        at: [8, 5]
      - text: Turn east and walk along the top corridor until the item ball is beside you.
        at: [16, 5]
      - text: Face east and open the ball. The tree next to it is only a shortcut, not a lock.
        at: [17, 5]
  - id: parcel-payout
    map: MAP_PALLET_TOWN
    title: Back to Pallet Town — the payout
    note: >-
      This is the biggest single moment in the chapter. Handing over the Parcel opens the road
      north out of Viridian, makes Blue wait for you on Route 22, and puts the Mart clerk back
      behind his counter.
    steps:
      - Jump the ledges back down Route 1 to Pallet Town.
      - text: Give Oak the Parcel. He hands you the Pokédex, the DexNav and five Poké Balls.
        at: [16, 13]
      - text: Go next door before you leave town. Blue's sister Daisy gives you the Town Map for free — but only now. Before the Parcel she has nothing for you. After you take it, she has nothing either. And the game never tells you to go and see her.
        at: [15, 7]
      - Take your five Poké Balls back into Route 1's grass and catch the two starters you walked past.
  - id: viridian-again
    map: MAP_VIRIDIAN_CITY
    title: Viridian City, second visit
    steps:
      - text: The old man is up now, standing a few tiles further north. Walk past him and he grabs you for a catching lesson. He catches a Weedle, not you, and it does not count for anything — but it costs nothing and you cannot really avoid it, so take it.
        at: [20, 8]
      - text: Heal before you go anywhere else. The next rival battle can genuinely knock you out.
        at: [26, 26]
      - The road north to Route 2 is properly clear now. Before you take it, leave Viridian by the west exit and walk out onto Route 22.
  - id: route22
    map: MAP_ROUTE22
    title: Route 22 — the trip west that wins you Pewter
    note: >-
      Nothing points you west. There is no story reason to come here. That is why most players
      fight Pewter Gym the hard way — the Pokémon that beats it is two screens from Viridian,
      and they walk right past it. You come in at the eastern end and everything below is west of
      you. There are two patches of grass and Mankey is in both. Blue also comes back to this same
      spot much later, after you beat Viridian Gym, with six Pokémon between Level 45 and Level 53.
      Note that and leave it alone for now.
    steps:
      - text: The first patch of grass is right where you come in. Walk into it and catch a Mankey — it appears on no other map in this chapter.
        at: [36, 11]
      - Train it. Mankey learns Low Kick at Level 8 and Seismic Toss at Level 12, and Fighting moves do double damage to Rock — which is the whole of Pewter Gym.
      - text: Carry on west and Blue jogs in for a second battle. This one is real. Lose it and you white out, so heal in Viridian before you come here.
        at: [33, 5]
      - text: Keep going west to the gate in the far corner. It leads to Route 23 and the Pokémon League, and the policeman inside turns you away without the Boulder Badge.
        at: [8, 5]
      - Go back to Pallet Town and talk to Oak again. With that battle won he hands over a second batch of five Poké Balls, once. It is buried behind a grumble about your empty Pokédex and nothing suggests the trip.
  - id: onward
    map: MAP_VIRIDIAN_CITY
    title: Where you go next
    steps:
      - text: Head north out of Viridian City to Route 2 and Viridian Forest. Pewter City and your first badge are that way.
        at: [21, 11]
---

# Pallet Town to Route 22

Your first hour in Kanto: get a starter, run an errand for Professor Oak, beat your rival
twice, and catch the one Pokémon that will win you your first badge.

You do not start in a bedroom. A new game opens on the departure floor of the World Transit
hub, and you choose your region by walking up to an attendant and talking to them. Nobody
checks anything — Kanto, Johto and Hoenn are all open on your very first turn. Kanto is the
one this guide covers.

## Picking your starter

Blue always takes the starter that beats yours. That decides every rival battle in Kanto.

| You pick   | You get          | Blue takes     |
| ---------- | ---------------- | -------------- |
| Bulbasaur  | Bulbasaur, Lv 5  | **Charmander** |
| Squirtle   | Squirtle, Lv 5   | **Bulbasaur**  |
| Charmander | Charmander, Lv 5 | **Squirtle**   |

## The two rival battles

**In the lab you cannot lose.** Blue has one Pokémon at Level 5 — Charmander with Scratch and
Growl, Bulbasaur with Tackle and Growl, or Squirtle with Tackle and Tail Whip. If your Pokémon
faints, the game heals your party and the story carries on.

**On Route 22 you can.** Lose that one and you white out. He brings two Pokémon at Level 9,
and his lead is a Pidgey with Tackle and Sand-Attack every time.

| Your starter   | Blue's second slot                 |
| -------------- | ---------------------------------- |
| **Bulbasaur**  | Charmander, Lv 9 — Scratch, Growl  |
| **Squirtle**   | Bulbasaur, Lv 9 — Tackle, Growl    |
| **Charmander** | Squirtle, Lv 9 — Tackle, Tail Whip |

Blue's starter never learned its own type move. Look at the lists: every attack he has is an
ordinary Normal move. Yours is not — and that is the whole fight.

Sand-Attack is the only move in his party that can actually beat you. Each one makes your
attacks more likely to miss, and they add up. Knock the Pidgey out first. If it lands two
Sand-Attacks early, switch your Pokémon out.

If you picked Bulbasaur, this is the easiest of the three — Vine Whip is a real attack and
Blue's Charmander only has Scratch. If you picked Charmander, Ember out-damages his Squirtle's
Tackle and you win the straight race. Grass Pokémon shrug off Water Gun, so if you picked
Squirtle this is the slowest of the three fights. Bring a second Pokémon — a Mankey is ideal.

## What lives in the grass

**Route 1.** All three Kanto starters are wild here. Together they make up 30% of everything
you meet. This is not the original game. You can own the whole trio before you have seen
Viridian City.

| Species        | Chance | Levels |
| -------------- | -----: | ------ |
| Rattata        |    40% | 2–4    |
| Pidgey         |    30% | 3–5    |
| **Bulbasaur**  |    10% | 3      |
| **Charmander** |    10% | 3      |
| **Squirtle**   |    10% | 2      |

**Route 22.** The Mankey stop.

| Species    | Chance | Levels |
| ---------- | -----: | ------ |
| Rattata    |    45% | 2–5    |
| **Mankey** |    45% | 2–5    |
| Spearow    |    10% | 3, 5   |

## What you cannot reach yet

| Thing                                                                       | Needs                                                                                                                     |
| --------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------- |
| The tree next to the Viridian Potion                                        | Cut — from the Cascade Badge, or straight away if you find the Cut Tool. The Potion itself is reachable on foot right now |
| The second cuttable tree in Viridian                                        | Cut, the same way                                                                                                         |
| Route 22's pond (Psyduck, Lv 20–40)                                         | Surf — from the Soul Badge, or straight away with the Surf Tool                                                           |
| Fishing in Pallet, Viridian and Route 22                                    | A rod                                                                                                                     |
| Route 1's hidden Pokémon (Bulbasaur 60%, Squirtle 35%, Caterpie 5%, Lv 6–8) | DexNav detector mode, which unlocks after your first Hall of Fame                                                         |
| Viridian Gym                                                                | Six Kanto badges                                                                                                          |
| The gate north out of Route 22                                              | The Boulder Badge                                                                                                         |

## Where you go next

North out of Viridian City to **Route 2** and **Viridian Forest**, heading for Pewter City and
the Boulder Badge. Route 2's grass is Rattata 45%, Pidgey 45%, Caterpie 5% and Weedle 5% at
Levels 2–5 (the two bugs come at 4–5) — no starters and no Mankey, so if you want a bug, go
into the Forest rather than hunting the route.

## Before you leave, check you have

- [ ] Your starter, and ideally the other two off Route 1
- [ ] A Mankey off Route 22 — you will want it in Pewter
- [ ] The Town Map from Daisy
- [ ] The free Potion from the Route 1 Poké Mart man
- [ ] The Potion from the item ball on Viridian's top row
- [ ] Both batches of five Poké Balls from Oak
- [ ] A shopping trip to the Viridian Mart, which sells Poké Balls, Potions, Antidotes and Paralyze Heals
