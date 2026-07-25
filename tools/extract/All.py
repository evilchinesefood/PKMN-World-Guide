"""Runs every extractor in dependency order. `npm run extract`."""

import os, sys, subprocess, hashlib, glob

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import Common as C

ORDER = ["Maps", "Encounters", "Trainers", "Species", "Items", "ItemLocations", "Progression", "Systems"]


def digest():
    h = {}
    for p in sorted(glob.glob(os.path.join(C.OUT, "*.json"))):
        with open(p, "rb") as f:
            h[os.path.basename(p)] = hashlib.sha256(f.read()).hexdigest()[:12]
    return h


def main():
    check = "--check-determinism" in sys.argv
    before = digest() if check else {}
    fail = []
    for name in ORDER:
        p = os.path.join(HERE, name + ".py")
        if not os.path.isfile(p):
            print(f"-- {name}: not written yet, skipped")
            continue
        print(f"== {name}")
        r = subprocess.run([sys.executable, p])
        if r.returncode:
            fail.append(name)
    after = digest()
    print(f"\n{len(after)} files in data/generated/")
    for k, v in sorted(after.items()):
        print(f"  {v}  {k}")
    if check:
        changed = [k for k in after if before.get(k) and before[k] != after[k]]
        print(f"\ndeterminism: {len(changed)} file(s) changed on re-run {changed}")
        if changed:
            fail.append("determinism")
    if fail:
        print(f"\nFAILED: {fail}")
    return 1 if fail else 0


if __name__ == "__main__":
    sys.exit(main())
