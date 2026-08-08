# Next session: M5 — the remaining chapters

Read this first, then `DECISIONS.md` (23–46 are the readability phase, 47–56 the re-pin and the
fixes around it, **57–61 close every M5 prerequisite**, 62–67 close groups C and D), then
`DATA-AUDIT.md §10`.

**Deferred group B is closed as of 2026-08-07 and the gate is green. Chapter two is unblocked** —
write it against the contract, and run `node tools/qa/Chapters.mjs` before you believe it.

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
  remain **frozen**; 23–46 record what this phase and the post-ship work changed around them, and
  57–61 close deferred group B without touching the templates.
- **Toolchain:** Python 3.12+ with `pillow` and `numpy`, Node 22+ (the QA scripts import `.ts`
  directly and rely on type stripping). Builds on macOS and on Ubuntu, from one code path —
  see decision 57 and the README's build section.
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

### And what landed on 2026-08-07 — all of group B

**Deferred group B is closed. There is nothing left to do before chapter two.** Decisions 57–61.

- **The `sections:` contract has a checker**, `tools/qa/Chapters.mjs`, wired into CI after the
  build. It drives `stepsOf` from `src/Steps.ts` rather than re-implementing it, so it reports the
  grouping the page will draw. 18 fixtures prove every rule fires and the healthy one is silent.
  Closes B3, B5 and B7.
- **The homepage stops claiming Kanto is the only region with a chapter** the moment it is not.
  Closes B6.
- **The repo builds on macOS.** Three extractors were failing on a correct command line — see the
  gotchas — and the fix is proved by determinism: all eight generated files rebuild byte-identical
  to the ones CI produced on Ubuntu. Decision 57.
- **The footer carries both repos and the author's credit.** Decision 61.
- **Documentation drift, fixed.** `npm run validate` pointed at `tools/validate/Check.py`, which
  does not exist and never has. The README still said "Status: M0 — Audit", four milestones behind,
  described `tools/validate/` as generating a `docs/COMPLETENESS.md` that is not in the tree, and
  called the submodule pin a tag when decision 52 moved it to a bare commit. All corrected, and the
  README now carries the build instructions this bring-up had to reconstruct.

### And what landed on 2026-08-08 — groups C and D

**Group D is closed except item 25, and group C is closed.** Decisions 62–67.

- **The 37 step pins are out of the tab order and named.** A keyboard user was tabbing 37 controls
  announced "3, button" to reach steps that are the next thing in the document anyway. Note the
  entry's own suggested fix — `L.marker`'s `alt` — **does not work on a `divIcon`** and would have
  shipped as a no-op.
- **A chapter read without JavaScript shows nine maps instead of nine voids**, and that put every
  map PNG into the HTML, so `Links.mjs` checks the rendered images for the first time: 23,886 →
  **25,090** internal links, +1,204 = 1,195 map pages + 9 sections.
- **`bindTooltip` stopped going through `innerHTML`**, so a step sentence containing `<` renders.
- **The `/maps` filter answers "route1" with Route 1 first**, without hiding route10 — and it
  reorders the DOM rather than using CSS `order`, which would have moved the paint and left the tab
  sequence behind it.
- **Revealed spoiler text is no longer dimmed**, and a trainer's name is printed once.
- **The homepage's Hub Pass promise carries its real qualifier.**
- **Two group C items were already fixed and the list was stale** (C13, C14) — struck with the
  evidence. Third time a deferred entry has pointed at finished work or a fix that does not work.

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
python3 tools/porymap/Render.py                    # 966 layouts -> 1195 entries, ~22s, gitignored
python3 tools/sprites/Extract.py                   # 1,978 sprite PNGs, gitignored
python3 tools/validate/CheckCoords.py              # coordinate invariants
node tools/qa/Checklist.mjs                        # 21 markdown shapes, 203 assertions
./node_modules/.bin/astro build                    # NOT `npx astro build` -- see gotchas
npx pagefind                                       # search index over dist/, ~0.5s
node tools/qa/Chapters.mjs                         # the sections: contract, + 18 fixtures
node tools/qa/Links.mjs                            # 0 broken, 0 orphans, 0 unreachable
node tools/qa/Keys.mjs                             # the six frozen checklist keys
```

Green at `2b1fba48` on 2026-08-08: **1,634 pages · 26,735 internal links · 0 broken · 0 orphans ·
0 unreachable**, determinism holds across all 8 files, 17 off-image markers.

The link count moved 23,886 → 25,090 on 2026-08-08 and the **+1,204 is 1,195 map pages plus the
chapter's 9 sections**: the no-JS still (D20) puts each map PNG in the HTML as an `<img>`, so the
rendered map images are link-checked for the first time. Leaflet fetches them at runtime, where
`Links.mjs` has never been able to see them.

Then the search page moved it 25,090 → 26,735, and the **+1,645 is 1,634 + 11**: the `Search` nav
link on every page including the new one, plus the search page's own eleven — its stylesheet, the
banner mark, the five other nav links and the four no-JS fallbacks. `npx pagefind` itself adds
neither: it writes only `dist/pagefind/`, 1,675 files of JS, WebAssembly and binary index chunks,
none of them HTML and none of them referenced from any `href` or `src`. Note the collision with
the sprites gotcha further down, which is also about ~1,645 links: that one is a count **short** by
1,645 and means you built before extracting sprites, this one is a count **up** by 1,645 and means
the search page landed.

`tools/qa/Chapters.mjs` is new — decisions 58 and 59, and it closes deferred B3, B5 and B7. It
runs AFTER the build because half of what it checks is a property of the emitted HTML. It also
carries its own fixture table: 18 constructed chapters, one per rule, asserted in the same
invocation, so a rule that has stopped firing fails there rather than in your chapter.

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

### Discovered bringing the repo up on macOS

- **`cpp` is not the preprocessor on macOS, and its first error names the wrong file.**
  `/usr/bin/cpp` runs clang in _traditional_ mode where `//` is not a comment, so the game's
  `#define P_MEGA_EVOLUTIONS TRUE // If TRUE, …` carries the comment into the macro body and every
  `#if` over it dies. The **loudest** errors are then `#else after #else` and `#endif without #if`
  in `include/constants/global.h` — a header that is perfectly well formed, and not the file with
  the problem. The extractors use `cc -E` with joined include flags (`-Iinclude`, never
  `-I include`, which Apple's driver reads as a linker input and then reports "no input files").
  Decision 57.
- **The build succeeds with an empty `public/sprites/` and quietly ships a smaller site.**
  `src/Sprites.ts` asks the filesystem whether each sprite exists and falls back to a text-only
  layout when it does not — deliberately, so a fresh checkout still builds. The cost is that
  running the sprite extractor after the build, or not at all, produces **22,241 internal links
  instead of 23,886** with a completely green gate. If your link count is short by ~1,645, you
  built before extracting sprites. Order matters and this is the reason.
- **Homebrew Python is PEP 668 externally managed**, so `pip install pillow numpy` fails. Use a
  venv; `.venv/` is already gitignored. Nothing else about the pipeline changes.
- The repo now lives at `~/Github/PKMN-World-Guide` on macOS. The old warning about never auditing
  against the stale `/mnt/c` checkout belongs to the WSL box and is kept for it.

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

### B. M5 prerequisites — ✅ ALL CLOSED, 2026-08-07

Closed by decisions 57–61. Retained below as the record of what was wrong, since 45–58 chapters
inherit the fixed code and the reasoning is still the reasoning. **The checker is
`tools/qa/Chapters.mjs`** — run it, and read its failure messages rather than guessing.

3. ~~**Nothing validates `choice_group`.**~~ **Fixed**, decision 58. The renderer degraded silently
   on genuine authoring errors (a group of one, `choice_group` without `choice`, a mismatched
   `choice` value inside a run). All of those are errors now, plus an empty `choice_group`, the
   forbidden `choice: false`, a malformed `at:` that silently drops the pin, and a step with no
   text. An unrecognised `choice` value stays a WARNING, because that is the contract's forward
   compatibility working rather than failing.

   It went to `tools/qa/` and not `tools/validate/` as this entry said, and that is the whole
   design: it imports `stepsOf` from `src/Steps.ts` and reads its runs off the renderer's own
   maximal-run pass, so it reports what the page will draw. A Python copy would be a second
   implementation of the thing under test — see `slugOf()` and the 486 phantom orphans.
4. **A body section folds if it contains any `<li>`, including "where you go next".** See the
   authoring constraint above. The template's own comment says that section must never sit behind a
   click, and it holds today only because this chapter's happens to be prose-only. Two bullet points
   would collapse it silently. Either teach the renderer to exempt that heading, or write the rule
   into the schema contract on the Technical page so 24 boss pages inherit it deliberately.
   Degrades to a click, not to wrong information — which is why it is not in group A.
5. ~~**Section `id`s are unvalidated.**~~ **Fixed**, decision 58. `walkthrough/[slug].astro` took the
   YAML `id` straight into a DOM id and the viewer's `steps` key, so two sections sharing an id
   silently handed the second viewer the **first** section's pins, plus duplicate DOM ids. A
   missing id, a duplicate id and an id that is not lowercase kebab-case are all errors now — the
   last because the id is also a `querySelector` argument and a URL fragment, and a space or a dot
   breaks one of those without breaking the others. `title` and `text` are checked alongside it,
   and a `map:` that is not in the manifest warns.
6. ~~**`index.astro` hard-codes "so far the only one with a written chapter".**~~ **Fixed**,
   decision 60. Both halves now come off `groups`, which is already filtered to regions that have a
   chapter and is in play order. Proved by construction: a temporary Johto chapter drops the clause
   and leaves "Pick Kanto first — it is where this guide's walkthrough starts", and removing it
   restores the sentence.
7. ~~**`data-step` can diverge from the badge.**~~ **Fixed**, decision 59 — as a check over the
   BUILT HTML, since that is the only place the divergence exists. If a step renders without
   `data-step` the CSS badge falls back to `counter(step)` while the pin script's `li[data-step]`
   query skips it, and the badges and the pins start numbering two different lists. Both branches
   were proved by mutating a built page and restoring it byte-identical.
8. ~~**Steps render above the markdown body and the body cannot be split.**~~ **Answered**,
   decision 55 — as a convention rather than a renderer feature. Everything in the body follows
   every step, so **an instruction belongs in `sections:` as a step** and the body opens with
   scene-setting and never tells the reader to do anything. Written into the schema contract on
   the Technical page, because there is nothing here for code to enforce that would not first have
   to guess which sentences are instructions.
9. ~~**The step legend renders whenever `steps` is set**~~ — **fixed**, decision 56 and `9b15116`.
   Only the caller knows whether a section draws pins, so the caller passes `null`.

**Item 4 is the one that is handled rather than closed.** Nothing in code can tell a handoff from
reference material by reading it, so the renderer names the section it TREATED as the handoff on
every build (decision 54) and the convention is written into the contract. Read that line in the
build output when you write a chapter; it is the only warning you get.

### C. Correctness, cheap

10. ~~The species "Where to get it" count overstates~~ — **fixed**, `190e1cd`. `sourceCount` now
    counts what the fold renders: a wild slot and an `other` entry are one row each, and "Evolves
    from X" is one sentence however many records back it. Measured across all 430 built species
    pages, **26 disagreed before, 0 after**.

    The two figures this was recorded under — 26 and 228 — were the same data under two readings
    of what a reader counts. 228 counts the evolution sentence as **nothing**: 202 pages hold one
    evolution record, 25 hold two, 1 holds three. 26 counts it as **one thing**, so only the pages
    whose sentence is backed by more than one record can disagree: 25 by one and Milotic by two.
    The second reading is the one that was fixed, because the first would print "(0)" over a
    visible sentence on 202 pages. Every one of the 26 is a trade evolution's item twin naming the
    **same** parent twice — "Evolves from Kadabra (Trade), Kadabra (Use Linking Cord)" — and no
    page anywhere names two distinct parents, so nothing was lost by counting the sentence once.

11. ~~Two checklist items with identical text share a key~~ — **fixed**, decision 48. Later copies
    are suffixed `~2`, `~3`; deleting a duplicate still shifts survivors, and the build warns.
12. ~~`- [x]` in source silently loses its pre-checked state~~ — **fixed**, decision 48. It is a
    build warning naming file and line; it will never pre-tick.
13. ~~Encounter tables render in source order, so DexNav can sit above Tall Grass.~~ **This was
    already fixed and the entry was stale.** `byMethod` in `maps/[slug].astro` sorts on the key
    order of `METHOD_LABEL` — land, water, rock_smash, fishing, hidden — and `byRod` does the same
    one level down for old/good/super. Route 10 renders Tall grass, Surfing, Fishing (Old, Good,
    Super), DexNav. The code even carries the rationale: "the order a player meets these".
14. ~~`wildSpecies` counts include `species_enabled === false` slots.~~ **Moot — that count no
    longer exists.** Decision 39 took the number off the "Wild Pokémon" heading entirely, because
    it counted distinct species while its own child folds counted rows and the two disagreed on
    330 of 331 pages. `species_enabled` now only gates per-slot rendering, and this pin has **0
    disabled slots**. There is nothing left to miscount.
15. ~~The homepage's "warps you back whenever you want" drops a real qualifier.~~ **Fixed**,
    decision 66. `CannotUseHubReturnHere()` blocks the Hub Pass in the Safari Zone, the Bug
    Contest, link/union rooms and Frontier/Trainer Hill runs. None is reachable on turn one, which
    is why it sat here — but a guide that promises a reader they can always leave has told them
    something false at the one moment it matters.
16. **Left as it is, deliberately.** 332 extracted sprites (166 front + 166 icon, ~0.39 MiB) are
    referenced by nothing — 596 emitted, 430 used. That is headroom for alt-form art, so a checker
    would report 332 problems on every build and be right about none of them. Revisit only if the
    figure grows for a reason nobody can name.

### D. Accessibility and UX — ✅ CLOSED except 25, 2026-08-08

Two items that were here — the 320px sideways scroll and the layer control covering a small map —
are **fixed**, in `0e4053d` and `d1c4845`. See decision 44. Everything else in this group is now
closed by decisions 62–65, except **25**, which was left on purpose; **19** was never a defect.
Every fix below was verified in a real browser, and the assertions are in the commits.

17. ~~**The 37 step pins are keyboard traps in miniature.**~~ **Fixed**, decision 62 — though not
    the way this entry said. **`L.marker`'s `alt` does nothing here:** Leaflet only assigns `alt`
    when the icon is an `<img>`, and these are `divIcon`s, so the suggested fix would have shipped
    and changed nothing. The pins now take `keyboard: false` and carry `role="img"` with an
    `aria-label` of "Step N: <sentence>", set on `add` because `getElement()` is null until the
    marker is on the map. Measured: 37 pins, **0** with `tabindex`, **0** with `role="button"`,
    **37/37** named.

    The pins came OUT of the tab order rather than being fixed inside it, because each one only
    scrolls to a step that is the next thing in the document anyway. The `<ol>` below the map
    carries the same numeral and the same sentence in reading order, so 37 tab stops bought a
    keyboard user nothing and cost them 37 stops.
18. ~~Overlapping 26px pin icons on the Viridian sequence~~ — **fixed**, `0ab304a`, and it did
    **not** need a plugin. Pairwise relaxation in `MapViewer.astro` pushes crowded pins apart to
    20px centre to centre — where a numeral clears its neighbour's disc — and re-runs on zoom
    because how close two tiles look is a property of the zoom. Measured at 390px: 8/9 and 13/14
    both **7.0px → 20.0px** (11px was the earlier figure; 7.0px is one tile at the zoom that fits
    the city on a phone), every other pair unchanged including the three starter balls at 23.0px;
    enumerating all 119 pairs across the chapter's nine viewers, pairs under 20px **2 → 0**.

    **What the cap actually guarantees, because the difference matters to whoever tunes it
    next:** it bounds **displacement** to one tile, not final position. A pin nudged 0.97 of a
    tile from its tile's centre lands about 0.47 of a tile past that tile's edge, so at fitted
    zoom pins 8, 9, 13 and 14 sit on the tile **next to** the one their step names — adjacent to
    it, not on it. That is 7px on a phone and zooming in restores exactness, which is why it is
    the right trade against a pin nobody can see; but raise `SEP` or the cap while believing the
    pin stays on its own tile and you will ship pins two tiles out. Zoom far enough out and the
    cap binds and the pins stay touching, which is the honest answer rather than a wrong one.

19. A measurement, not a defect: the chapter is **11,948px** tall with the script running, and the
    dead space below the last step is **1,345px**. Left as the record it is.
20. ~~With JS off, the chapter reserves nine 780×480 boxes — ~4,300px of nothing.~~ **Fixed**,
    decision 63. Each viewer now carries a `<noscript>` still of the same PNG Leaflet would have
    tiled in, and one rule in `Base.astro` collapses the empty box. Verified with JavaScript
    actually disabled: **9 stills, the empty `.pw-viewer` box gone entirely, first still 780×562**.
    The chapter gets TALLER without the script — 13,417px against 11,948 — and that is the point:
    ~4,300px of nothing became ~5,000px of maps.
21. ~~`bindTooltip(string)` goes through `innerHTML`~~ — **fixed**, decision 62. It takes an element
    with `textContent` set, so the invariant the comment twelve lines above asserts is now true of
    the tooltip as well as the numeral. Proved by putting `<b>odd</b>` into a step's text before
    its viewer mounted: the tooltip reads it back as literal characters and its `innerHTML` holds
    no `<b>`.
22. ~~The `/maps` filter is a plain substring~~ — **fixed**, decision 64. The substring MATCH is
    unchanged, because route10 does contain "route1" and hiding it would be worse; the ORDER now
    carries the precision — exact name or slug, then prefix, then the rest, each rank keeping its
    alphabetical run. "route1" still returns 101 hits and now opens with Route 1. Reordered in the
    DOM and not with CSS `order`, which moves the paint without moving the tab sequence and would
    have been this list's own version of the bug it fixes.
23. ~~`opacity: 0.7` on an open `.peek` dims the label text~~ — **fixed**, decision 65. The
    dimming moved to the border alone via `color-mix`, with the flat accent left underneath as the
    fallback. The revealed text — the thing the reader pressed the button to read — is back to
    full contrast.
24. ~~Trainer fold summaries repeat the name already in `TrainerCard`'s header.~~ **Fixed**,
    decision 65. `TrainerCard` takes `showName`, default true so M5's 24 standalone boss pages
    still say whose party it is, and the map page passes false because its fold summary already
    said.
25. **Still open, deliberately.** `fitBounds` + `zoomSnap 0.25` letterboxes square-ish maps.
    Pre-existing and not a regression, it affects map pages as well as chapters, and it is a
    geometry change to the viewer rather than a contained fix — so it was left rather than
    bundled into an accessibility pass.

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
round-six reviews. 47–50 are deliberately not fixed: they all need hand-written raw HTML inside a
chapter, and `content/` has none — every chapter is markdown, and the compiler cannot produce any
of these shapes. 51 and 52 are pre-existing and unrelated in cause; they are filed here because
this is where they were found, and **51 has since been fixed**. **A shape nine goes in this list
and nowhere else.**

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
51. ~~Sideways scroll at 320px and 360px once a chapter's reference folds are opened.~~ —
    **fixed**, `96096b9`. The recorded diagnosis — chapter-body tables get no `.scroll-x` wrapper —
    was **half of it, and the smaller half**. Wrapping all five tables in the live DOM and
    re-measuring moved `scrollWidth` not at all: still 384 against 320.

    The whole of the reported 384 was the grid. `.split`'s two-column track is
    `minmax(0, 1fr) 20rem`, but the `max-width: 900px` override dropped to a bare `1fr`, and a
    bare `1fr` is floored at its **min-content** — so the column measured 360px inside a 272px
    container and the page grew to fit it. The tables were real but second: with the floor gone
    the page still read 370, on the two tables whose `white-space: nowrap` headers cannot shrink.
    Both are fixed and `scrollTables` moved to `src/Html.ts` so the chapter and the features page
    share one implementation.

    **The lesson worth keeping is the method, not the fix**: the diagnosis named a true fact
    (5 tables, 0 wrappers) that was not the cause, and only testing it in the DOM before writing
    any code separated the two. Decision 44 committed to phone widths being supported rather than
    best-effort; the standard now holds at 320, 360, 390, 768 and 1280 with every fold opened, on
    the chapter, a map page and a species page.

52. **A trailing parenthetical containing a digit costs a section its tier.** `## Roadmap
(Gen 8)` lands in `extra` instead of `build`. `PAREN_RE` excludes digits by design (decision
    50 — so `(Gen 8)`, `(v1.3)` and `(2 of 3)` are never mistaken for status markers), but the
    tier lookup's strip-and-retry at `src/Features.ts:309` uses the same pattern, so it cannot
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
