# Next session: M5 — the remaining chapters

Read this first, then `DECISIONS.md` (entries 23–46 are this phase), then `DATA-AUDIT.md §10`.

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
- **Game pin:** submodule at **`2b1fba48`** (`master`) — **re-pinned 2026-07-27**, see
  `DECISIONS.md` 52. The five game bugs are fixed and the guide is measured at the new pin.
- **1,633 pages · 23,886 internal links · 0 broken · 0 orphans · 0 unreachable** (links 23,880 →
  23,886 at the re-pin: Lunatone and Zangoose gained encounter locations)
- Extractor determinism holds across all 8 generated JSON files and the sprite extractor
- Milestones M0–M4 complete, plus the readability overhaul. M2 templates (`DECISIONS.md` 13–22)
  remain **frozen**; 23–46 record what this phase and the post-ship work changed around them.
- Top nav is Pokédex · Items · Gyms · Maps · **Features** — the last one new, generated from the
  game's own `FEATURES.md` out of the pinned submodule (decision 40).

### What the eight changes produced

| #   | Change                   | Result                                                                                                                                                                                   |
| --- | ------------------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1   | Homepage is the guide    | Contents page: orientation block + chapter list in play order. **0** raw map links.                                                                                                      |
| 2   | New `/maps` page         | **1,195** map links, all of them, verified as a set equality against the manifest in both directions. Region sections kept, Sevii included.                                              |
| 3   | Maps inline in chapters  | **9** Leaflet viewers on the Kanto chapter, one per section, mounted lazily on scroll and eagerly on `beforeprint`.                                                                      |
| 4   | Numbered steps           | **44** steps across **9** sections; **37** carry an `at:` and draw a pin. Pin number **is** the step number, proven by mutation, and every pin sits within 1px of its step's real place. |
| 5   | Cut the prose            | Prose **448 → ~87 lines**. File is **290 lines** because the steps became data — see decision 30, this is a recorded deviation from the ~150 target, not an overrun.                     |
| 6   | Accordions               | Everything that is not a numbered step starts collapsed. Native `<details>`, **zero JavaScript**.                                                                                        |
| 7   | Insider Tips re-collapse | Toggles both ways and persists the closed state.                                                                                                                                         |
| 8   | Sprites                  | **1,978** PNGs (596 front pics + 596 icons + 786 item icons), 1.61 MiB of content, gitignored, CI-regenerated.                                                                           |

Two things fell out of the work that were not on the list: the base-form rule collapsed from three
drifting copies to one data field (decision 29, and it fixed two genuinely wrong Pokédex pages), and
`Links.mjs` gained an unreachable-page check (decision 34).

### And what the closing fix wave produced

The final review found seven must-fix items and they were all addressed before the push. What
changed, because several of these are things M5 would otherwise re-discover:

- **Four content claims in the chapter were false or self-contradicting at source** and are now
  corrected. The chapter is a walkthrough, so a wrong claim is the worst defect class it has —
  budget review time for source-checking every hand-written claim in M5, not just the numbers.
- **A heading that counted something its children did not** is fixed across **330** pages
  (decision 39). "Wild Pokémon (N)" counted distinct species over folds that count rows.
- **Spoilers now print revealed** on 125 map pages (decision 37) — they previously printed as a
  heading, a dead button, and no table.
- **Nothing scrolls sideways at 390px**, and `tools/qa/Shot.mjs` gained `SHOT_WIDTH` so a phone
  width can actually be photographed. Phone is a supported width now; treat it as one.
- **The chapter body's reference tables fold** (decision 38), which is what the phase was for:
  chapter height **13,509 → 11,852px**, and the dead space below the last step **2,882 → 1,345px,
  a 53% cut**. Steps, the "where you go next" section and the departure checklist stay open.

One step was cut as unfollowable, which is why the count is 44 and not the 45 quoted mid-phase.

### And what landed after the push

- **The departure checklist is real.** `- [ ]` used to compile to a disabled, dead checkbox. It now
  ticks, and the ticks persist per chapter, keyed by a hash of each item's own text so that
  inserting an item cannot slide everyone's ticks down (decision 43). 23 Playwright assertions,
  including the one that matters most — a key absent from storage stays unticked, so a new item is
  never silently already done.
- **Maps no longer steal the page's scroll** (decision 44). The wheel bug was visible; the touch
  bug was worse and invisible — a one-finger drag moved the page **0px** because Leaflet's own
  stylesheet forbids the browser from scrolling. One finger now scrolls, two pan and pinch.
- **`/features/` exists**, generated from the game's own `FEATURES.md` out of the pinned submodule
  (decisions 40–42). 9 of 10 `<h2>` and 23 of 23 `<h3>` render; the one drop is `Table of Contents`,
  named explicitly in `src/Features.ts` rather than silently omitted.
- **320px stopped scrolling sideways** — `flex-wrap` on `.banner nav`, closing a deferred item.

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

Three files per chapter, then: the chapter, `…Tips.md`, `…Technical.md`. Kanto's are 290 / 113 /
458 lines and that ratio is about right — the Technical page is allowed to be the long one.

### One authoring constraint the body imposes on you

Decision 38 folds a body `<h2>` section **if it contains table rows or any `<li>`** — the signal is
mechanical, so no per-chapter list has to be maintained. The consequence is a trap:

> **A "where you go next" section that carries even two bullet points will silently collapse.**

The template's own comment says that section must never sit behind a click, and on this chapter it
is protected only because it happens to be prose-only. It degrades to a click, not to wrong
information, and you will see it the moment you look at the page — but you have to look. Write
"where you go next" as prose, or accept the fold deliberately. Twenty-four boss pages and three
leagues is a lot of chances to do it by accident.

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
- ~~The 22 hijacked trainer slots carry Leader and Elite Four classes on ordinary route ids, so any
  filter on `class` must exclude `anomaly`.~~ **No longer true — fixed upstream, 0 anomalies at
  `2b1fba48`.** The `anomaly` filter on `/gyms/` is now a no-op: 24 leaders with it and without it,
  on the same id set. **Keep filtering it anyway.** The extractor's detection is retained as a
  regression tripwire, and the filter is its render-side half — if that paste ever recurs the page
  must not grow. A new generator should still exclude `anomaly`; it just will not change anything
  today.
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
- **The site sets `scroll-behavior: smooth`, so a `scrollIntoView` is still animating when you place
  a pointer.** Any test that positions a cursor must disable smooth scrolling and **assert that
  `elementFromPoint` is actually over the target** — otherwise the wheel event lands on empty page
  and the test reports PASS. It did exactly that once. Third instance of the same family as the
  `Shot.mjs` viewport bug and the hover-the-pin tooltip failures: **the harness quietly measured
  something other than what it claimed to.** Assume that is happening until you have asserted it is
  not.
- **`requestIdleCallback` is not in stable Safari, so the fallback is a live path, not a
  theoretical one.** Every Safari reader takes `load` + 500ms instead of the idle callback for the
  map image prefetch. It was verified to produce a byte-identical PDF, so this is documentation
  rather than a defect — but the next person to touch that code must test the fallback branch,
  because a whole browser is on it.
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

Forty-six items were raised across this phase and the post-ship work, judged real but not blocking,
and deferred. They are listed most valuable first. Nothing here is a known-broken page — the gate is
green — but **group A must be closed before the re-pin** and group B will bite M5 specifically.

### A. Close these before the re-pin — ✅ BOTH CLOSED

Closed by decisions 47–51, before the gitlink moved on 2026-07-27. Both were latent at `9ee61fbd`
and fired on new input, which is exactly what a re-pin and 45–58 new chapters are. Retained below
as the record of what was wrong, since 45–58 chapters still inherit the fixed code.

1. **`src/Checklist.ts:68` corrupts an item that has a nested sub-list.** The non-greedy
   `([\s\S]*?)</li>` stops at the **child's** `</li>`, so the match ends early: the item's markup
   comes out unbalanced, the child's text folds into the parent's hash, and a sibling can escape
   the label. Today's chapter is flat, which is the only reason it is invisible — **40–58 chapters
   inherit it** and it fires the first time an author indents a bullet under a checklist line.
   That is an ordinary thing to write, so treat it as a certainty rather than an edge case.
2. **`src/Features.ts:151` publishes an unknown status marker as playable.** `STATUS_RE` matches
   only `unreleased|dormant`, so a re-pin adding `## Battle Frontier (beta)` gets **no warning and
   also loses its tier** to the same parenthesis problem `4dcab7f` just fixed for the two known
   words. Verified for `(beta)`, `(planned)`, `(WIP)`, `(coming soon)`, `(experimental)`. Decision
   41 chose "publish into the middle tier" over "fail the build" for an unknown _heading_, and that
   is right — but an unknown _status_ is different in kind: the failure is a section presented as
   shipped when the game says it is not. Match any parenthesised marker, and treat an unrecognised
   one as a warning rather than as silence.

### B. M5 prerequisites — do these before writing chapter two

3. **Nothing validates `choice_group`.** The renderer degrades silently on genuine authoring errors
   (a group of one, `choice_group` without `choice`, a mismatched `choice` value inside a run). The
   schema was designed so these are _detectable_; nothing yet detects them. A check in
   `tools/validate/` is the single highest-value item on this list.
4. **A body section folds if it contains any `<li>`, including "where you go next".** See the
   authoring constraint above. The template's own comment says that section must never sit behind a
   click, and it holds today only because this chapter's happens to be prose-only. Two bullet points
   would collapse it silently. Either teach the renderer to exempt that heading, or write the rule
   into the schema contract on the Technical page so 24 boss pages inherit it deliberately.
   Degrades to a click, not to wrong information — which is why it is not in group A.
5. **Section `id`s are unvalidated.** `walkthrough/[slug].astro` takes the YAML `id` straight into a
   DOM id and the viewer's `steps` key. Two sections sharing an id silently hand the second viewer
   the **first** section's pins, plus duplicate DOM ids. Forty-plus chapters of hand-written ids
   will hit this.
6. **`index.astro` hard-codes "so far the only one with a written chapter".** Hand-written prose that
   a second chapter silently falsifies. Derive it from `chapters.length`. This one goes wrong the
   day M5 lands its first file.
7. **`data-step` can diverge from the badge.** If a step ever renders without `data-step`, the CSS
   badge falls back to `counter(step)` while the pin script's `li[data-step]` query skips it —
   numbers drift. Currently unreachable, but guard it with a QA lint or mandate
   `dataset.step ?? index + 1`.
8. **Steps render above the markdown body and the body cannot be split.** Everything in the body
   therefore follows every step, whatever it is about. Near-zero cost today; it grows with longer
   chapters. Decide the convention now: bodies open with scene-setting, and anything that is an
   instruction belongs in `sections:` as a step.
9. **The step legend renders whenever `steps` is set**, even if no step in that section has an `at:`
   — a legend for pins that do not exist.

### C. Correctness, cheap

10. **The species "Where to get it" count overstates on 228 of 427 pages** — 202 by one, 25 by two,
    1 by three. `sourceCount` counts each evolution parent separately while the body renders them as
    a single sentence. Recorded mid-phase as 26 pages; the real figure is roughly nine times that,
    measured at `a0ed3a8` and byte-identical there, so it is pre-existing rather than introduced.
    **Triage it by severity, not by the count**: unlike decision 39's heading, this fold is open by
    default, so the number sits directly above the content it disagrees with and a reader can see
    both at once. That makes it less corrosive than a count hidden behind a click — but it is on 228
    pages, and the fix is the same shape as 39's.
11. ~~Two checklist items with identical text share a key~~ — **fixed**, decision 48. Later copies
    are suffixed `~2`, `~3`; deleting a duplicate still shifts survivors, and the build warns.
12. ~~`- [x]` in source silently loses its pre-checked state~~ — **fixed**, decision 48. It is a
    build warning naming file and line; it will never pre-tick.
13. Encounter tables render in source order, so DexNav can sit above Tall Grass. One-line fix.
14. `wildSpecies` counts include `species_enabled === false` slots.
15. The homepage's "warps you back whenever you want" drops a real qualifier:
    `CannotUseHubReturnHere()` blocks the Hub Pass in the Safari Zone, the Bug Contest, link/union
    rooms and Frontier/Trainer Hill runs. None are reachable on turn one, which is why it was not
    ranked higher.
16. 332 extracted sprites (166 front + 166 icon, ~0.39 MiB) are referenced by nothing — 596 emitted,
    430 used. Deliberate headroom for alt-form art, but `Links.mjs` checks pages, not assets, so
    nothing would notice if it stayed dead forever.

### D. Accessibility and UX

Two items that were here — the 320px sideways scroll and the layer control covering a small map —
are **fixed**, in `0e4053d` and `d1c4845`. See decision 44.

17. **The 37 step pins are keyboard traps in miniature** — `role="button" tabindex="0"` with the
    bare numeral as their only accessible name. A keyboard user tabs 37 controls announced "3,
    button". `L.marker`'s `alt` fixes it. Highest-value item in this group.
18. Overlapping 26px pin icons on the Viridian sequence: **two pairs, 8/9 and 13/14, both 11px
    apart** (plus the three starter balls, which are adjacent by design). Decluttering needs a
    Leaflet plugin. Worse on a phone, where two of Viridian's fourteen pins hide behind neighbours
    until you zoom.
19. The chapter page is **11,852px** tall (down from 13,509 before the fix wave), ~4,300px of it
    maps. Dead space below the last step is now **1,345px**, down from 2,882.
20. With JS off, the chapter reserves nine 780×480 boxes — ~4,300px of nothing.
21. `bindTooltip(string)` goes through `innerHTML`, breaking the `textContent` invariant asserted by
    a comment twelve lines above. Not exploitable (repo-authored), but step text containing `<`
    renders wrong.
22. The `/maps` filter is a plain substring, so "route1" also matches route10 and route11 — 101 hits
    for a query the reader meant as exact.
23. `opacity: 0.7` on an open `.peek` dims the label text, not just the border.
24. Trainer fold summaries repeat the name already in `TrainerCard`'s header.
25. `fitBounds` + `zoomSnap 0.25` letterboxes square-ish maps. Pre-existing, also on map pages.

### E. Print

26. **The checklist's own `<h2>` prints near-white on white** — roughly 1.1:1 measured, i.e. not
    there. Pre-existing site-wide in `Guide.css`'s print block, but `6516a89`'s entire purpose is a
    checklist a reader ticks on paper, so an invisible heading over it matters more now than it did
    when nothing depended on it. Cheap, and it is the first thing to fix in this group.
27. **Encounter tables, trainer cards and the rail still print on their dark panel backgrounds**, so
    the bottom third of a printed chapter is ink-heavy. It predates this phase and lives in the
    design system's own print block, which is why it did not block — but it is **more noticeable
    now, not less, precisely because the maps print properly** (decision 36 gave the viewers a
    white background and a black border on all 1,195 map pages). The maps stopped being the
    ink-heavy thing on the page, so these became it.
28. Fold print-expansion is verified in Chromium only; older engines print folds collapsed. The
    in-code comment overstates coverage — the real floor is Chromium ≥128 / Firefox ≥139 /
    Safari ≥18.4.
29. The map image prefetch costs 222 KB (this chapter's six distinct maps) for a reader who opens
    a chapter and leaves immediately.

### F. Tooling robustness

30. **A _local_ re-pin without re-running extraction makes the features page cite the old commit
    while serving new content.** The page renders `game/FEATURES.md` live from the submodule but
    takes its "as of" commit from generated data, so moving the gitlink and rebuilding without
    running `tools/extract/All.py` produces a page that contradicts itself. **CI is safe** — it
    extracts before it builds — so this is a local-workflow trap, and the re-pin is exactly when
    someone will hit it. Run the full gate in order, per the verification section. **Confirmed live
    at the 2026-07-27 re-pin:** `/features/` is byte-identical apart from the 40-character SHA it
    cites, so skipping extraction would have published new content under the old commit. Still
    open — the trap is unchanged, it has just now been demonstrated rather than predicted.
31. `Extract.py` treats any unrecognised flag as the output directory — `Extract.py --dry-run`
    creates `./--dry-run/`.
32. `Extract.py`'s item-count assertion fires _after_ every item PNG is written, so a failure leaves
    partial output.
33. `Extract.py`'s `a % 16 if a.max() > 15` would silently fold a genuine 8bpp source rather than
    reject it.
34. `Extract.py`'s "no `.frontPic`/`.iconSprite`" error also fires on a missing `.iconPalIndex` and
    does not say so.
35. CI runs `Extract.py` without `--check-determinism` (matching the `Render.py` precedent), so
    sprite non-determinism would ship rather than fail.
36. `Links.mjs` exits on the reachability failure _before_ the manifest orphan check, so one
    unlinked page suppresses the orphan report for that run.
37. `Shot.mjs` reads `scrollHeight` once before the walk, so a page that grows while scrolling is
    under-captured.
38. `Sprites.ts` reads its directory once at module load, so `astro dev` misses sprites that appear
    mid-session. Nothing mechanically prevents it being pulled into a client bundle either — the
    guard is a comment plus a `dist/` grep.
39. `baseForm()` hard-stops the whole build if a future re-pin yields 0 or 2 base forms for a dex
    number. Correct, but loud; and per-species sprite extraction has the same no-slack property —
    one enabled species missing `.frontPic`/`.iconSprite`/`.iconPalIndex` fails the entire run.
    **Both survived their first real re-pin** (`9ee61fbd` → `2b1fba48`, 2026-07-27) — but that
    re-pin touched no species data, so this is one clean run rather than evidence the risk is gone.
40. `Species.py`'s `form_tables()` is a third `cpp` invocation, on a header `species_info.h` does not
    include, and omits `metaprogram.h` — "same flags" overstates the parity.
41. `src/Species.ts` degrades to `"dex undefined: 0 base forms among "` on an empty forms array.
    Unreachable from both call sites today.

### G. Housekeeping

42. **Correct the comment at `walkthrough/[slug].astro:85`.** It says nothing else on these pages
    emits a checkbox. **In the DOM that is false** — 36 exist once the maps mount, 30 of them
    Leaflet layer controls. It is harmless today because the detection it justifies runs at
    **build time on compiled markdown**, where the claim _is_ true, and the client script scopes to
    `input[data-check]`. But it reads as a statement about the page, and the next person to write a
    DOM-side selector on its authority will get 36 matches. Fix the comment to say _build-time
    markdown_, not _the page_.
43. There is **no `.prettierrc`**, so formatting `.astro` files needs an explicit
    `--plugin=prettier-plugin-astro`. Adding one would remove a recurring papercut.
44. `docs/SCHEMAS.md` fails `prettier --check` for pre-existing reasons unrelated to any recent
    change. Left alone deliberately; fix it as its own commit or not at all.
45. `--edge`, `--spoil-bg` and `--spoil-bg-h`, referenced by `Spoiler.astro`, are undefined in
    `Guide.css`. Pre-existing; the component renders on fallbacks.
46. `localStorage.getItem` is called outside a `try`/`catch` in `Spoiler.astro` and `Base.astro`
    (pre-existing), and `pw:hide-all` clears the site-wide revealed set rather than only the gates
    in the current DOM. Relatedly, while `pw-reveal-all == "1"` an individual close does not survive
    a reload and nothing in the UI explains why — spec-compliant, but confusing.

### H. Found by review, recorded rather than fixed

**The checklist work is closed** (decision 51). Everything below was found by the round-five and
round-six reviews and is deliberately not fixed: 47–50 all need hand-written raw HTML inside a
chapter, and `content/` has none — every chapter is markdown, and the compiler cannot produce any
of these shapes. 51 and 52 are pre-existing and unrelated in cause; they are filed here because
this is where they were found. **A shape nine goes in this list and nowhere else.**

47–50 are here so that whoever first pastes raw HTML into a chapter has a chance of connecting the
symptom to the cause, because the symptom is always the same one: **the boxes render and they do
nothing, or they tick the wrong line.**

47. **`closeOf` assumes every `<li>` is explicitly closed.** It finds an item's own `</li>` by
    counting `<li` opens against `</li` closes, which is exact for anything remark emits. HTML
    itself does not require the close — `<ul><li>a<li>b</ul>` is legal and common in hand-written
    markup — and against that the count never returns to zero at the right place, so the item's
    extent is wrong and the label swallows its sibling. **Trigger: a raw `<ul>`/`<ol>` written by
    hand into a chapter, inside or around a task list, with implicit `</li>`.** The fixture's
    `no label swallowed a sibling item` assertion would catch it if such a shape were in the
    table; it is not, because markdown cannot produce one.
48. **`text()` strips tags with `/<[^>]+>/g`, which stops at the first `>`.** An attribute
    containing an unescaped `>` — `<a title="Route 2 > Viridian Forest">` — ends the match early,
    so the attribute's tail leaks into the hashed sentence and the item's key is not the sentence
    a reader sees. remark escapes `>` in everything it generates; raw HTML passed through is
    copied verbatim. **Trigger: raw inline HTML in a checklist item whose attribute value
    contains a bare `>`.** The tick still works, but the key is derived from text nobody can see,
    so the same visible sentence written normally elsewhere keys differently.

49. **Shape eight: a phrasing CONTAINER holding non-phrasing children is cut inside the
    container.** Decision 49 ends a checklist sentence at the first non-phrasing tag, which is
    right for a bare block — a `<div>` or an `<hr>` lands outside the `<label>` and the key
    survives. But the scan has no notion of nesting, so it stops at the container's first
    non-phrasing **child**, not at the container: the open tag stays in the label, the children
    and the close tag go to the tail, and the element straddles `</label>`.

    ```
    - [ ] Beat <svg><circle/></svg> Brock today
    →  <span class="lbl">Beat <svg></span></label><circle></circle></svg> Brock today</li>
       key 1wl5u5h, which is keyOf("Beat") — not hvwjpv
    ```

    "Brock today" is outside the label: unclickable and unhashed. **Seven containers do it** —
    `<svg><circle>`, `<math><mi>`, `<select><option>`, `<video><source>`, `<map><area>`,
    `<template><div>`, and a `<span>` wrapping any block. This is shape six's harm reached
    through a container instead of a bare block, so the inverted direction decision 49 relies on
    does **not** cover it — `src/Checklist.ts` now says so in place of the claim that it did.
    The honest repair is nesting awareness, which is a parser, and that is far more than this
    earns while no chapter contains raw HTML.

50. **`tools/qa/Keys.mjs:63` truncates a label containing a nested `<span>`.** The capture is
    non-greedy to the first `</span>`, so `<span class="lbl">Beat <span>x</span> Brock</span>`
    records "Beat" as the sentence. The guard then protects less than it reports: the recorded
    text is not the sentence, so a later rekey of the real sentence would be classed as an author
    edit rather than a rekey. Same raw-HTML-only family as 47–49 — markdown emits no nested span
    inside a task item today.
51. **Sideways scroll at 320px and 360px once a chapter's reference folds are opened.**
    `scrollWidth` 384 against a 320 viewport, on any of the first three folds. Cause: chapter-body
    tables get no `.scroll-x` wrapper — **5 tables, 0 wrappers** in the built chapter — while
    `src/Features.ts:226` wraps its own. **Pre-existing**, not introduced by the checklist work:
    the chapter HTML is byte-identical to `fa7af2e` and no CSS changed. **Diagnosed, not
    verified** — the fix (give the chapter body the same wrapper the features page uses) was
    reasoned about but never built or measured, so treat the cause as likely rather than proven.
    Decision 44 committed to phone widths being supported rather than best-effort, which is what
    makes this worth doing.
52. **A trailing parenthetical containing a digit costs a section its tier.** `## Roadmap
(Gen 8)` lands in `extra` instead of `build`. `PAREN_RE` excludes digits by design (decision
    50 — so `(Gen 8)`, `(v1.3)` and `(2 of 3)` are never mistaken for status markers), but the
    tier lookup's strip-and-retry at `src/Features.ts:316` uses the same pattern, so it cannot
    rescue the heading either. Pre-existing and cosmetic under decision 41 — wrong group, still
    published — and the before column of decision 50's matrix shows `extra` on both sides.

**Two near misses in decision 50's status vocabulary, noted rather than acted on:** `(partial)`
and `(pending)` are not in `MARKERS`, so a re-pin using either publishes it as prose with a build
notice rather than folding it red. Both are genuinely ambiguous — `(partial)` could describe
coverage as easily as completeness — which is why neither was added. If a re-pin ever uses one as
a status, the notice will name it and adding the word is a one-line edit.

---

## M5's shape — the answers already given

The previous handoff's most useful property was that it stated the decisions already made, so they
were not relitigated. These were asked as open questions and **have since been answered by the
reader**. Treat them as settled; `DECISIONS.md` 45 and 46 are the record.

| Question                         | Answer                                                                         |
| -------------------------------- | ------------------------------------------------------------------------------ |
| How are chapters sourced?        | **From source. Nobody is playing the game.** See the content rule below.       |
| How big is a chapter?            | **One badge segment**, split when it gets big — chapter 1's granularity, kept. |
| Does Sevii get chapters?         | **Yes, full chapters.** Not atlas-only.                                        |
| How many chapters total?         | **45–58**, Sevii included.                                                     |
| Boss pages: what shape?          | `sections:` for the puzzle + a generated `TrainerCard` for the party.          |
| Do boss pages change the schema? | **No.** The frozen contract carries all 24 plus the leagues unchanged.         |
| When does the re-pin happen?     | **After the current work, as its own task.**                                   |

**The content rule that falls out of source-derivation, and it binds every chapter:** nothing
derivable from source supports "this fight is tough", "you will want to grind here", or "this part
drags". That is the natural voice of a strategy guide and it must not appear, because the guide
cannot stand behind it. Chapter 1 is clean on this — keep it that way. What _is_ derivable — levels,
parties, encounter rates, what you will miss — is what the guide says instead.

**Still genuinely open, and worth deciding early rather than at chapter 30:**

1. **Does `order:` interleave the regions, or run per region?** Currently a flat integer sorted
   globally inside a fixed Kanto/Johto/Hoenn grouping. Three regions playable in any order have no
   single true sequence. _Default: number per region, keep the grouping._
2. ~~**Do the 22 hijacked trainer slots get boss pages?**~~ **Moot — the re-pin happened and there
   are no hijacked slots.** All 22 are restored upstream, so the 8 that carried a Leader class are
   now ordinary route trainers and a `class`-keyed boss-page generator produces 24, not 65. The
   question does not need answering; the standing advice to filter `anomaly` in any new generator
   stands anyway, as a tripwire rather than as a live necessity.
3. **Are boss parties spoiler-gated?** Decision 37 prints spoilers revealed, and a boss page is
   mostly spoiler by nature. _Default: ungated on boss pages, gated in Insider Tips as today._
4. **Do all chapters get all three files?** At 45–58 chapters plus 24 boss pages that is a lot of
   files, and many will have no engine detail worth a Technical page. Absence is already legal — a
   missing companion is fine, a **mistyped** one throws. _Default: chapter always, Tips and
   Technical only where there is something to say._
5. **Is Sevii completable end to end?** Audit Q5, still open — and source-derivation means nobody
   is playing to find out. It **is** answerable from source, by tracing the script chain and
   decoding reachability, which is exactly how game issue #39 turned out to be unreachable data.
   **Make that the first task of Sevii**, not an assumption baked into eight chapters.

## The re-pin — ✅ DONE, 2026-07-27

Moved `9ee61fbd` → **`2b1fba48`**. All five upstream game bugs are fixed and closed (`0f5b2595`
covers #36–#39, `6ee98c77` covers #40) and the game repo's README now links to this site. Deferred
group A was closed first (decisions 47–51). Full record in `DECISIONS.md` 52; what actually moved:

|                              |           before |             after |
| ---------------------------- | ---------------: | ----------------: |
| `anomaly`-flagged slots      |               22 |             **0** |
| map pages captioning one     | 12 (22 captions) |             **0** |
| gym leaders                  |               24 |            **24** |
| unreachable species          |                3 |             **1** |
| off-image markers            |               19 |            **17** |
| Kanto chapter pins in bounds |            37/37 |         **37/37** |
| pages · internal links       |    1633 · 23 880 | 1633 · **23 886** |

Determinism holds at the new pin, the six frozen checklist keys are unchanged, and `Checklist.mjs`
still passes 21 shapes / 203 assertions.

**Three things worth carrying forward, because none of them was predicted from the diff:**

- **`hard` (42) and `frlg_hoenn_johto_placements` (2) did not move**, despite `trainers.party`
  changing by 1,191 lines. Both were expected to. Re-measuring beat reasoning about the diff, which
  is decision 11 earning its keep again.
- **Placing a species is not additive.** Giving Lunatone and Zangoose slots took slots from Solrock
  and Seviper — encounter tables are fixed-width. Exactly four species records changed and two of
  them are species nobody touched. Check what a placement pushed out, not just what it added.
- **`/features/` moved even though `FEATURES.md` is byte-identical** — by exactly the commit SHA it
  cites, proven by substituting the old SHA back and recovering the previous MD5. That is deferred
  30 working, not failing, and only because extraction ran before the build.

## Still open, needs the reader

- **M5** — 45–58 walkthrough chapters across three regions plus Sevii, 24 boss pages, the three
  leagues, Red at Mt. Silver, the 15-trainer World Championship (audit Q12 deferred these here).
  `content/kanto/PalletToViridian.md` is the template and the `sections:` schema is the contract.
  Shape and sourcing are settled; the five items above are what is not.
- **M6** — Pagefind search, mGBA screenshot automation, print/PDF export, version diff page. Note
  that print now works well enough to be worth building on rather than around (decisions 35–38).
- **`DATA-AUDIT.md §10`** — Q11 (Johto has only 3 hidden items), Q13 (quest system), Q14 (config
  ternaries), Q20 open items. **Q18 is now 17 off-image markers, not 19** — the four
  out-of-bounds events it named are exactly the ones game issue #38 removed, so what remains is a
  different class (inside the addressable border, off the rendered image) and the suppress / clamp
  / leave decision still stands. **Q22 is closed** — there was no back door. **Q5 (is Sevii
  completable end to end?) is now on M5's critical path** — see the re-pin and M5 sections above.
- ~~**The five game bugs are closed** and the re-pin will change real content.~~ **Done** — see
  "The re-pin" above. Nothing left to chase here.
- **A form column for the species "Where to get it" table.** Decision 33 refused to union regional
  forms onto the base page because the table cannot say which form a row yields. Adding that column
  makes the union honest and unlocks ~20 thin pages. Content task, not a rendering one.
