# Next session: M5 — the remaining chapters

Read this first, then `DECISIONS.md` (entries 23–35 are this phase), then `DATA-AUDIT.md §10`.

The readability overhaul is **done**. The generated half of the guide was already correct; this
phase made it readable, and in doing so it froze the shape every remaining chapter inherits. Your
job is to write the other chapters against that shape — not to redesign it.

Target reader, unchanged and still the only test that matters: **a ten-year-old who wants to know
what to do next.** If a sentence explains how the game works internally, it belongs on the
Technical notes page, not on the walkthrough.

---

## State as of this handoff

- **Live:** https://dev.jdayers.com/pkmn-world/ — CI deploys on every push to `main`
- **Repo:** https://github.com/evilchinesefood/PKMN-World-Guide (public), `main`, clean
- **Game pin:** submodule at `9ee61fbd` (`master`) — unchanged by this phase
- **1,632 pages · 22,240 internal links · 0 broken · 0 orphans · 0 unreachable**
- Extractor determinism holds across all 8 generated JSON files and the sprite extractor
- Milestones M0–M4 complete, plus the readability overhaul. M2 templates (`DECISIONS.md` 13–22)
  remain **frozen**; 23–35 record what this phase changed around them.

### What the eight changes produced

| #   | Change                   | Result                                                                                                                                                                                   |
| --- | ------------------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1   | Homepage is the guide    | Contents page: orientation block + chapter list in play order. **0** raw map links.                                                                                                      |
| 2   | New `/maps` page         | **1,195** map links, all of them, verified as a set equality against the manifest in both directions. Region sections kept, Sevii included.                                              |
| 3   | Maps inline in chapters  | **9** Leaflet viewers on the Kanto chapter, one per section, mounted lazily on scroll and eagerly on `beforeprint`.                                                                      |
| 4   | Numbered steps           | **45** steps across **9** sections; **37** carry an `at:` and draw a pin. Pin number **is** the step number, proven by mutation, and every pin sits within 1px of its step's real place. |
| 5   | Cut the prose            | Prose **448 → ~87 lines**. File is **287 lines** because the steps became data — see decision 30, this is a recorded deviation from the ~150 target, not an overrun.                     |
| 6   | Accordions               | Everything that is not a numbered step starts collapsed. Native `<details>`, **zero JavaScript**.                                                                                        |
| 7   | Insider Tips re-collapse | Toggles both ways and persists the closed state.                                                                                                                                         |
| 8   | Sprites                  | **1,978** PNGs (596 front pics + 596 icons + 786 item icons), 1.61 MiB of content, gitignored, CI-regenerated.                                                                           |

Two things fell out of the work that were not on the list: the base-form rule collapsed from three
drifting copies to one data field (decision 29, and it fixed two genuinely wrong Pokédex pages), and
`Links.mjs` gained an unreachable-page check (decision 34).

---

## What M5 inherits — read this before writing a single line

**`content/kanto/PalletToViridian.md` is the template for every future chapter.** Copy its shape.
Do not invent a second one.

**The `sections:` schema is frozen and its contract is written down** in
`content/kanto/PalletToViridianTechnical.md`, under "Chapter `sections:` schema". That page is not
notes — it is the specification, with the key tables, the `choice`/`choice_group` rules, six
specified edge cases, and the two house rules for pins. Read it in full before authoring. In
summary:

- A chapter's frontmatter carries an ordered `sections:` list. **One section = one map.** Every
  `at: [x, y]` inside it is local to that map.
- A step is a plain string or a mapping with `text`, optional `at`, optional
  `choice` + `choice_group`.
- `choice` is a **string** (`pick` | `depends`), never a boolean. `choice_group` is **required**
  whenever `choice` is present — see decision 25 for why adjacency was not good enough.
- A renderer that ignores both keys still emits correct output. The keys group; they never change
  step identity, numbering or pins.
- Each chapter needs `order:` and `summary:` in frontmatter. The homepage sorts on `order` and
  prints `summary` as the chapter's one-line description; without them the chapter falls to the
  end of the list with no blurb.
- Insider Tips attach via `companion_to:`, Technical notes via `technical_to:`. Both are declared
  **on the companion file only**, in one direction. The chapter carries no key pointing back.

Three files per chapter, then: the chapter, `…Tips.md`, `…Technical.md`. Kanto's are 287 / 111 /
441 lines and that ratio is about right — the Technical page is allowed to be the long one.

---

## Verification gate

Run in this order — it is the same order `.github/workflows/Deploy.yml` uses, and the extractors
are order-dependent (`Gates.py` runs last inside `All.py` and rewrites four files in place).

```
python3 tools/extract/All.py --check-determinism   # 8 JSON files, must be byte-stable
python3 tools/porymap/Render.py                    # 966 map PNGs, ~22s, gitignored
python3 tools/sprites/Extract.py                   # 1,978 sprite PNGs, gitignored
python3 tools/validate/CheckCoords.py              # coordinate invariants
./node_modules/.bin/astro build                    # NOT `npx astro build` -- see gotchas
node tools/qa/Links.mjs                            # 0 broken, 0 orphans, 0 unreachable
```

`Links.mjs` now enforces **three** conditions, not two. The third — no built page without an
inbound link — is the one that catches a stray content file publishing a page of its own, which
the manifest orphan check is structurally blind to. Expect to meet it: at M5 one misplaced
frontmatter key on a Tips or Technical file does exactly that.

Optional but useful: `node tools/qa/Shot.mjs <outdir> <url>…` screenshots served pages and reports
any JS errors on each. It scrolls before capturing — see the gotcha below for why that matters.

---

## Gotchas that will cost you an hour each

### Carried forward, all still true

- **`npx astro build` hangs on this machine.** No output, no error. `./node_modules/.bin/astro build`
  works instantly. Not understood; do not spend time on it. **CI uses `npx astro build` and it is
  fine there** — do not "fix" the workflow.
- **Piping a build through `| tail` buffers all output**, so a working build looks like a hang. Run
  it with `run_in_background` and poll the log.
- **Concurrent agents rewriting `data/generated/` cause phantom failures.** If Python and Node
  disagree about the same JSON file, something else is mid-write. Run the pipeline and the build in
  one command.
- **`rm` is blocked** in this harness. Use `git rm -f`, `git clean -ffdx <path>`, or `mv`.
- **`slugOf()` in `src/Names.ts` and the copy in `tools/qa/Links.mjs` must stay identical.** They
  drifted once and produced 486 phantom orphans. This phase deleted a similar three-way duplicate
  (decision 29) rather than synchronise it; do the same if you find another.
- The 22 hijacked trainer slots (`anomaly: "frlg_boss_in_hoenn_slot"`) carry Leader and Elite Four
  classes on ordinary route ids. **Any filter on `class` must exclude `anomaly`** or you get 65
  "gym leaders" instead of 24.
- **Never audit against the `/mnt/c` checkout.** The repo lives at `~/Projects/PKMN-World-Guide`
  (decision 5) and the Windows copy is stale.

### Discovered this phase

- **A `#if`-blind regex over the game's C headers silently binds everything to the wrong file.** In
  `src/data/graphics/pokemon.h` the GBA-style `#else` branch is declared _second_ and overwrites the
  correct entry, so a naive scan bound **every** species to its `_gba` sprite and looked entirely
  successful. Any extractor reading that header must track `#if`/`#else` state. There are **three**
  such macros, not the two the research named: `P_GBA_STYLE_SPECIES_GFX`, `…_ICONS` and
  `…_FOOTPRINTS`. `Extract.py` guards this in three layers, one of which is a hard error on any
  symbol reachable by two live paths — that layer is what found the third macro.
- **`tools/qa/Shot.mjs` used to grow the viewport instead of scrolling**, so `IntersectionObserver`
  never fired and any lazily-mounted content photographed as an empty box. Fixed in `8ced13a`, but
  the class of bug generalises: **a headless screenshot is not evidence about lazy content unless
  the tool actually scrolled.** A reviewer reading that screenshot would have called a working
  feature broken.
- **Print is a separate rendering path and it lies about images.** Mounting the maps on
  `beforeprint` looked correct and printed 41 of 46 images — the race is the **image decode**, not
  the component. Measure printed output by counting embedded image XObjects in the PDF, not by
  eyeballing the preview.
- **Do not trust a GBA PNG's embedded palette.** 20 of 596 species icons drift from the palette the
  source actually assigns via `.iconPalIndex` (Meowth-Gmax and Snorlax-Gmax badly). Apply the
  resolved `.pal` explicitly. 28 form directories need a parent-directory fallback for a missing
  local `normal.pal`.
- **`du -sh public/sprites` reports 7.9M and that number is a lie** — block-allocation slack on 1,978
  files averaging 850 bytes against a 4 KiB block. Use `--apparent-size` (1.7M) before re-litigating
  commit-vs-regenerate.
- **`technical_to` must be excluded everywhere `companion_to` is**, or the Technical page publishes
  as a walkthrough chapter. Four sites, already fixed — but **not** the positive lookup in
  `walkthrough/[slug].astro`, which resolves the companion and cannot match. Companion resolution
  compares **full normalised paths**, not basenames; `kanto/RouteOne.md` and `johto/RouteOne.md`
  would otherwise collide, and at M5 they will exist.
- **Hovering Leaflet pins to read their tooltips produces false failures.** Adjacent-block icons
  overlap, so the hover lands on the neighbour. Verify pin identity from the DOM and derive
  positions from the image overlay's own rect instead.
- **A "which form is dex N" rule must never be written again.** `is_base_form` in `species.json` is
  the answer, `baseForm()` in `src/Species.ts` is the only reader. A `grep` for
  `MEGA|ALOLA|ALT_FORM` across `src/` and `tools/` returning anything but comments is a regression.

---

## Deferred findings, triaged

Thirty-eight items were raised during this phase, judged real but not blocking, and deferred. They
are listed here most valuable first. Nothing here is a known-broken page — the gate is green — but
the first group will bite M5 specifically.

### A. M5 prerequisites — do these before writing chapter two

1. **Nothing validates `choice_group`.** The renderer degrades silently on genuine authoring errors
   (a group of one, `choice_group` without `choice`, a mismatched `choice` value inside a run). The
   schema was designed so these are _detectable_; nothing yet detects them. A check in
   `tools/validate/` is the single highest-value item on this list.
2. **Section `id`s are unvalidated.** `walkthrough/[slug].astro` takes the YAML `id` straight into a
   DOM id and the viewer's `steps` key. Two sections sharing an id silently hand the second viewer
   the **first** section's pins, plus duplicate DOM ids. Twenty-four chapters of hand-written ids
   will hit this.
3. **`index.astro` hard-codes "so far the only one with a written chapter".** Hand-written prose that
   a second chapter silently falsifies. Derive it from `chapters.length`. This one goes wrong the
   day M5 lands its first file.
4. **`data-step` can diverge from the badge.** If a step ever renders without `data-step`, the CSS
   badge falls back to `counter(step)` while the pin script's `li[data-step]` query skips it —
   numbers drift. Currently unreachable, but guard it with a QA lint or mandate
   `dataset.step ?? index + 1`.
5. **Steps render above the markdown body and the body cannot be split.** Kanto's body ends in a
   departure checklist that means nothing before the walk. Near-zero cost today; it grows with
   longer chapters. Decide the convention now: bodies open with scene-setting, never close with
   instructions.
6. **The step legend renders whenever `steps` is set**, even if no step in that section has an `at:`
   — a legend for pins that do not exist.

### B. Correctness, cheap

7. Encounter tables render in source order, so DexNav can sit above Tall Grass. One-line fix.
8. `wildSpecies` counts include `species_enabled === false` slots.
9. `sourceCount` counts each evolution parent separately but renders them as one sentence — the
   count in the fold summary overstates on 26 pages.
10. The homepage's "warps you back whenever you want" drops a real qualifier:
    `CannotUseHubReturnHere()` blocks the Hub Pass in the Safari Zone, the Bug Contest, link/union
    rooms and Frontier/Trainer Hill runs. None are reachable on turn one, which is why it was not
    ranked higher.
11. 332 extracted sprites (166 front + 166 icon, ~0.39 MiB) are referenced by nothing — 596 emitted,
    430 used. Deliberate headroom for alt-form art, but `Links.mjs` checks pages, not assets, so
    nothing would notice if it stayed dead forever.

### C. Accessibility and UX

12. **The 37 step pins are keyboard traps in miniature** — `role="button" tabindex="0"` with the
    bare numeral as their only accessible name. A keyboard user tabs 37 controls announced "3,
    button". `L.marker`'s `alt` fixes it. Highest-value item in this group.
13. Steps one block apart draw overlapping 26px icons (Viridian 13/14, the three starter balls).
    Decluttering needs a Leaflet plugin.
14. The chapter page is now ~13,500px tall, ~4,300px of it maps (viewers capped at 30rem).
15. With JS off, the chapter reserves nine 780×480 boxes — ~4,300px of nothing.
16. `bindTooltip(string)` goes through `innerHTML`, breaking the `textContent` invariant asserted by
    a comment twelve lines above. Not exploitable (repo-authored), but step text containing `<`
    renders wrong.
17. The `/maps` filter is a plain substring, so "route1" also matches route10 and route11 — 101 hits
    for a query the reader meant as exact.
18. `opacity: 0.7` on an open `.peek` dims the label text, not just the border.
19. Trainer fold summaries repeat the name already in `TrainerCard`'s header.
20. `fitBounds` + `zoomSnap 0.25` letterboxes square-ish maps. Pre-existing, also on map pages.

### D. Print

21. Encounter tables, trainer tables and the rail still print on their dark panel backgrounds, so
    the bottom third of a printed chapter is ink-heavy. Pre-existing, in the design system's print
    block.
22. Fold print-expansion is verified in Chromium only; older engines print folds collapsed. The
    in-code comment overstates coverage — the real floor is Chromium ≥128 / Firefox ≥139 /
    Safari ≥18.4.
23. The map image prefetch costs 227 KB for a reader who opens a chapter and leaves immediately.

### E. Tooling robustness

24. `Extract.py` treats any unrecognised flag as the output directory — `Extract.py --dry-run`
    creates `./--dry-run/`.
25. `Extract.py`'s item-count assertion fires _after_ every item PNG is written, so a failure leaves
    partial output.
26. `Extract.py`'s `a % 16 if a.max() > 15` would silently fold a genuine 8bpp source rather than
    reject it.
27. `Extract.py`'s "no `.frontPic`/`.iconSprite`" error also fires on a missing `.iconPalIndex` and
    does not say so.
28. CI runs `Extract.py` without `--check-determinism` (matching the `Render.py` precedent), so
    sprite non-determinism would ship rather than fail.
29. `Links.mjs` exits on the reachability failure _before_ the manifest orphan check, so one
    unlinked page suppresses the orphan report for that run.
30. `Shot.mjs` reads `scrollHeight` once before the walk, so a page that grows while scrolling is
    under-captured.
31. `Sprites.ts` reads its directory once at module load, so `astro dev` misses sprites that appear
    mid-session. Nothing mechanically prevents it being pulled into a client bundle either — the
    guard is a comment plus a `dist/` grep.
32. `baseForm()` hard-stops the whole build if a future re-pin yields 0 or 2 base forms for a dex
    number. Correct, but loud; and per-species sprite extraction has the same no-slack property —
    one enabled species missing `.frontPic`/`.iconSprite`/`.iconPalIndex` fails the entire run. Both
    are fine at `9ee61fbd`; both are re-pin risks.
33. `Species.py`'s `form_tables()` is a third `cpp` invocation, on a header `species_info.h` does not
    include, and omits `metaprogram.h` — "same flags" overstates the parity.
34. `src/Species.ts` degrades to `"dex undefined: 0 base forms among "` on an empty forms array.
    Unreachable from both call sites today.

### F. Housekeeping

35. There is **no `.prettierrc`**, so formatting `.astro` files needs an explicit
    `--plugin=prettier-plugin-astro`. Adding one would remove a recurring papercut.
36. `docs/SCHEMAS.md` fails `prettier --check` for pre-existing reasons unrelated to any recent
    change. Left alone deliberately; fix it as its own commit or not at all.
37. `--edge`, `--spoil-bg` and `--spoil-bg-h`, referenced by `Spoiler.astro`, are undefined in
    `Guide.css`. Pre-existing; the component renders on fallbacks.
38. `localStorage.getItem` is called outside a `try`/`catch` in `Spoiler.astro` and `Base.astro`
    (pre-existing), and `pw:hide-all` clears the site-wide revealed set rather than only the gates
    in the current DOM. Relatedly, while `pw-reveal-all == "1"` an individual close does not survive
    a reload and nothing in the UI explains why — spec-compliant, but confusing.

---

## Still open, needs the reader

- **M5** — walkthroughs for three regions, 24 boss pages, the three leagues, Red at Mt. Silver, the
  15-trainer World Championship (audit Q12 deferred these here). The brief says this content is a
  byproduct of the 1.0 playthrough. `content/kanto/PalletToViridian.md` is the template and the
  `sections:` schema is the contract.
- **M6** — Pagefind search, mGBA screenshot automation, print/PDF export, version diff page. Note
  that print now works well enough to be worth building on rather than around (decision 35).
- **`DATA-AUDIT.md §10`** — Q11 (Johto has only 3 hidden items), Q13 (quest system), Q14 (config
  ternaries), Q18 (4 out-of-bounds events), Q20/Q22 open items.
- **Five game bugs filed upstream:** PKMN-World issues #36, #37, #38, #39, #40. #36 (22 trainer
  slots holding Kanto boss parties) is decided as publish-as-is; the rest are unanswered.
- **A form column for the species "Where to get it" table.** Decision 33 refused to union regional
  forms onto the base page because the table cannot say which form a row yields. Adding that column
  makes the union honest and unlocks ~20 thin pages. Content task, not a rendering one.
