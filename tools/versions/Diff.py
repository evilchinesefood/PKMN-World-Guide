"""Version diff: what the guide's own committed data says changed between two game pins.

Writes data/versions/versions.json -- one row per pin the repo has ever carried, and one
transition per consecutive pair, so the next re-pin does not need a person to re-measure
DECISIONS.md 52's two-column table by hand.

NOT data/generated/. That directory is a pure function of the pinned submodule, and
All.py --check-determinism makes an exact, load-bearing claim about it: 8 JSON files, all
byte-stable on a re-run. This file is a function of the repo's HISTORY, which re-running
the extractors cannot reproduce, so a 9th file in there would quietly make that claim
wrong. data/manifest/map-manifest.json is the precedent for a committed generated file
living outside data/generated/.

CI MUST NOT REGENERATE THIS, and Deploy.yml does not. `actions/checkout@v4` clones at
depth 1 unless told otherwise, so the history this tool reads is simply absent there: it
would find one pin, no transition, and overwrite a real diff with an empty one that still
parses, still validates, and says the guide never changed. The output is committed for
exactly that reason. Same shape of trap as NEXT.md F30.

RE-PINNING IS TWO COMMITS. Re-pin and re-extract in one, as bde510f did, then run this and
commit versions.json in a second. Nothing here checks anything out or reads the working
tree -- every byte comes from `git cat-file` -- so the tool cannot see a new pin until that
pin's data is committed.

The two halves are read from opposite directions. Pins come from the submodule gitlink
(`git log -- game`), which is the authority on what was ever pinned and the only way the
v1.3.6 pin appears at all: it predates every extractor, no maps.json carries it, and a walk
of the generated data alone would silently drop a third of the repo's pin history rather
than report an empty row with a reason. Which data belongs to which pin comes the other
way, from `game_commit` inside maps.json at each commit that touched data/generated/.

A pin is snapshotted at its LAST data commit, not its first. The extractors landed
incrementally -- 13ec4de0 committed three of the eventual eight files -- so snapshotting a
pin where its data first appears reports five whole collections as freshly added at the
next transition, and attributes the guide's own build-out to an upstream re-pin.

TWO IDENTITY KEYS ARE COMPOSITE, and getting either wrong fails silently rather than
loudly. `trainer_id` is not unique -- a HARD rematch is a second record under the same id,
as src/pages/gyms/index.astro documents -- so keying on it alone drops 42 of 1767 records
and diffs each surviving rematch against a normal-difficulty party. `encounters[].map` is
not unique either: 479 tables live on 331 maps, 18 of them on MAP_SIX_ISLAND_ALTERING_CAVE,
so keying on the map drops 148 tables and a change inside a shadowed one reads as no change
at all. _index() refuses to overwrite a key rather than let either happen quietly.

PROVENANCE DRIFT DOMINATES A NAIVE RECORD COMPARISON. Every record carries the C.source()
{file, key, line} pointer into the game tree, some a `gate_source` as well. At
9ee61fbd -> 2b1fba48, 876 of 1767 trainer records differ and 854 of them differ only in one
of those pointers -- 829 in source.line alone, because upstream edited trainers.party above
them, 25 in gate_source. "876 trainers changed" is true of the JSON and false of the guide.
So the provenance-only count is reported beside the total, and the capped id list leads
with the records that changed in something a reader can see: 876 - 854 leaves exactly the
22 hijacked slots DECISIONS.md 52 records as fixed, and a plain sort would have spent the
whole cap on line drift and shown none of them.
"""

import os, sys, json, subprocess, tempfile

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "extract"))
import Common as C

OUTDIR = os.path.join(C.ROOT, "data", "versions")
NAME = "versions.json"
GENERATED = "data/generated"
MAPS = GENERATED + "/maps.json"

# Named ids per list, with the true total beside every capped list. A re-pin that rewrites
# a collection wholesale must still produce a page rather than a wall, and must not grow
# this file by a megabyte to say so.
CAP = 50

# Every collection the page can talk about: file -> collection -> the fields that identify
# a record, or None where the collection is a dict already keyed by the game constant it
# describes. A collection's name is also the top-level key it lives under. The rest of each
# file is scalars and lookup tables with no id to diff, and the per-file byte row still
# catches those moving.
COLLECTIONS = {
    "battledata.json": {c: None for c in ("abilities", "items", "moves", "species", "types")},
    "encounters.json": {"encounters": ("map", "base_label")},
    "items.json": {"items": ("id",)},
    "maps.json": {"maps": ("id",)},
    "progression.json": {"gates": ("key",)},
    "species.json": {"species": ("id",)},
    "systems.json": {"systems": ("key",)},
    "trainers.json": {"trainers": ("trainer_id", "difficulty")},
}
FILES = sorted(COLLECTIONS)

# The exact shape C.source() returns. A field is provenance if it has that shape, and
# nothing else in the generated data does.
SOURCE_SHAPE = {"file", "key", "line"}


# --- git ---------------------------------------------------------------------
# Read-only, and deliberately so: blobs by revision, never a checkout, never the
# working tree. A tool that moved the gitlink to measure it would be re-pinning the
# submodule as a side effect of describing it.


def _git(*args):
    r = subprocess.run(("git", "-C", C.ROOT) + args, capture_output=True)
    if r.returncode:
        raise SystemExit("git %s: %s" % (" ".join(args), r.stderr.decode().strip()))
    return r.stdout


def _text(*args):
    return _git(*args).decode().strip()


def _oid(commit, path):
    """The blob id at <commit>:<path>, or None when the path does not exist there."""
    r = subprocess.run(
        ("git", "-C", C.ROOT, "rev-parse", "--verify", "--quiet", f"{commit}:{path}"),
        capture_output=True,
    )
    return r.stdout.decode().strip() or None


def _blob(commit, path):
    return json.loads(_git("cat-file", "blob", f"{commit}:{path}"))


def pins():
    """Every pin the repo has carried, oldest first, read from the gitlink itself."""
    log = _text("log", "--reverse", "--date=short", "--format=%H %ad", "--", "game")
    if not log:
        # The shallow-clone case the docstring warns about, made legible. Left to itself
        # this walks an empty log and reports a repo that has never had a pin.
        raise SystemExit("no commit in this clone touches game/ -- history is missing, "
                         "probably a shallow checkout; versions.json is committed for that reason")
    out = []
    for line in log.split("\n"):
        commit, date = line.split()
        out.append(
            {
                "game_commit": _text("rev-parse", f"{commit}:game"),
                "guide_commit": commit,
                "date": date,
                "data_commit": None,
            }
        )
    return out


def snapshots():
    """pin -> the newest commit whose data/generated/ was extracted at that pin."""
    out, by_blob = {}, {}
    log = _text("log", "--format=%H", "--", GENERATED)
    # An empty log would leave `commit` empty below, and `git rev-parse :path` with no
    # revision reads the INDEX -- the one place this tool must never look.
    for commit in log.split("\n") if log else []:
        blob = _oid(commit, MAPS)
        if blob is None:
            continue  # data/generated/ existed at this commit but held no maps.json yet
        if blob not in by_blob:
            by_blob[blob] = _blob(commit, MAPS)["game_commit"]
        out.setdefault(by_blob[blob], commit)  # newest first, so the first hit wins
    return out


# --- diff --------------------------------------------------------------------


def _canon(v):
    return json.dumps(v, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


def _content(rec):
    """The record minus its provenance pointers."""
    if not isinstance(rec, dict):
        return rec
    return {k: v for k, v in rec.items() if not (isinstance(v, dict) and set(v) == SOURCE_SHAPE)}


def _index(where, records, fields):
    out = {}
    for r in records:
        k = ":".join(str(r[f]) for f in fields)
        if k in out:
            raise SystemExit(f"{where}: {'+'.join(fields)} is not unique -- two records key on {k}")
        out[k] = r
    return out


def _capped(ids):
    return {"total": len(ids), "ids": ids[:CAP]}


def _diff(before, after):
    both = set(before) & set(after)
    changed = sorted(k for k in both if _canon(before[k]) != _canon(after[k]))
    provenance = {k for k in changed if _canon(_content(before[k])) == _canon(_content(after[k]))}
    return {
        "before": len(before),
        "after": len(after),
        "added": _capped(sorted(set(after) - set(before))),
        "removed": _capped(sorted(set(before) - set(after))),
        # Two sorted groups rather than one, so the cap is spent on records a reader can
        # see a difference in. Deterministic either way; only the order differs.
        "changed": _capped([k for k in changed if k not in provenance] + sorted(provenance)),
        "changed_provenance_only": len(provenance),
    }


def compare(a, b):
    """Diff the data/generated/ trees of two guide commits, one file at a time."""
    out = {}
    for f in FILES:
        p = f"{GENERATED}/{f}"
        before, after = _blob(a, p), _blob(b, p)
        colls = {}
        for coll, fields in sorted(COLLECTIONS[f].items()):
            x, y = before[coll], after[coll]
            if fields:
                x = _index(f"{a[:8]} {f} {coll}", x, fields)
                y = _index(f"{b[:8]} {f} {coll}", y, fields)
            colls[coll] = _diff(x, y)
        # progression.json and systems.json move at a re-pin without any collection moving
        # -- only their game_commit line -- and both SHAs are 40 characters, so the byte
        # counts match while the blobs differ. `identical` is the only row that catches
        # that, and a file that moves while every one of its collections reads flat is the
        # signal that this tool is not looking at something it should be.
        out[f] = {
            "bytes_before": int(_text("cat-file", "-s", f"{a}:{p}")),
            "bytes_after": int(_text("cat-file", "-s", f"{b}:{p}")),
            "identical": _oid(a, p) == _oid(b, p),
            "collections": colls,
        }
    return out


def build():
    ps = pins()
    snap = snapshots()
    known = {p["game_commit"] for p in ps}
    for pin in sorted(snap):
        # Generated data built against a pin the gitlink never held means someone extracted
        # from a dirty submodule. Every count downstream would be attributed to the wrong
        # commit, so say so instead of publishing it.
        if pin not in known:
            raise SystemExit(
                f"{MAPS} at {snap[pin][:8]} was built at pin {pin[:8]}, which `git log -- game` never records"
            )
    for p in ps:
        p["data_commit"] = snap.get(p["game_commit"])

    transitions = []
    for a, b in zip(ps, ps[1:]):
        missing = [p["game_commit"][:8] for p in (a, b) if not p["data_commit"]]
        reason = None
        if missing:
            reason = "no commit carries extractor output built at %s, so there is nothing to compare" % (
                " or ".join(missing)
            )
        transitions.append(
            {
                "from": a["game_commit"],
                "to": b["game_commit"],
                "comparable": not missing,
                "reason": reason,
                "files": None if missing else compare(a["data_commit"], b["data_commit"]),
            }
        )
    return {
        "cap": CAP,
        "generator": {"name": "tools/versions/Diff.py", "version": "1.0.0"},
        "pins": ps,
        "transitions": transitions,
    }


# --- output ------------------------------------------------------------------


def render(payload):
    """The exact bytes C.write would commit, produced by C.write itself.

    Re-serialising here instead would let --check keep passing while this file drifted
    from Common.write's formatting, which is the one thing --check exists to catch.
    """
    with tempfile.TemporaryDirectory() as d:
        with open(C.write(NAME, payload, d), "rb") as f:
            return f.read()


def report(payload, path, size):
    print(f"{len(payload['pins'])} pins, {len(payload['transitions'])} transitions -> {path}")
    for p in payload["pins"]:
        data = p["data_commit"][:8] if p["data_commit"] else "no data"
        print(f"  {p['game_commit'][:8]}  {p['date']}  guide {p['guide_commit'][:8]}  data {data}")
    for t in payload["transitions"]:
        print(f"\n{t['from'][:8]} -> {t['to'][:8]}")
        if not t["comparable"]:
            print(f"  not comparable: {t['reason']}")
            continue
        for f, fd in sorted(t["files"].items()):
            flag = "same" if fd["identical"] else "differs"
            print(f"  {f:18s} {fd['bytes_before']:>9} -> {fd['bytes_after']:<9} {flag}")
            for coll, d in sorted(fd["collections"].items()):
                n = d["changed_provenance_only"]
                print(
                    f"    {coll:16s} {d['before']:>5} -> {d['after']:<5}"
                    f"  +{d['added']['total']} -{d['removed']['total']} ~{d['changed']['total']}"
                    + (f"  ({n} provenance only)" if n else "")
                )
    print(f"\nsize {size} bytes")


def main():
    payload = build()
    path = os.path.join(OUTDIR, NAME)
    if "--check" in sys.argv:
        if not os.path.isfile(path):
            print(f"FAIL: {path} is missing; run this without --check and commit the result")
            return 1
        want = render(payload)
        with open(path, "rb") as f:
            have = f.read()
        report(payload, path, len(want))
        print("check: " + ("matches" if have == want else "FAIL: differs from the file on disk"))
        return 0 if have == want else 1
    C.write(NAME, payload, OUTDIR)
    report(payload, path, os.path.getsize(path))
    return 0


if __name__ == "__main__":
    sys.exit(main())
