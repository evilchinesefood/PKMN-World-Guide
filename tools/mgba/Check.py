"""Validates tools/mgba/shots.json against its schema. This is the verifiable half of the
capture tool: tools/mgba/Capture.lua runs inside mGBA's GUI console against a ROM this repo
will never contain, so nothing about an actual capture can be exercised by a checker that
runs in CI or on a bare checkout. What CAN be checked without a ROM, an emulator, or a
savestate is the one file a maintainer hand-writes: shots.json itself. Every rule below is a
way that file can be wrong WITHOUT Capture.lua noticing loudly on its own --

  - a duplicate id silently makes the second shot's screenshot overwrite the first's PNG at
    the same public/screenshots/<id>.png path, and manifest.json ends up with two rows
    describing that one file as if they were different shots -- with no error from anything;
  - an id that is not kebab-case still makes an id.png, but Capture.lua does not re-validate
    the shape (see its docstring for why: that would be a second, driftable copy of this file's
    rules), so a stray space or capital reaches the filesystem;
  - a missing or blank savestate, or a non-integer/non-positive frame count, IS caught by
    Capture.lua's own guards at the point of use -- but only if a maintainer runs it and
    happens to trigger the row in question, one mGBA session at a time. Catching it here means
    every row is checked on every save, before anyone opens the emulator.
  - two DIFFERENT ids can still collide as the SAME output file. `public/screenshots/` is a
    plain directory on whatever filesystem the maintainer's machine uses, and macOS's default
    (APFS, case-insensitive) treats "Pallet-Town.png" and "pallet-town.png" as one file. The
    id-uniqueness rule above compares ids as exact strings and would wave both through; this
    rule compares the derived output paths case-folded, which is the only way to catch a shot
    whose id merely FAILS the kebab-case rule (so it is already reported once for that) but
    ALSO silently overwrites a different, validly-named shot's PNG.

FOLLOWS tools/qa/Chapters.mjs'S FIXTURE DISCIPLINE, PORTED TO PYTHON. That file's own header
explains why the table at its bottom is not optional: a checker's failure mode is silence, and
silence is indistinguishable from success. The FIXTURES list below constructs one shots.json
per rule that breaks it (plus one healthy list that breaks none), runs every one of them
through check_shots() in this same process on every invocation, and compares the exact set of
diagnostics produced against what each fixture is supposed to produce -- COUNT included, so a
rule that fires twice, or a second rule that fires by accident, fails here and not on a real
shots.json edit six months from now.
"""

import json, os, re, sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "extract"))
import Common as C

OUTDIR = os.path.join(C.ROOT, "public", "screenshots")
SHOTS = os.path.join(C.ROOT, "tools", "mgba", "shots.json")

# Same shape as tools/qa/Chapters.mjs's ID: an id becomes a DOM-free but filesystem-real thing
# -- the literal stem of public/screenshots/<id>.png -- so the same lowercase-kebab reasoning
# applies even though nothing here touches a DOM.
ID_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


def check_shots(data):
    """(where, message) for every way `data` breaks the schema. One function, so the fixture
    table below and the real shots.json are checked by the same code -- same reasoning as
    Chapters.mjs's checkChapter."""
    errors = []

    if not isinstance(data, list):
        errors.append(("shots.json", "top level must be a JSON array of shot objects, got %s" % type(data).__name__))
        return errors

    seen_ids = {}
    seen_outputs = {}  # lowercased output path -> (index, id, path); catches case-insensitive
                        # collisions between ids that differ as STRINGS (see module docstring)

    for i, entry in enumerate(data):
        where = "entry %d" % (i + 1)
        if not isinstance(entry, dict):
            errors.append((where, "must be a JSON object, got %s" % type(entry).__name__))
            continue

        sid = entry.get("id")
        if isinstance(sid, str) and sid:
            where = "entry %d (%s)" % (i + 1, sid)

        if not isinstance(sid, str) or not sid:
            errors.append((where, "`id` is missing or not a non-empty string"))
        elif not ID_RE.match(sid):
            errors.append((where, "id %r is not lowercase kebab-case (a-z, 0-9, single hyphens) -- "
                                   "it becomes public/screenshots/%s.png literally" % (sid, sid)))
        elif sid in seen_ids:
            errors.append((where, "id %r is already used by entry %d" % (sid, seen_ids[sid] + 1)))
        else:
            seen_ids[sid] = i

        savestate = entry.get("savestate")
        if not isinstance(savestate, str) or not savestate.strip():
            errors.append((where, "`savestate` is missing or not a non-empty string"))

        frames = entry.get("frames")
        if isinstance(frames, bool) or not isinstance(frames, int) or frames <= 0:
            errors.append((where, "`frames` must be a positive JSON integer (no decimal point), got %r" % (frames,)))

        # Computed from whatever `id` actually is, even a malformed one -- a shape violation
        # and a case-collision are two separate, independently true facts about the same bad
        # row, and the second is invisible if this is gated on the first also having passed.
        # An EXACT repeat of an earlier id is skipped here on purpose: that is the same row
        # the id-uniqueness rule above already reported, and re-reporting it as a "case"
        # collision would be a second message for one mistake -- and a wrong one, since the
        # id strings in that case do not differ at all.
        if isinstance(sid, str) and sid:
            out = os.path.join(OUTDIR, sid + ".png")
            key = out.lower()
            prev = seen_outputs.get(key)
            if prev is None:
                seen_outputs[key] = (i, sid, out)
            elif prev[1] != sid:
                other_i, other_id, other_out = prev
                errors.append((where, "output %s collides with entry %d's %s (id %r) on a "
                                       "case-insensitive filesystem (macOS's default), even "
                                       "though the `id` strings differ" % (out, other_i + 1, other_out, other_id)))

    return errors


# ---------------------------------------------------------------------------------------
# The fixture table. Every rule above, broken on purpose, asserted in this same run.
# ---------------------------------------------------------------------------------------

FIXTURES = [
    (
        "healthy: three distinct, well-formed shots",
        [
            {"id": "pallet-town-start", "savestate": "a.ss0", "frames": 60},
            {"id": "route-1-battle", "savestate": "b.ss0", "frames": 90},
            {"id": "cerulean-gym", "savestate": "c.ss0", "frames": 120},
        ],
        [],
    ),
    (
        "top level is not a list",
        {"shots": []},
        ["top level must be a JSON array"],
    ),
    (
        "entry is not an object",
        ["pallet-town-start"],
        ["must be a JSON object"],
    ),
    (
        "missing id",
        [{"savestate": "a.ss0", "frames": 60}],
        ["`id` is missing"],
    ),
    (
        "empty id",
        [{"id": "", "savestate": "a.ss0", "frames": 60}],
        ["`id` is missing"],
    ),
    (
        "id is not kebab-case: uppercase",
        [{"id": "Pallet-Town", "savestate": "a.ss0", "frames": 60}],
        ["not lowercase kebab-case"],
    ),
    (
        "id is not kebab-case: space",
        [{"id": "pallet town", "savestate": "a.ss0", "frames": 60}],
        ["not lowercase kebab-case"],
    ),
    (
        "duplicate id",
        [
            {"id": "pallet-town", "savestate": "a.ss0", "frames": 60},
            {"id": "pallet-town", "savestate": "b.ss0", "frames": 60},
        ],
        ["is already used by entry 1"],
    ),
    (
        "missing savestate",
        [{"id": "pallet-town", "frames": 60}],
        ["`savestate` is missing"],
    ),
    (
        "blank savestate",
        [{"id": "pallet-town", "savestate": "   ", "frames": 60}],
        ["`savestate` is missing"],
    ),
    (
        "missing frames",
        [{"id": "pallet-town", "savestate": "a.ss0"}],
        ["`frames` must be a positive"],
    ),
    (
        "frames is a float",
        [{"id": "pallet-town", "savestate": "a.ss0", "frames": 60.5}],
        ["`frames` must be a positive"],
    ),
    (
        "frames is zero",
        [{"id": "pallet-town", "savestate": "a.ss0", "frames": 0}],
        ["`frames` must be a positive"],
    ),
    (
        "frames is negative",
        [{"id": "pallet-town", "savestate": "a.ss0", "frames": -5}],
        ["`frames` must be a positive"],
    ),
    (
        "frames is a bool (JSON true is a Python int subclass -- must not slip through)",
        [{"id": "pallet-town", "savestate": "a.ss0", "frames": True}],
        ["`frames` must be a positive"],
    ),
    (
        "two different ids collide as the same output file on a case-insensitive filesystem",
        [
            {"id": "pallet-town", "savestate": "a.ss0", "frames": 60},
            {"id": "Pallet-Town", "savestate": "b.ss0", "frames": 60},
        ],
        ["not lowercase kebab-case", "collides with entry 1"],
    ),
]


def run_fixtures():
    failed = 0
    for name, shots, expect in FIXTURES:
        got = [msg for _, msg in check_shots(shots)]
        pool = list(got)
        missing = []
        for want in expect:
            hit = next((idx for idx, msg in enumerate(pool) if want in msg), None)
            if hit is None:
                missing.append(want)
            else:
                pool.pop(hit)
        if missing or pool:
            failed += 1
            print("FIXTURE FAIL  %s" % name)
            if missing:
                print("      never fired: %s" % ", ".join(repr(m) for m in missing))
            if pool:
                print("      unexpected: %s" % "; ".join(repr(m) for m in pool))
    if failed:
        print("\n%d fixtures, %d FAILED" % (len(FIXTURES), failed))
    else:
        print(
            "%d fixtures: every rule fires on content that breaks it, and the healthy one is silent"
            % len(FIXTURES)
        )
    return failed


def main():
    try:
        with open(SHOTS, encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        print("FAIL: %s does not exist" % SHOTS)
        return 1
    except json.JSONDecodeError as e:
        print("FAIL: %s is not valid JSON: %s" % (SHOTS, e))
        return 1

    errors = check_shots(data)
    for where, msg in errors:
        print("ERROR %s: %s" % (where, msg))
    n = len(data) if isinstance(data, list) else 0
    print(
        "%s: %d shot(s) checked, %d error(s)" % (os.path.relpath(SHOTS, C.ROOT), n, len(errors))
    )

    print()
    fix_failed = run_fixtures()

    return 1 if (errors or fix_failed) else 0


if __name__ == "__main__":
    sys.exit(main())
