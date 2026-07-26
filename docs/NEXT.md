# Next session: readability overhaul

Read this first, then `DECISIONS.md`, then `DATA-AUDIT.md §10`.

The generated half of the guide is finished and correct. **This phase is entirely about
making it readable.** The reader's verdict was: too much text, too hard to follow, maps
missing from the guide, reads like engineering notes rather than a guide.

Target reader: **a ten-year-old who wants to know what to do next.** If a sentence explains
how the game works internally, it does not belong on a walkthrough page.

---

## State as of this handoff

- **Live:** https://dev.jdayers.com/pkmn-world/ — CI deploys on every push to `main`
- **Repo:** https://github.com/evilchinesefood/PKMN-World-Guide (public), `main`, clean
- **Game pin:** submodule at `9ee61fbd` (`master`)
- 1,630 pages · 18,932 internal links · 0 broken · 0 orphans
- Extractor determinism holds across all 8 generated files
- Milestones M0, M1, M2, M3, M4 complete. M2 templates are **frozen** — changing them means
  re-checking every page (see `DECISIONS.md` 13-22).

Run everything with:

```
python3 tools/extract/All.py --check-determinism   # 8 JSON files, must be byte-stable
python3 tools/porymap/Render.py                    # 966 map PNGs, ~22s, gitignored
./node_modules/.bin/astro build                    # NOT `npx astro build` -- see gotchas
node tools/qa/Links.mjs                            # 0 broken, 0 orphans required
python3 tools/validate/CheckCoords.py              # coordinate invariants
```

---

## The eight changes, with the answers already given

### 1. Homepage becomes the guide
Chapter list in play order, preceded by a short "start here" orientation block (which region
to pick first, what the World Transit hub is). Everything else moves behind the top nav.

### 2. New `/maps` page
All 1,195 map links move off the homepage to their own page, reachable from the top nav
alongside Pokédex, Items and Gyms. Keep the existing region sections including Sevii.

### 3. Maps must appear INSIDE walkthrough chapters
Currently a chapter only links to its maps. The aerial map with its overlays is the whole
point of the genre and has to be inline, next to the steps that reference it. `MapViewer.astro`
already takes everything it needs; the chapter page has to render one per map it covers.
Consider showing the map for the area the current step group is about, rather than all 14 at
the top.

### 4. Numbered steps throughout
Every walkthrough chapter becomes numbered steps. `Guide.css` already has `ol.steps` with
the numbered-badge styling built and unused. One action per step. The numbers should
correspond to the numbered callouts on the aerial map — that pairing is the signature of the
printed guides this is modelled on, and `[slug].astro` for maps already assigns stable
callout numbers.

### 5. Cut the prose to roughly one third
`content/kanto/PalletToViridian.md` is 448 lines; target ~150. **Facts stay, engine
explanation goes.** Delete: code identifiers, file paths, tile coordinates, variable and flag
names, "this build's ALL_REGIONS path", byte counts. Keep: what to do, where to go, what you
will miss, what is worth catching.

Chosen option also asked for a separate **Technical notes** page so the verified engine detail
is not lost — it was all traced to source and is worth keeping, just not on the walkthrough.

### 6. Accordions — everything except the steps starts collapsed
The reader selected all four options, so: encounter and stat tables, source citations,
trainer parties, and in general everything that is not a numbered walkthrough step begins
closed behind a summary line (e.g. "Wild Pokémon (9)"). Use `<details>`/`<summary>` styled to
match `Guide.css`; do not build a JS accordion.

Note this interacts with change 5: source citations are being removed from walkthrough prose
entirely, so the accordion for them applies to the generated reference pages.

### 7. Insider Tips must re-collapse
`Spoiler.astro` is currently one-way — `open()` adds a class and there is no close path. Make
the reveal toggle both directions and persist the closed state too. The global "Reveal
everything" button already reloads to re-hide, which is a workaround, not a fix.

### 8. Sprites in the Pokédex and Items
- **Pokédex index rows:** small `icon.png` (32×32, party-menu icon)
- **Species pages:** `anim_front.png` (64×64 battle sprite)
- **Items index:** `graphics/items/icons/<name>.png` (630 available)

Assets live in the pinned submodule: `game/graphics/pokemon/<name>/{icon,anim_front}.png` and
`game/graphics/items/icons/*.png`. **They are 4bpp indexed GBA PNGs** — the same format the
map renderer already handles in `tools/porymap/Render.py` (`load_tiles`), so reuse that
approach rather than inventing a new one. Some need a companion `.pal` applied.

Write a `tools/sprites/Extract.py` that copies/converts only what is needed into
`public/sprites/`, and **gitignore the output** the same way `public/maps/*.png` is
(DECISIONS.md 13) — CI regenerates it. Add the step to `.github/workflows/Deploy.yml`.

Species-name → sprite-directory mapping is not guaranteed to be a simple lowercase of the
constant; verify it the way tileset paths were verified (parse the source binding) rather
than guessing. Expect form sprites to live in subdirectories.

---

## Suggested order

1. **Spoiler toggle fix** — smallest, unblocks testing everything else (~15 min)
2. **Sprite extractor** — independent of the prose work, and CI needs it early
3. **Homepage / `/maps` split + nav** — structural, do before rewriting content
4. **Accordions + numbered-step styling** — presentation layer
5. **Rewrite the Kanto chapter** — the hardest and most valuable; it re-freezes the content
   template for every future chapter
6. **Inline maps into the chapter** — depends on 3, 4 and 5 being settled

---

## Gotchas that will cost you an hour each

- **`npx astro build` hangs on this machine.** No output, no error. `./node_modules/.bin/astro build`
  works instantly. Not understood; do not spend time on it.
- **Piping a build through `| tail` buffers all output**, so a working build looks like a
  hang. Run it with `run_in_background` and poll the log.
- **Concurrent agents rewriting `data/generated/` cause phantom failures.** If Python and Node
  disagree about the same JSON file, something else is mid-write. Run the pipeline and the
  build in one command.
- **`Gates.py` runs LAST** and rewrites four files in place. Anything added to a record
  upstream survives, but only if `All.py` runs in order.
- **`rm` is blocked** in this harness. Use `git rm -f`, `git clean -ffdx <path>`, or `mv`.
- **`slugOf()` in `src/Names.ts` and the copy in `tools/qa/Links.mjs` must stay identical.**
  They drifted once and produced 486 phantom orphans.
- The 22 hijacked trainer slots (`anomaly: "frlg_boss_in_hoenn_slot"`) carry Leader and Elite
  Four classes on ordinary route ids. **Any filter on `class` must exclude `anomaly`** or you
  get 65 "gym leaders" instead of 24.

---

## Still open, needs the reader

- **M5** — walkthroughs for three regions, 24 boss pages, the three leagues, Red at Mt. Silver,
  the 15-trainer World Championship. The brief says this content is a byproduct of the 1.0
  playthrough. The rewritten Kanto chapter becomes its template.
- **M6** — Pagefind search, mGBA screenshot automation, print/PDF export, version diff page.
- **`DATA-AUDIT.md §10`** — Q11 (Johto has only 3 hidden items), Q13 (quest system), Q14
  (config ternaries), Q18 (4 out-of-bounds events), Q20/Q22 open items.
- **Five game bugs filed upstream:** PKMN-World issues #36, #37, #38, #39, #40. #36 (22
  trainer slots holding Kanto boss parties) is decided as publish-as-is; the rest are unanswered.
