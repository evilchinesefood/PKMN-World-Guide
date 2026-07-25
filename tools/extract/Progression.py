"""progression.json -- the gate keys every other file's `gate` field points at.

Partly hand-authored by design (brief section 5). The split, from DATA-AUDIT.md 5B.7:
  derived   badges (24 setflag sites), champion flags, league entry gates
  authored  the C rule tables (obedience, level caps) and the callnative semantics,
            because they appear in no script and an extractor cannot recover them

Everything authored carries hand_authored: true and cites its source file so it can be
re-checked when the pin moves.
"""

import os, re, sys, json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import Common as C

REGIONS = ("kanto", "johto", "hoenn")

# Derived: every gym's badge flag and the map that sets it. Located by scanning
# data/maps/*/scripts.inc for setflag of a badge constant.
BADGE_PAT = re.compile(r"setflag\s+(FLAG_BADGE0?(\d)_GET|FLAG_(KANTO|JOHTO)_BADGE_?(\d))")


def find_badge_sites():
    out = {}
    base = C.g("data", "maps")
    for d in sorted(os.listdir(base)):
        p = os.path.join(base, d, "scripts.inc")
        if not os.path.isfile(p):
            continue
        with open(p, encoding="utf-8", errors="replace") as f:
            for i, line in enumerate(f, 1):
                m = BADGE_PAT.search(line)
                if not m:
                    continue
                flag = m.group(1)
                if m.group(3):
                    region, n = m.group(3).lower(), int(m.group(4))
                else:
                    region, n = "hoenn", int(m.group(2))
                out.setdefault((region, n), []).append((flag, d, i))
    return out


def champion_flags():
    txt = C.read("include", "constants", "region_flags.h")
    out = {}
    for r in REGIONS:
        m = re.search(rf"#define\s+FLAG_{r.upper()}_CHAMPION\s+(.+)", txt)
        if m:
            out[r] = m.group(1).split("//")[0].strip()
    return out


# Authored: read from C, verified at this pin. Sources cited so a re-pin can re-check.
OBEDIENCE = {
    "by_badge_index": [10, 20, 30, 40, 50, 60, 70, 80, None],
    "note": "badge INDICES tested by sequential overwriting ifs, not a count; the 8th badge "
    "returns OBEYS outright. Applies to outsider Pokemon only. With "
    "B_OBEDIENCE_MECHANICS >= GEN_8 the comparison uses MET level, not current level.",
    "hand_authored": True,
    "source": C.source("src/battle_util.c", key="GetAttackerObedienceForAction", line=5569),
}

LEVEL_CAPS = {
    "per_badge": [15, 19, 24, 29, 31, 33, 42, 46],
    "eight_badges": 58,
    "champion": 100,
    "hard_mode_only": True,
    "exp_at_cap": 0,
    "note": "caps bind ONLY when SaveBlock2.optionsHardMode is set, which is chosen once at "
    "new game and locked for the save. The last tier keys on the GLOBAL FLAG_IS_CHAMPION, "
    "not a per-region flag. EV caps are dead code (B_EV_CAP_TYPE = EV_CAP_NONE) -- do not "
    "document them.",
    "hand_authored": True,
    "source": C.source("src/caps.c", key="GetCurrentLevelCap", line=10),
}

GLOBAL_GATES = [
    ("global:champion-any", 1, ["Battle Frontier", "Eon Ticket", "DexNav detector mode"]),
    ("global:champion-two", 2, ["PC 2F World Transit pad", "Old Sea Map"]),
    ("global:champion-all", 3, ["Mystic Ticket", "World Championship registrar"]),
]


def main():
    sites = find_badge_sites()
    champs = champion_flags()
    gates = []

    for ri, region in enumerate(REGIONS):
        for n in range(1, 9):
            hits = sites.get((region, n), [])
            flag, folder, line = hits[0] if hits else (None, None, None)
            gates.append(
                {
                    "key": f"{region}:badge-{n}",
                    "region": region,
                    "order": ri * 100 + n,
                    "severity": "routine",
                    "label": f"{region.title()} badge {n}",
                    "flag": flag,
                    "earned_at": {"map_dir": folder} if folder else None,
                    "hand_authored": False,
                    "gaps": [] if hits else [C.gap("flag", "no setflag site found in data/maps")],
                    "source": C.source(f"data/maps/{folder}/scripts.inc", line=line) if folder else None,
                }
            )
        gates.append(
            {
                "key": f"{region}:champion",
                "region": region,
                "order": ri * 100 + 50,
                "severity": "endgame",
                "label": f"{region.title()} Champion",
                "flag": f"FLAG_{region.upper()}_CHAMPION",
                "flag_value": champs.get(region),
                "hand_authored": False,
                "source": C.source("include/constants/region_flags.h"),
            }
        )

    for key, n, unlocks in GLOBAL_GATES:
        gates.append(
            {
                "key": key,
                "region": None,
                "order": 900 + n,
                "severity": "endgame",
                "label": f"Champion of {'any region' if n == 1 else f'{n} regions'}",
                "rule": f"IsNRegionChampion({n})",
                "unlocks": unlocks,
                "hand_authored": True,
                "source": C.source("src/region_switch.c", key="IsNRegionChampion"),
            }
        )

    payload = {
        **C.header(),
        "gates": sorted(gates, key=lambda g: (g["order"], g["key"])),
        "obedience": OBEDIENCE,
        "level_caps": LEVEL_CAPS,
        # There is none: the three hub attendants have no flag check at all. The friction is
        # RETURNING, not leaving. See DATA-AUDIT.md 5B.4.
        "region_order": None,
        "region_order_note": "The player may start in any region and switch at any time. But "
        "obedience and level caps reset per region, so a second region begins at a Lv15 cap in "
        "Hard Mode regardless of prior progress -- that is the real cost of switching.",
    }
    p = C.write("progression.json", payload)

    derived = sum(1 for g in gates if not g["hand_authored"])
    missing = sum(1 for g in gates if g.get("gaps"))
    print(f"{len(gates)} gates -> {p}")
    print(f"  derived {derived}, hand-authored {len(gates)-derived}, with gaps {missing}")
    for r in REGIONS:
        got = sum(1 for g in gates if g["region"] == r and g.get("flag"))
        print(f"  {r}: {got}/9 gates resolved to a flag")
    return 0 if missing == 0 else 0


if __name__ == "__main__":
    sys.exit(main())
