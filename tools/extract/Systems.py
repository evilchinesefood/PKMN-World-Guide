"""systems.json -- one explainer entry per non-vanilla system (brief section 5).

Presence is DETECTED, never assumed: each system declares the files and identifiers that
prove it exists, and the extractor reports present/absent per the pinned commit. That
matters because at v1.3.6 half of these did not exist at all, which is why the pin moved
(DECISIONS.md 8). If the pin moves again this file tells the truth rather than the plan.

Prose is editorial and belongs in content/; what lives here is the factual spine --
where the system's code and data are, and the numbers a guide must state correctly.
"""

import os, re, sys, json, subprocess

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import Common as C

# key, title, probe identifiers (any hit = present), and the facts a guide must get right.
SYSTEMS = [
    dict(
        key="world-transit",
        title="World Transit",
        probes=["src/region_switch.c", "data/maps/RegionHub"],
        facts=[
            "Switching regions boxes your whole party to the global PC; held mail moves to the PC mailbox.",
            "If the PC fills, the transfer stops partway.",
            "The hub is deliberately never a whiteout target.",
        ],
    ),
    dict(
        key="shared-pc-dex",
        title="Shared PC and Pokédex",
        probes=["include/global.h"],
        idents=["regionVars"],
        facts=[
            "One global National Dex across all three regions -- there are no per-species regional dex numbers.",
            "There is no Johto dex: JOHTO_DEX_COUNT exists but has no order table, and Johto routes to the Hoenn dex.",
        ],
    ),
    dict(
        key="obedience",
        title="Obedience by current-region badges",
        probes=["src/battle_util.c"],
        idents=["HasCurrentRegionBadge"],
        facts=[
            "Obedience follows the CURRENT region's badges, so it resets when you switch region.",
            "Outsider Pokémon only. Levels 10/20/30/40/50/60/70/80, then full obedience at the 8th badge.",
        ],
    ),
    dict(
        key="level-caps",
        title="Hard Mode level caps",
        probes=["src/caps.c"],
        idents=["sLevelCapPerBadge"],
        facts=[
            "Caps bind ONLY in Hard Mode, chosen once at new game and locked for the save.",
            "15/19/24/29/31/33/42/46 by badge, 58 at eight badges, uncapped once Champion.",
            "At or over the cap a Pokémon gains zero EXP.",
            "EV caps are dead code and must not be documented.",
        ],
    ),
    dict(
        key="riding",
        title="Riding your own Pokémon",
        probes=["src/event_object_movement.c"],
        idents=["MOVEMENT_TYPE_PLAYER_SURF", "SurfBlob", "sSurfBlob"],
        facts=[
            "Your active follower rides first if it can use the move; otherwise the first capable party member by slot order.",
            "Falls back to the generic blob for surf and to Flygon for flight.",
        ],
    ),
    dict(
        key="field-moves",
        title="Field-move badge gates",
        probes=["src/field_move.c"],
        facts=[
            "Kanto maps field moves to DIFFERENT badge indices than Hoenn and Johto.",
            "Johto's Surf gate is deliberately the 4th badge, not the 5th -- Cianwood is surf-only.",
            "Owning the matching field-move tool item bypasses the badge gate for Cut, Rock Smash, Strength, Surf, Dive and Waterfall. Flash and Fly have no bypass.",
        ],
    ),
    dict(
        key="battle-net",
        title="Battle Net",
        probes=["src/battle_net.c", "data/maps/RegionHub_2F"],
        idents=["BattleNet"],
        facts=[
            "Opens once you are any region's Champion.",
            "The Director grants the Mega Ring and one starter-line Mega Stone.",
        ],
    ),
    dict(
        key="shard-economy",
        title="Shard economy and Mega Stone vendors",
        probes=["src/battle_net.c"],
        idents=["SHARD_PRICE_COMMON", "BP_PER_SHARD"],
        facts=[
            "HARD gym-leader rematch wins pay Shards; the first win against a stone-holding leader also drops their signature Mega Stone, once.",
        ],
    ),
    dict(
        key="sim-modes",
        title="Battle Net sim modes",
        probes=["src/battle_net.c"],
        idents=["LeaderSim", "TowerStreak"],
        facts=["Sim battles run under Battle Tower rules: no money at stake, no whiteout, party restored around every match."],
    ),
    dict(
        key="world-championship",
        title="World Championship",
        probes=["src/battle_dome.c"],
        idents=["sChampionshipTrainerIds", "VAR_WORLD_CHAMPIONSHIP_MODE"],
        facts=[
            "Gated on being Champion of all three regions.",
            "A 15-trainer bracket. Red is force-seeded into the final, so you always meet him last.",
            "Opponents draw from candidate POOLS, not fixed parties.",
        ],
    ),
    dict(
        key="dexnav",
        title="DexNav",
        probes=["src/dexnav.c", "include/config/dexnav.h"],
        facts=[
            "Granted with each region's Pokédex; detector mode unlocks at your first Hall of Fame.",
            "Search levels are disabled in this build and must not be documented.",
        ],
    ),
    dict(
        key="quests",
        title="Quest system",
        probes=["src/quests.c"],
        idents=["sSideQuests"],
        facts=["Engine present and wired into the Start menu, but the quest table is upstream placeholder data and no script opens it."],
    ),
]


def present(s):
    hits = []
    for p in s.get("probes", []):
        if os.path.exists(C.g(*p.split("/"))):
            hits.append(p)
    if hits or not s.get("idents"):
        return bool(hits), hits
    # fall back to an identifier sweep when the file name alone is not decisive
    for ident in s["idents"]:
        r = subprocess.run(
            ["grep", "-rlm1", ident, C.g("src"), C.g("include"), C.g("data")],
            capture_output=True, text=True,
        )
        if r.stdout.strip():
            hits.append(r.stdout.strip().splitlines()[0].replace(C.GAME + "/", ""))
            break
    return bool(hits), hits


def main():
    out = []
    for s in SYSTEMS:
        ok, hits = present(s)
        out.append(
            {
                "key": s["key"],
                "title": s["title"],
                "present": ok,
                "facts": s["facts"] if ok else [],
                "evidence": hits,
                "gate": None,
                "severity": "story",
                "gaps": [] if ok else [C.gap("present", "no code or data found at this pin")],
            }
        )
    cfg = sorted(os.listdir(C.g("include", "config")))
    toggles = 0
    for f in cfg:
        toggles += len(re.findall(r"^#define\s+\w+", C.read("include", "config", f), re.M))
    p = C.write("systems.json", {**C.header(), "systems": out, "config": {"files": cfg, "defines": toggles}})
    n = sum(1 for s in out if s["present"])
    print(f"{n}/{len(out)} systems present at this pin -> {p}")
    for s in out:
        if not s["present"]:
            print(f"  ABSENT: {s['key']}")
    print(f"include/config: {len(cfg)} files, {toggles} #defines")
    return 0


if __name__ == "__main__":
    sys.exit(main())
