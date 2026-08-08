# Decisions

Append-only. Every non-trivial choice gets a line and a one-line rationale. Newest last.

Entries marked **[brief §3 deviation]** change something the build brief listed as already decided.
Per the brief's working rules those were raised before acting, not substituted quietly.

---

## 2026-07-24 — M0

1. **Pinned the submodule to `v1.3.6`, a tag created today.** **[brief §3 deviation — approved]**
   The brief says pin to "the current tag, `v1.3.6`". No such tag existed: the repo carried only
   `v1.0-beta` plus four `backup/*` tags, while `README.md` and `CHANGELOG.md` both named v1.3.6.
   The version was released in prose but never tagged. Boundary identified as commit
   `87a66e89` ("docs: polish README + FEATURES for public release", 2026-07-13) — at that commit
   `README.md` reads `**v1.3.6**` and the top `CHANGELOG.md` section is `## v1.3.6 — 2026-07-13`
   with nothing unreleased above it. Tagged there as an annotated tag.

2. **The tag was created through the GitHub REST API, not `git push`.**
   `git push` from the WSL `/mnt/c` checkout hangs past three minutes on this host; `gh api` returns
   in under a second. Tag object `64331bad`, ref `refs/tags/v1.3.6`. Same result, different
   transport. This also applies to any future automation that has to write to the game repo.

3. **`v1.3.6` is ~30 commits behind `master`.** Consequence of decision 1, recorded so it is not
   rediscovered later. Content merged after the pin — Orange Islands, the Jessie & James region
   ambushes, the World Championship Dome entry, save format v7 — is **out of scope for the guide at
   this pin** and will appear only when the pin advances. See open question Q1 in `DATA-AUDIT.md`.

4. **Deploy target is `dev.jdayers.com/pkmn-world`, not GitHub Pages.** **[brief §3 deviation —
   user directed]** Brief decision 2 specified GitHub Pages via GitHub Actions. The site is still a
   static Astro build; only the publish step changes. Two consequences to honour from the first
   commit: Astro needs `base: '/pkmn-world'`, and every asset/link reference must be
   subpath-relative rather than root-absolute, because the site is served from a subdirectory.

5. **Repo lives on ext4 at `~/Projects/PKMN-World-Guide`, not under `/mnt/c/.../Github/`.**
   Deviates from the usual convention of keeping repos in the Windows `Github` folder. The
   extractors walk ~1200 `map.json` files and the site pulls a `node_modules` tree; both are
   5–10x slower across the WSL/Windows filesystem boundary, and this project has a recorded history
   of `/mnt/c` stalling under load. Reversible — nothing depends on the path.

6. **`game/` was cloned from the local `/mnt/c` checkout, then repointed at the GitHub URL.**
   Avoids a slow network clone of a 96 MB history. `.gitmodules` records the canonical
   `https://github.com/evilchinesefood/PKMN-World.git`, so a fresh `git clone --recursive` elsewhere
   behaves normally.

7. **The game repo is public.** Prior project notes recorded it as "PRIVATE, never public"; the API
   reports `private: false` as of the public-release polish in `87a66e89`. Recorded because it
   removes a real constraint — CI can clone the submodule without a deploy token.

## 2026-07-25 — re-pin

8. **Re-pinned the submodule from `v1.3.6` to `master` at `9ee61fbd`.** **[reverses decision 1 —
   user directed, answering audit Q1]** The audit found that at `v1.3.6` more than half of the
   systems brief §5 requires `systems.json` to cover simply did not exist — no Battle Net, no Shard
   economy, no Mega Stone vendors, no sim modes — and that **Mega Evolution was unusable** because
   nothing granted the Mega Ring. Documenting that pin would have shipped a guide for a materially
   smaller game than the project's own `FEATURES.md` advertises. All of it is present at
   `9ee61fbd`, verified: `giveitem ITEM_MEGA_RING` at `data/maps/RegionHub_2F/scripts.inc:19`.

9. **Pinned to a commit SHA, not a branch name.** `master` moves; the gitlink does not. Builds stay
   deterministic and the brief's "same submodule commit in, byte-identical JSON out" rule holds.
   Cost: the pin no longer names a release. Tagging `v1.4.0` at `9ee61fbd` would restore that for
   one command — offered, not assumed.

10. **The whole audit was re-measured at the new pin rather than carried forward.** Counts are
    pin-specific and `DATA-AUDIT.md` is the document the extractors are written against, so stale
    numbers there would propagate into code. Deltas: maps 1194→1195, hidden items 298→304, object
    events 6859→6925, species families disabled 265→**339**. The layout and encounter layers did
    not move at all, so the renderer spec and encounter schema are unaffected.

11. **The "74 disabled families" discrepancy is resolved, not a mistake in anyone's notes.**
    265 (v1.3.6) + 74 (a later strip pass) = 339 (master). All three figures were correct for their
    own commit. The durable rule stands: recompute from the pinned `species_enabled.h`, never
    inherit a count.

## 2026-07-25 — M2 template lock

**The templates below are FROZEN.** Brief section 7 requires one segment finished completely
before scaling to three regions; changing any of these afterwards means re-checking every page
that inherits them.

13. **Rendered map PNGs are not committed.** 32 MB, fully deterministic, 22 seconds to
    regenerate from the pinned submodule. CI runs `tools/porymap/Render.py` before building.
    Cost: CI and any fresh clone need Python, Pillow and numpy. The manifest's `content_hash`
    covers the _inputs_, so it already tells you when a re-render is genuinely needed.

14. **The design system's palette is the map's marker palette.** `src/styles/Guide.css` takes
    its accent colours from the Leaflet overlay markers — amber for items, violet for hidden
    items, red for trainers, cyan for warps. An amber chip in a table and an amber dot on the
    aerial map therefore mean the same thing without a legend. Changing a marker colour changes
    the page, deliberately.

15. **Type: condensed uppercase display, serif body, mono for all numerics.** Period-correct for
    a late-90s printed guide, and the serif body is what stops it reading like every other
    generated site. All three are system stacks — no font is downloaded, which keeps the
    subpath deploy and the zero-external-request property intact.

16. **Gate labels read "from X onwards", never "requires X".** A gate is a FLOOR (audit Q19).
    `gateLabel()` in `src/Names.ts` is the single implementation; both the map page and the
    walkthrough chapter call it. `always_available` gates render "from the start".

17. **A walkthrough chapter is the unit of hand-written content**, not a per-map blurb. Prose in
    the main column, Insider Tips boxed in the rail, maps listed alongside. Chapters declare the
    maps they cover in frontmatter, and map pages link back by matching that list — the pairing
    is declared in the content, never inferred from filenames.

18. **Trainer parties print `evs` and `nature` as "unspecified".** Those keys are used zero times
    in both `.party` files, so rendering the engine defaults would present them as the author's
    choice. Same rule for any absent field: say it is absent.

19. **Sevii is its own atlas section, not folded into Kanto.** 160 maps — 38% of all Kanto
    content — with its own ferry network and three dedicated region-map layouts.
    `Common.subregion_of_map()` parses `sKantoSubregionMapsecs` out of `src/regions.c` rather
    than hand-listing the islands, so it tracks the source.

20. **Dead data is excluded, not published with a warning.** The 132 `*_LeafGreen` encounter
    tables carry `live: false` and never render. A guide that shows a table and captions it
    "this may not apply" has failed at its job.

21. **The 22 hijacked trainer slots publish as the data has it** (user decision on audit Q10).
    Each carries `anomaly: "frlg_boss_in_hoenn_slot"` and its card says so plainly, pointing at
    game issue #36. The guide reports what the game contains; it does not quietly correct it.

22. **Deploy is GitHub Actions → rsync over SSH** to `dev.jdayers.com/pkmn-world`, replacing
    brief decision 2's GitHub Pages. `.github/workflows/Deploy.yml` enforces extractor
    determinism and the link/orphan check before publishing. Needs the `JDAYERS_SSH_PASSWORD`
    repository secret; the host allows password auth only and blocks SFTP, so rsync runs over
    plain ssh with pubkey auth explicitly disabled.

---

12. **`Testing/ValidateGen13.py` joins `tools/validate/`.** It is absent at `v1.3.6` but present
    and passing at the new pin, and it is the game's own invariant check — no obtainable content
    references a stripped family, and every Gen 4+ family is stripped. Cheaper and more
    authoritative than reimplementing the same check in the guide.

---

## 2026-07-26 — readability overhaul

The M2 templates (13–22) still stand. These entries record what the readability phase changed
around them, and the one place it exceeded a stated target on purpose.

23. **The homepage is the guide's contents page, not the map atlas.** It had been a wall of
    1,195 map links, which is an index of the data rather than an entry point to a guide. The
    homepage now opens on a short orientation block and the chapter list in play order; the
    1,195 links moved wholesale to `/maps`, reachable from the top nav beside Pokédex, Items
    and Gyms. Nothing was dropped — kanto 256 + sevii 160 + johto 254 + hoenn 458 + shared 67
    = 1,195, verified as a set equality in both directions against the manifest.

24. **A chapter's steps live in frontmatter as a structured `sections:` list, not in prose.**
    Prose can say "go north to the grass patch"; only data can say _which tile_. Making each
    step a record with an optional `at: [x, y]` is what lets the renderer draw a pin whose
    number **is** the step number, which is the entire mechanism decision 26 depends on. A
    section is exactly one map, so every `at:` in it is unambiguous without a map key per step.
    The written contract is on the Technical notes page, not in a schema file, because the
    people writing the remaining chapters will be reading chapters.

25. **`choice:` is a string and `choice_group:` is required whenever `choice` is present.**
    A boolean cannot distinguish "pick one, here, now" (the three starter balls) from
    "whichever you chose hours ago" (every rival party thereafter), and those need different
    words on the page — so the kind is part of the value. Grouping is explicit rather than
    positional for a harder reason: if a group were inferred from adjacency, an author who put
    two same-kind groups next to each other would silently get one group of four, and **no
    validator could catch it, because a group of four is legal content.** With the slug
    required, the two groups differ by construction and a mismatch becomes detectable. This
    shape is real, not hypothetical — Victory Road forks at stairs and again at doors with no
    action between.

26. **Step pins are a second numbering system, deliberately coexisting with the map pages'
    event callouts.** A map page numbers its own events in a fixed order (items → hidden →
    trainers → warps → signs); a chapter numbers its steps in play order. They are not
    reconcilable and should not be: one answers "what is on this map", the other answers "what
    do I do next". Collapsing them would force either the atlas into one chapter's route order
    or the walkthrough into the atlas's inventory order, and both destroy the thing they are
    for. They never appear together — a map page renders callouts and no step pins, a chapter
    renders step pins and no callouts — so a reader never sees two numbers for one place.

27. **Everything that is not a numbered walkthrough step starts collapsed.** Encounter tables,
    stat blocks, trainer parties and source citations open behind a summary line that carries
    its own count ("Wild Pokémon (9)"), so the closed state still tells you what is inside.
    Native `<details>`/`<summary>`, no JavaScript — it survives JS being off, it is in the
    accessibility tree already, and modern engines expand it for printing on their own. Where a
    fold meets an Insider Tips spoiler the fold **wraps** the spoiler and defaults to open, so
    the spoiler gate stays the only gesture that reveals anything.

28. **Extracted sprites are gitignored, exactly as the rendered map PNGs are.** Same reasoning
    as decision 13, applied to a second asset class: 1,978 PNGs deterministically reproduced
    from the pinned submodule by `tools/sprites/Extract.py`, so committing them would add a
    second copy to re-diff on every re-pin. This overrules `sprite-research.md §E`, which
    argued 1.6 MiB is small enough to commit — true, and beside the point. CI regenerates them.

29. **Sprites are keyed on species id, not dex number, and `is_base_form` from the extractor is
    the only implementation of "which form is dex N".** Three copies of that rule had grown —
    a regex in `species/[slug].astro`, another in `species/index.astro`, and a third pick
    inside `Extract.py` — and they had already drifted: dex 386 rendered Deoxys-Attack's stats
    on the page while dex 982 was decided by array order on both. This is the same failure that
    the `slugOf()` drift between `src/Names.ts` and `tools/qa/Links.mjs` produced when it cost
    486 phantom orphans, so the fix is deletion rather than synchronisation. The extractor now
    emits one sprite per enabled species and never picks a base at all, and the base form is a
    **data field** read from the game's own `form_species_tables.h` rather than a rule
    reimplemented per consumer. Cost: 596 front pics instead of 430, which are gitignored and
    therefore free.

30. **The rewritten Kanto chapter is 287 lines against a stated ~150 target.**
    **[deliberate deviation]** The instruction behind the target was "cut the prose", and the
    prose was cut hard: 448 lines to about 87. The file is larger than 150 because the steps
    became structured pin data (decision 24) — roughly 125 lines of the frontmatter is the
    `sections:` block carrying 9 sections, 45 steps and 37 verified coordinates. Cutting to
    150 would mean deleting pins, which would delete the mechanism that makes it a guide rather
    than an essay. The target measured the wrong thing; the intent was met.

31. **Verified engine detail moves to a Technical notes page, linked one-directionally.** The
    coordinates, flag names and source citations were all traced to the game and are worth
    keeping — just not on a page written for a ten-year-old. The chapter carries **no** key
    pointing at its Technical page; the Technical page carries `technical_to:` and the renderer
    scans for it, exactly as Insider Tips works via `companion_to:`. One authoritative key in
    one direction: a two-directional link can disagree with itself, and there is nothing a
    forward key does that the scan does not.

32. **Derived step pins must declare their arithmetic; an unconfirmable pin is omitted.** Two
    house rules the remaining chapters inherit. Where the source states a rectangle and the
    step needs a point, reducing it to the floored midpoint is acceptable **only** when the
    derivation is written out in an audit table on the Technical page with the real `map.bin`
    citation — stated-and-shown is not an invention. Where the data cannot confirm a tile at
    all, the step ships with no pin rather than a guess; a missing pin costs the reader a
    little, a wrong pin costs them their trust in all the others.

33. **Regional-form encounters are not unioned onto the base species page.** The obvious fix
    for a thin "Where to get it" section is to pull in every form's `obtainable_via`. Measured:
    it adds 21 deduped rows across 20 pages, all regional forms, into a table with no column
    saying which form a row yields — so the Rattata page would claim you can find Rattata at a
    location that gives **Alolan** Rattata. That invents a fact on twenty pages to enrich none.
    A form column would make it honest, and is a content task, not a rendering one.

34. **`tools/qa/Links.mjs` fails the build on any page nothing links to.** The existing orphan
    check only asserted that every _map in the manifest_ rendered a page; it was structurally
    blind to a stray content file publishing a page of its own. That is not hypothetical — one
    misplaced frontmatter key published a duplicate chapter under its own URL while every other
    check reported clean. The allowlist ships empty and stays that way by decision: all 1,632
    pages have an inbound link, so an unreachable page is a defect until someone writes down
    why it isn't.

35. **Printing mounts every map on `beforeprint` and prefetches the images on idle.** Print is
    deliberately supported, and an unscrolled chapter printed eight empty black boxes because
    the viewers mount lazily on scroll. **Both obvious fixes were tried and both failed**, and
    the reason is the durable part of this entry:

    - **CSS-only** — hide any viewer that never mounted — cleared the empty boxes and printed a
      chapter containing exactly **one** map. The pinned aerial map is the whole feature, so
      suppressing eight of nine is not a fix, it is a surrender.
    - **`beforeprint` alone** mounted all nine viewers synchronously and still printed only
      **41 of 46** images. Isolated by holding the mount at 1 of 9 while prefetching the
      images, which produced a PDF byte-identical to the warm path: **the race is the image
      decode, not the Leaflet instance.** That fact is what the fix follows from, and it is
      what a future maintainer needs before touching this code.

    So the fix is all three: `beforeprint` mounts every viewer, `requestIdleCallback` prefetches
    the images to remove the decode race while keeping the expensive Leaflet instances lazy for
    the common case, and the print stylesheet still hides any viewer that never mounted so a
    reader with JS off gets no map instead of a black hole. Cold print is now 573,300 bytes /
    46 images against a warm 573,354 / 46.

    Measure printed output by counting embedded image XObjects in the PDF. The preview lies.

36. **Maps print white with a black border, on all 1,195 map pages.** Consequence of 35's print
    stylesheet, recorded separately because its blast radius is different: the rule targets
    `.leaflet-container` globally, so every map page's printed appearance changed, not just the
    walkthrough chapter that motivated the fix. On screen a viewer sits on the design system's
    dark panel; in print that panel is a solid rectangle of ink, and a map whose image is still
    decoding prints as blank paper rather than a black hole. Deliberate, and an improvement —
    but a page a reader prints is a page the reader sees, so it is a design change to 1,195
    pages and belongs here rather than passing silently. See the deferred list in `NEXT.md §D`:
    the tables and the rail have **not** been given the same treatment yet, which is now the
    most visible thing left on a printed chapter precisely because the maps were fixed.

---

## 2026-07-26 — pre-ship fix wave

37. **Spoilers print revealed, on 125 map pages.** Decision 27's print rule forced every
    `<details>` fold open for printing but never reached `Spoiler.astro`, which hides its body
    with the bare `hidden` attribute — so those pages printed a "Hidden items (4)" heading, a
    "reveal" button that does nothing on paper, and no table. Reveal was chosen over
    suppression for three reasons: a printed page is used **away from the screen**, so silently
    dropping four hidden items is worse than showing them; printing is an explicit act by the
    reader on one page, not a site-wide default; and the gate is already protecting nothing on
    these pages, because the aerial map's own markers carry `Hidden: Nugget` in plaintext in
    the shipped HTML. The peek button is hidden in the same rule — a control that cannot be
    clicked is furniture. Blast radius, stated as decision 36 states its own: **what 125 map
    pages print changes**, and every spoiler elsewhere prints revealed too, including the
    Insider Tips rail on a chapter.

38. **A chapter body's `<h2>` sections fold when they carry reference rows, and only then.**
    Decision 27 was written universally and read as covering the reference pages; the
    walkthrough chapter's own body was owned by nobody, so ~2,900px of tables sat open below
    the last step on the page the whole phase existed to fix. The rule is mechanical rather
    than authored, so M5's chapters inherit it without a per-chapter list to maintain: the
    renderer splits the compiled body at each `<h2>`, and a section containing table rows or
    list items becomes a closed fold whose count **is** those rows. A prose-only section stays
    open, because a closed summary earns its keep by carrying a count and prose has none to
    give — and the section telling a reader where to go next must never sit behind a click.
    **A task list stays open on the same grounds**, decided after the chapter's departure
    checklist shipped folded once: a checklist is not something a reader consults when they
    want it, it is the chapter's exit gate and functionally its last step, and a checklist
    nobody opens is a checklist that does not work. The signal is mechanical rather than named
    per chapter — markdown's `- [ ]` compiles to a checkbox input and nothing else on these
    pages emits one — so every M5 chapter inherits it without a list to maintain.
    **Numbered steps are never folded**, in any form; they render from frontmatter above the
    body and are the one thing on the page that is not reference material. Cost: the body is
    rendered from `compiledContent()` rather than `<Content />`, so a chapter wanting Astro to
    process a relative image would need the component back.

39. **A heading never prints a number that counts something other than what its children
    count.** "Wild Pokémon (N)" counted distinct species over folds that count table rows, and
    the two disagreed on **330 of 331** pages (Altering Cave: 10 species, 73 rows). Both
    figures are true; neither is the other, and a reader who opens "(6)" and counts 13 has been
    taught not to trust the counts decision 27 added the folds to earn. The heading now carries
    no number at all rather than a second, differently-derived one: the child folds each carry
    a row count that can be checked by opening them, which is the whole point. The general form
    — a summary's number must be verifiable by doing the thing the summary invites — is what
    M5 should apply to any new heading.

---

## 2026-07-27 — post-ship

40. **A page can be generated from the game's prose, not only from its data.** `/features/`
    renders `game/FEATURES.md` straight out of the pinned submodule — `import.meta.glob` plus
    `compiledContent()`, the same mechanism `src/Chapters.ts` uses for `content/` — with nothing
    copied into this repo. The project's founding premise was that the guide is a function of
    the pin, and until now that meant extracted JSON; this extends it to the game's own written
    documentation, which was previously the kind of thing a human would have pasted in and let
    rot. **Precedent worth naming:** if the game repo already says it, generate it rather than
    restate it. The page follows the pin for free, and a re-pin cannot leave it stale.

41. **Section ordering is a small lookup table, and an unrecognised heading publishes into the
    middle tier rather than failing the build.** Nine sections are sorted into `play` / `extra` /
    `build` by naming them in a tier table; a heading the table does not know falls into `extra`.
    The alternative — hard-fail on an unknown heading — was rejected deliberately: a re-pin is a
    scheduled maintenance action, and trading a broken deploy for a section appearing in the
    wrong group is a bad exchange. Wrong group is visible and cosmetic; vanished or unbuildable
    is neither. Tested rather than assumed, by editing the submodule working tree and restoring
    it: a renamed heading demoted to `extra` and stayed on the page, and a new `(unreleased)`
    section published, folded and marked. That exercise is also what caught `## Roadmap
(dormant)` losing its tier to the parenthesis, fixed in `4dcab7f`.

42. **Unshipped content is never the first thing a reader meets open.** A section the source
    marks `(unreleased)` or `(dormant)` always folds — **even when it is prose-only**, which is
    the one place decision 38's "prose stays open" rule is deliberately overridden — takes the
    red `trainer` tone, says "Not in the game yet" or "Built, but switched off" in its shut
    summary, and repeats the warning inside. A marked `<h3>` nested in another fold keeps a red
    chip on its heading. The status comes from the source's own marker, so the game decides what
    is unreleased and the guide only presents it. Reasoning: a reader scanning an open section
    has already started believing it, and a warning below the fold arrives after the damage.

43. **A ticked checklist item is keyed by a hash of its own text, not its position.** Storage is
    `pw-checked:<chapter-slug>` — one key per chapter, so three regions cannot collide.
    Position is the obvious key and fails precisely where it matters: insert an item at the top
    of a six-item list and every tick below slides onto the wrong line **and the brand-new item
    silently inherits a tick**. A guide that tells a ten-year-old they already caught the Mankey
    when they did not is worse than one that never persisted anything. Text hashing cannot do
    that — a new item is a new key and starts unticked, and an item that merely moves keeps its
    tick. **The cost is that rewording an item resets it, and that is the honest half:** if the
    sentence changed, what is being asked has changed, and the reader should look again. Markup
    edits do not count; tags are stripped and whitespace collapsed before hashing, so bolding a
    word or repointing a link leaves the tick alone.

44. **A map must never take the page's scroll — one contract in both contexts.** `scrollWheelZoom`
    is off on chapter maps and on all 1,195 map pages. The two were judged separately and got the
    same answer: a map page is mostly _about_ its map, which argues for keeping wheel zoom, but it
    keeps encounters, trainers and exits below the fold, so it traps a reader identically. One
    rule across the site also beats two — a reader who learns the contract on a chapter should not
    find a different one on a map page. Zoom stays discoverable through the `+`/`−` control already
    drawn on every map, plus double-click, shift-drag and pinch; Ctrl+wheel was rejected as needing
    a hint overlay to be discoverable at all, and click-to-activate because a click on these maps
    already means something.

    **The touch half was worse than the wheel half, and was measured rather than reasoned about.**
    Leaflet's own stylesheet sets `touch-action: none` on a container with drag and zoom enabled,
    which forbids the _browser_ from scrolling: a one-finger drag moved the page **0px**, and on a
    chapter the map is already fitted to its box so the thumb could not even pan. The page simply
    stopped dead. Turning `dragging` off for a **coarse pointer** leaves Leaflet's own
    `touch-action: pan-x pan-y`, which is exactly the wanted contract — one finger scrolls, two
    fingers pan and pinch — with no custom gesture code. A touchscreen laptop reports a _fine_
    pointer and keeps drag-to-pan.

    **Phone is now a supported width, not a best effort.** `flex-wrap` on `.banner nav` closed the
    last sideways-scroll defect at **320px** across all 15 page types (deferred C13), and the
    Leaflet layer control now collapses to its button on a coarse pointer instead of covering the
    middle of a 342×288 map. Supporting a width is a commitment to keep testing it.

45. **M5's content is derived from source, not from a playthrough — and the guide therefore never
    claims difficulty or pacing.** The brief allowed for the content being a byproduct of the 1.0
    playthrough; the answer is that nobody is playing it. Chapter 1's 37 pins came from reading
    scripts and verifying coordinates against `map.bin`, and that is the method for all of it.
    **The consequence is a content rule, and it is the important half of this entry:** nothing
    derivable from source supports "this fight is tough", "you will want to grind here", or "this
    part drags". Those sentences are the natural voice of a strategy guide and they must not appear,
    because the guide cannot stand behind them. Chapter 1 is already clean on this; every future
    chapter inherits it. What _is_ derivable — levels, parties, encounter rates, what you will miss
    — is what the guide says instead, and it is enough.

46. **M5's shape is settled: badge-segment chapters, Sevii included, and no schema change.**
    Answering the questions this document's handoff raised, so they are not reopened.
    **Granularity** stays at chapter 1's — one badge segment, split when it gets big — giving
    40–50 chapters. **Sevii gets full chapters**, not atlas-only, taking the total to 45–58; its
    160 maps are 38% of Kanto and decision 19 already treats it as a first-class region.
    **Boss pages need no new keys**: `sections:` carries the gym puzzle and a generated
    `TrainerCard` carries the party, so the frozen contract survives all 24 of them plus the
    leagues. That last one matters most — the point of freezing the template at M2 was that the
    next 50 chapters would not each renegotiate it, and this is the test it had to pass.

47. **An unrecognised status marker warns; an unrecognised heading still does not.** Decision 41
    says a heading the tier table does not know publishes into the middle tier rather than
    failing the build, because wrong group is cosmetic and a broken deploy is not. That stands
    unchanged. Status markers are the other case and get the opposite default: `STATUS_RE`
    matched only `unreleased|dormant`, so `## Battle Frontier (beta)` did two wrong things at
    once — it lost its tier to the parenthesis (the bug `4dcab7f` fixed for the two known words,
    reappearing for every unknown one) **and it published with no warning at all, which reads as
    finished, shipped, playable content.** That is the one thing decision 42 exists to prevent,
    and it is not cosmetic: a wrong group misfiles a feature, a missing warning sends a
    ten-year-old to look for something that is not in the game.

    So **any** trailing parenthetical word is now taken as a marker. A known word keeps the
    sentence it has earned. An unknown one folds, takes the red `trainer` tone and carries a chip
    with **the source's own spelling** — the structural half of decision 42, which is what stops
    it reading as playable — but a deliberately weaker sentence: it says the notes used a word
    this guide does not know and it cannot promise you can play this, because "You cannot play
    it" is a claim about the game that nobody here has checked. Loud in shape, quiet in wording.

    Matching is letters and spaces only, so the realistic non-status parenthetical — `(Gen 8)`,
    `(v1.3)`, `(2 of 3)` — keeps its brackets and is left alone. The build **warns and does not
    fail**, which is decision 41's judgement applied to a re-pin being scheduled maintenance:
    the person doing it is told once, by name, at the end of the build.

    Tested by editing the submodule working tree and restoring it byte-identically, over
    `(beta)`, `(planned)`, `(WIP)`, `(coming soon)` and `(experimental)`, plus both known words
    and no marker at all. The decisive case is a **`play`-tier** section, the only tier that
    renders open: unmarked it stays open, and `(beta)` now folds red with a warning exactly as
    `(unreleased)` does, keeping its tier instead of being demoted.

48. **Two checklist items with the same sentence are keyed apart, and `- [x]` is a build
    warning rather than a feature.** Decision 43 chose to key a tick by a hash of the item's own
    text and named the cost it accepted — rewording resets the tick. It did not consider two
    items whose text is _identical_, and that case was live: both got the same key, so ticking
    one and reloading came back with **both** ticked. That is the checklist crediting work the
    reader never did, which is the precise harm 43 exists to prevent, reached by a route 43 did
    not look down.

    **The first occurrence keeps the bare key; later ones get `~2`, `~3`.** Identical text
    carries nothing that could tell two items apart, so the tiebreak has to be position, and the
    only real question is which occurrence pays for it.

    **The trade, reasoned rather than defaulted, because it is not obvious.** Suffixing _every_
    occurrence (`~1`, `~2`) is the tidier rule and it was rejected: it optimises the wrong
    direction. **Adding a duplicate to a chapter is far likelier than deleting one** — chapters
    grow — and the first occurrence is the only one that can be carrying a stored tick, because
    it is the only one that existed before. Suffixing the first therefore turns a routine edit
    into a silent reset of a line the reader had already ticked, which is the failure this whole
    entry is about. Leaving the first bare means adding a duplicate costs nothing at all, and
    only the rarer deletion case pays. Both rules are positional inside the duplicate set; this
    one puts the cost where it is least likely to be met and least likely to matter.

    **What this costs, stated rather than hidden:** deleting a duplicate shifts the survivors up
    one, so a survivor can inherit the deleted twin's stored state. That is the positional
    fragility 43 rejected, and it is **bounded to items whose text is identical** — everything
    else stays text-keyed. Inside that set the "wrong" one is by definition indistinguishable to
    the reader, because it is the same sentence. **The real fix is rewording, which only an
    author can do, so the build warns and names the sentence.** Ordering the ambiguity is second
    best; removing it is first.

    **`- [x]` does not pre-tick and will not.** The departure checklist belongs to the reader, so
    it starts empty — a checklist whose first act is to claim the reader has already done
    something is the same lie 43 was written against, just delivered on page load. But an author
    writing `- [x]` previously got an ordinary empty box and no signal at all, so it is now a
    build warning naming the file and line. Warned, never thrown: same instrument and same
    reasoning as decision 47.

    **Worth recording plainly: this one small feature has produced five silent-failure shapes** —
    a nested sub-list, a loose list, duplicate keys, `- [x]`, and the `<p>` wrapper. Every one
    rendered a page that looked correct and did the wrong thing, and **three of the five were
    invisible on the page** and existed only because someone constructed the input. That is what
    `tools/qa/Checklist.mjs` is for, and why it runs in CI **before** the build rather than after
    it: a green build proves nothing about a checklist, because the broken versions all built
    perfectly. The table in it is the space of shapes markdown can produce, not the bugs already
    fixed — a fixture that only covers those cannot catch shape six. Anything added here is
    assumed to have a sixth shape until the markdown that produces it has been enumerated.

49. **A checklist item's sentence ends at its first block-level child, and "block" is defined by
    exclusion.** `NESTED = /<(?:ul|ol)\b/i` described itself as "the whole set" and was a special
    case wearing a general description: for a tight item the block ends at the first block-level
    child, and a list is only the block an author reaches for first. Verified by review and then
    reproduced: a `blockquote`, an `###` heading, a raw `<div>`, a `***` rule and a fenced code
    block all folded into the `<label>` — invalid markup, since a label takes phrasing content —
    and four of the five **changed the item's key**, which silently wipes every tick a reader has
    stored on that line while the page looks perfect. That is decision 43's harm arriving by a
    third route, after 48 closed the second.

    **The fix inverts which set gets named.** HTML defines phrasing content and that definition
    does not grow; the set of blocks that can sit under a checklist line does. So the code names
    the phrasing tags and ends the sentence at the first tag that is not one of them, and an
    unrecognised tag ends the sentence rather than entering the label. That is the right
    direction for a **bare** block — `<div>`, `<hr>`, `<pre>`, a heading, a custom element all
    land outside the label and the item keeps its key.
    **It is not a guarantee, and an earlier version of this entry wrongly said it was.** The scan
    stops at the first non-phrasing _tag_ and has no notion of nesting, so a phrasing
    **container** holding non-phrasing children is cut _inside_ the container: `<svg>`, `<math>`,
    `<select>`, `<video>`, `<map>`, `<template>` and a `<span>` wrapping a block each leave their
    open tag in the label and their children and close tag outside it, straddling `</label>`, and
    the key truncates to whatever preceded the container —
    `- [ ] Beat <svg><circle/></svg> Brock today` keys `1wl5u5h`, which is `keyOf("Beat")`. That
    is shape six's harm through a container instead of a bare block. Recorded, not fixed
    (`NEXT.md` group H, F1): it needs raw HTML hand-written into a chapter, and the honest repair
    is nesting awareness, which is a parser.
    **Naming the blocks is what shipped shape six, so the rule may not name a block again** —
    including by "just adding blockquote to the list", which is the repair that would have left
    `<div>`, `<hr>` and `<pre>` broken.

    **The `seen` scope was wrong at the same time, and it is the same failure as 48.** The
    comment claimed "one chapter is one `seen` scope, exactly the scope of `pw-checked:<slug>`".
    It was not: `[slug].astro` calls the rewriter once per `<h2>`, so every section got a fresh
    map, and two checklists in one chapter sharing a sentence both took the bare key — the tick
    spread across them on reload and the duplicate warning never fired. Storage is per chapter,
    so **the scope moved to the code that owns the loop** — `chapterBody()`, which took the
    `<h2>` split in with it (decision 51), so the page cannot hold a per-section scope because it
    no longer holds the loop. A comment asserting a scope is not a scope.

    **An item the rewrite does not recognise is now left whole and reported.** The claim that
    unrecognised shapes "are left exactly as it came in rather than half-rewritten" was also
    false: the scan did not step past the item, walked back into it, and rewrote a nested task
    list inside a parent nobody rewrote. It now steps past, and says so at the end of the build —
    an item this code declined is a box that renders and does nothing, which is the signature all
    six silent failures share, and the only new thing worth adding is that it stops being silent.

    **The header comment called resetting-on-reword "the honest failure of the two". It is no
    longer the only one left, and saying so was a lie by omission.** Decision 48's duplicate rule
    means deleting a duplicate lets a survivor inherit its twin's tick — false credit, the
    dishonest failure this whole design exists to avoid. The behaviour is kept for 48's stated
    reasons; the comment now names the failure it chose instead of implying there is none.

50. **A trailing parenthetical is prose unless it is a status word, and the build warning — not
    the chip — is what keeps decision 47 whole.** 47 widened `STATUS_RE` to any bracket of
    letters and spaces so that `## Battle Frontier (beta)` could not publish as playable. The
    pattern cannot see meaning, and `(beta)` and `(all three regions)` are the same shape:
    review built `### Region switching (all three regions)` and got shipped, playable content
    wearing a red `all three regions` chip, a "this guide cannot promise you can play this"
    warning, and its heading text cut off. That is decision 42's harm with the sign flipped —
    the guide disowning content that **is** in the game — and the guard 47 relied on, "letters
    and spaces only", stops nothing: it excludes `(Gen 8)` and `(v1.3)` and admits `(optional)`,
    `(Kanto only)` and `(all regions)`.

    Pattern cannot separate the two, so **vocabulary does**: a list of words that mean "not
    finished", deliberately wider than the two the guide can explain, since 47's whole case is
    the word it cannot explain. A candidate outside it is part of the heading and publishes
    exactly as the source wrote it.

    **The honest way to read the trade is that both directions warn.** Every unrecognised
    candidate is still named at the end of the build, by heading, so a re-pin introducing a
    genuinely new status word is told in the same breath it would have been before. What changed
    is only what the page does while the operator reads that warning: publish the heading as
    written, or publish a red contradiction of it. One of those can ship a falsehood and the
    other cannot. **The residue, stated rather than hidden:** a status word outside the
    vocabulary now publishes open for as long as it takes someone to read the warning and add
    the word — that window is the cost, and decision 41's judgement that a re-pin is scheduled
    maintenance with a person attached is what pays for it.

    Proved by real build over thirteen source edits, restored byte-identically. Ten rows are
    unchanged, including all five of 47's unknown markers (`beta`, `planned`, `WIP`, `coming
soon`, `experimental`) keeping their tier and their red fold, both known words, and
    `(Gen 8)`. Three rows changed, and all three are the false positives: `(optional)` and
    `(all regions)` and `(all three regions)` keep their heading text, lose the red chip, and
    are named in a build notice instead.

51. **The keys readers' ticks are stored under are frozen in a committed file and checked against
    the built site.** A tick is stored under a hash of the item's _compiled_ sentence, and
    `text()` strips tags but not entities — so a sentence containing `&` hashes whatever spelling
    the markdown compiler chose, which today is `&#x26;` (`src/Features.ts` already documents
    that it spells ampersands numerically). An Astro or remark upgrade that spells it `&amp;`
    instead, or that flips smartypants and rewrites a quote or a dash, **silently rekeys every
    checklist line containing one and orphans every tick a reader has stored on it.** Nothing
    renders differently and nothing warns. This is the seventh failure of this feature's kind and
    the first one that is not a markdown shape at all.

    **`tools/qa/Checklist.mjs` structurally cannot catch it**, which is the reason a second file
    exists. Its strongest assertion — the same sentence keys identically in every shape — compiles
    both sides through the same processor, so a processor change moves both sides together and the
    assertion stays green while the site rekeys underneath it. **A guard against a toolchain
    change has to compare against something the toolchain cannot move: a frozen literal.**
    `tools/qa/GoldenKeys.json` is that literal, and `tools/qa/Keys.mjs` reads `dist/` rather than
    compiling markdown, so what is checked is what ships.

    **Three outcomes, told apart on purpose, because the right response differs.** A recorded
    sentence still on the page under a different key is a **rekey** and fails hard — including
    when the sentence differs only in typography, which is exactly what a smartypants flip does
    and which would otherwise read as every author rewording every line on the same day. A
    recorded sentence gone from the page is an **author edit**, decision 43's accepted cost, and
    says so. A key on the page that was never recorded is **unprotected** and fails until it is
    recorded — no reader can hold a tick under a key that never shipped, so nothing is lost, but
    silently leaving new chapters uncovered is how the file would rot as M5 adds 45–58 of them.

    **`--write` only ever adds.** It will not rewrite the key of a sentence already in the file,
    because that is precisely the orphaning the guard exists to catch, and blessing it must be a
    deliberate edit by someone who has read the failure — not the command a person runs to make
    CI green. Proved: with the processor changed, `--write` recorded the new key, left the old one
    in place, and still exited 1.

    Proved by a real toolchain change rather than a mock — `markdown: { smartypants: false }` in
    `astro.config.mjs`, full build, guard fired: `j5i4mm → ttr6sw` on "The Potion from the item
    ball on Viridian's top row", correctly classified as typography rather than an author edit.

    **The chapter split moved into `src/Checklist.ts` in the same change**, for the reason
    `isTaskList` lives there: a chapter is several sections, whoever owns the loop owns the scope,
    and while `[slug].astro` owned it the scope was per-section (decision 49). `tools/qa/
Checklist.mjs` now drives `chapterBody`, the function the page runs, instead of
    re-implementing the split beside it — that second copy is why the fixture stayed green through
    the bug. **A test that reimplements the path it is testing is testing itself.**

    **This is where the checklist stops.** Six silent shapes, then a seventh that was not a shape.
    Reader data is now guarded by a fixture over 21 markdown shapes, two build warnings, and a
    frozen key file checked against the shipped HTML. The two candidates that remain
    (`NEXT.md` group H) both require hand-written raw HTML in a chapter, which `content/` does not
    contain and the markdown compiler cannot produce. A shape eight goes to `NEXT.md` for M5
    rather than another round here.

52. **The re-pin to `2b1fba48` makes decision 21 obsolete rather than wrong, and 21 stays as
    written.** All five bugs this guide found are fixed upstream — `0f5b2595` covers game issues
    #36–#39, `6ee98c77` covers #40 — so decision 21's subject no longer exists. "The 22 hijacked
    trainer slots publish as the data has it" was the right call for as long as the data had it;
    it now describes a version of the game nobody runs. It is left intact because it is the record
    of a decision that was correctly made, not a claim about today's data.

    What the guide publishes instead, all measured at the new pin rather than inherited:

    |                                      | `9ee61fbd`       | `2b1fba48`      |
    | ------------------------------------ | ---------------- | --------------- |
    | `anomaly`-flagged trainer slots      | 22               | **0**           |
    | map pages captioning a hijacked slot | 12 (22 captions) | **0**           |
    | ids carrying a Leader class          | 74               | **66**          |
    | gym leaders on `/gyms/`              | 24               | **24**          |
    | species nothing in the game produces | 3                | **1** (Jirachi) |
    | off-image markers                    | 19               | **17**          |

    **The detection is kept and only its expected count changed.** `EXPECT["anomalies"]` is
    `(22, 0)` — the audit did record 22, the pin now measures 0, and that divergence is exactly
    what the two-column shape prints a DRIFT line for. Setting it to `(0, 0)` would claim
    `DATA-AUDIT.md` said something it never said and silence the one line that stops a stale
    figure passing. The `TRAINER_LYLE` assertion is inverted rather than deleted for the same
    reason, and made stronger while inverting: it now asserts LYLE resolves to `LYLE, Bug Catcher`
    rather than merely that no slot carries the flag. A count of zero says nothing looks hijacked;
    naming the canonical slot says the fix actually landed.

    **Two guards proved to be no-ops, and both stay.** The `anomaly` filter on `/gyms/` produces
    24 leaders with it and 24 without it, on the same id set — verified both ways rather than
    reasoned about. The caption branch on map pages renders nowhere. Deleting either would mean a
    recurrence of the original paste publishes silently, which is the failure the guide was built
    to catch, so both remain as dormant tripwires with comments that say so.

    **`FEATURES.md` is byte-identical across the re-pin and `/features/` moved anyway** — by
    exactly the 40-character commit SHA it cites, proven by substituting the old SHA back into the
    built HTML and recovering the previous MD5 byte for byte. That is deferred item 30 working as
    designed rather than failing: the page cites the commit it was built from, and it only stays
    honest because extraction ran before the build. A local re-pin that skips extraction still
    produces a page that contradicts itself.

## 2026-07-27 — chapter structure

53. **Each section's map is sticky inside that section, and the map is capped so the steps it
    exists for keep the screen.** The chapter set the map, then the steps under it, which works
    up to about six steps and then stops working. Viridian City is fourteen, and eight of those
    are a tile-by-tile walking route — sentences that exist _only_ to be read against the map —
    with the last of them 1,068px below a 550px map at 1280 and 1,631px below it at 390.

    **The figures, under the instrument this was measured with.** The step is scrolled
    `block: "end"` — where a step arrives when a reader works down the page, and where a clicked
    pin now puts it — and the count is steps with **zero** pixels of their own map on screen:
    **7 of 44 at 1280×800 and 9 of 44 at 390×844; 0 of 44 at both, after.** `nearest` gives the
    same four numbers. The blind set at 1280 is exactly `viridian-city` steps 8–14, and no step
    anywhere is marginal — every one of the 44 reads either 0 or more than 40px, so the count does
    not turn on a rounding rule. It is stable across 780/800/820px viewport heights, and falls to
    5 of 44 at 900px.

    **An earlier draft of this entry quoted 15 of 44 and 23 of 44. Those are `center` readings**
    printed under an `end` heading — real numbers, wrong instrument, and higher, so the correction
    reduces the claim. `center` cannot be used on the fixed page at all: the stuck map occupies
    the middle of the viewport, so all 44 rows fail the harness's own guard rather than measuring 0. Quote `end` or `nearest`, which reproduce on both builds.

    Pin N _is_ step N (decision 26), and that pairing is worth nothing when the two are never
    visible together.

    **Sticky inside the `<section>` rather than inside the page, because a section is one map.**
    The release is then automatic and correct by construction: the map follows exactly its own
    steps and lets go at the section boundary, so no map is ever stuck beside another map's
    steps. Nothing else moved — same markup, one viewer per section, same `IntersectionObserver`
    mount, same 37 pins.

    **The three ways it could have gone wrong, and what each costs:**

    - It must not cover the banner, whose height is **not** a constant — 49px on a desktop,
      126px at 390px where the mark and six nav controls take three rows, and M5 adding a nav
      item moves it again. `Base.astro` publishes `--banner-h` from a `ResizeObserver` (not a
      `resize` listener: the banner also changes height when the display font loads, which fires
      no resize event). A hard-coded offset would have put the map behind the banner on a phone.
    - It must not follow the reader as an **empty box**. With JavaScript off the viewer is a
      reserved rectangle, and the sticky rule is therefore `:has(.leaflet-container)` — it
      applies only to a map that actually mounted. JS off measures `position: static` on all
      nine, i.e. exactly today's layout.
    - It must not **fill the screen it is stuck to**. `max-height: min(30rem, 52vh)` on the
      chapter's `.compact` viewers only binds on a window shorter than 923px; at 1280×800 the map
      goes 480 → 416px and about three steps stay under it. `.compact` is set by this page and
      nowhere else, so the 1,195 map pages measure byte-identical.

      **The cap costs 16% of tile size and the reason is a zoom snap, which is worth knowing
      before anyone tunes it.** Measured off the image overlay's own rect on Viridian City:
      **11.31 → 9.52 px per tile**, because `fitBounds` with `zoomSnap: 0.25` quantises, and 480px
      and 416px fall either side of the boundary between scale 2^−0.5 and 2^−0.75. The map is
      768×640, so **any cap at or above 453px keeps the larger zoom** — 57vh rather than 52vh at
      an 800px window — for 40px less step band. That is a real option, not a defect; it was left
      at 52vh because the band is what the fix exists to create. An earlier note in this entry
      said "12px per tile to about 10.4", which ignored `zoomSnap` and was wrong in both columns.

    - **The `--banner-h` fallback is safe by accident, and the code comment gives the wrong
      reason.** It claims the CSS constant covers a browser without `ResizeObserver`. In practice
      no such browser reaches the rule: `:has()` postdates `ResizeObserver` in every engine, so
      anything lacking `ResizeObserver` also lacks `:has()` and gets `position: static` — the
      fallback constant is unreachable rather than merely untested. Harmless, and recorded so the
      next person does not treat it as a tested path.

    **Rejected, with the measurement that rejected each.** _Side by side at wide viewports_: the
    prose column is 780px and the steps already run to a 68ch measure, so a two-column split
    leaves the map under 400px. Against the measured 11.31 px per tile today, a 380px-wide column
    snaps to scale 2^−1.25 and yields **6.7 px per tile** — on the one page whose whole argument
    is that the tiles are readable, and it would push more pins into the declutter path that
    decision 32 tuned at 7px. Sticky keeps the map full column width.
    _Splitting long sections_: needs edits to frozen content, and a 14-step section is legitimate
    — the next chapter simply recreates the problem. _A per-step crop of the map_: 44 viewers
    instead of 9, and it breaks the pin contract, which is one numbered set per section.

    **A defect the fix introduced, and the first repair of it was not enough.** A stuck map owns
    the middle of the viewport, so `scrollIntoView({block: "center"})` — what clicking a pin did —
    scrolled the step behind the map the reader had just clicked. The first repair used
    `block: "end"`, and **that is right only while the step fits the band the map leaves.** At
    390px Route 1's band is 158px and its steps run to 226px, so `end` pushed the head of three
    steps up behind the map (**where the map is sticky** — with no sticky map `end` is correct and
    is what the non-sticky branch uses): `oaks-lab` 5 by 19px, `route1` 2 by 32px and `route1` 3 by
    **92px**,
    taking the numbered badge with it. The reader clicked pin 3 and lost the numeral 3 — the pin
    -to-step pairing, broken by the fix meant to serve it. This entry previously called that
    "closed"; it was not.

    The click now puts the step's **top** just below the map's predicted stuck bottom, read from
    `getComputedStyle(fig).top` plus the figure's height so the script cannot disagree with the
    stylesheet about where the map stops. One prediction covers both cases with no branch: if the
    map turns out not to be stuck, the step still lands below it, because a step always follows
    its map in the document. **37/37 pin clicks land the step's first line clear at 320×640,
    320×560, 390×700, 390×760, 390×844, 768×560, 1280×600 and 1280×800** — asserted at three
    probe points across the step's first line, including the badge, not at its visible middle,
    which is what let the earlier check pass a step whose head was hidden.

    **And it stops sticking where there is no room to stick — which means a FULL revert, not a
    change of `position`.** The band is driven by the banner, which wraps: 126px at 480px wide and
    under, 93px from 560 to 720, 49px from 740 up. At 390/320 the band is −9px at a 560px-high
    window, 57px at 640, 86px at 700, then 117px at 760, so below 760 the map owns the screen and
    the page goes back to the layout this replaces.

    **The first version of that revert reset only `position`, `z-index`, `background`, `padding`
    and `margin`, and this entry claimed the reader then "gets the old layout, which still works".
    That was false, and the measurements say so.** `scroll-margin-block`'s 24px bottom and the
    viewer's `vh` caps both stayed in force, so what shipped below 760 was the old layout shifted
    24px with 8px less map — and the non-sticky click branch used `block: "start"`, which parks the
    step under the banner and scrolls the map, always earlier in the document, completely off the
    top. Measured against `bef5f66` with clicks driven through Leaflet's own handler and the scroll
    polled until it stopped: **pin clicks landing with zero map on screen went 31→37 of 37 at
    390×700 and 24→37 at 768×560**, and scroll-blind steps regressed at six sub-760 sizes. A
    partial revert is not a revert.

    All four properties now revert together and the non-sticky branch uses `block: "end"`, which
    beats even the `center` it replaced because it gives the map the whole viewport above the step
    rather than half of it. The result is better than baseline everywhere and worse nowhere:

    | size     | zero-map pin clicks | scroll-blind steps |            |
    | -------- | ------------------- | ------------------ | ---------- |
    | 320×560  | 37 → **27**         | 31 → 31            | old layout |
    | 320×640  | 36 → **23**         | 26 → 26            | old layout |
    | 360×640  | 33 → **21**         | 23 → 23            | old layout |
    | 375×667  | 31 → **19**         | 21 → 21            | old layout |
    | 390×700  | 31 → **17**         | 19 → 19            | old layout |
    | 393×730  | 30 → **17**         | 17 → 17            | old layout |
    | 390×750  | 30 → **16**         | 16 → 16            | old layout |
    | 390×759  | 30 → **16**         | 16 → 16            | old layout |
    | 390×760  | 29 → **0**          | 16 → **0**         | sticky     |
    | 390×844  | 26 → **0**          | 11 → **0**         | sticky     |
    | 768×560  | 24 → **0**          | 10 → **0**         | sticky     |
    | 1280×600 | 24 → **0**          | 10 → **0**         | sticky     |
    | 1280×800 | 17 → **0**          | 8 → **0**          | sticky     |

    **The width half of the query was also wrong at first.** `max-width: 900px` disabled 768×560,
    which measures 126px of band and works perfectly — the selector was switching off a size the
    measurements said to keep. It is `739px` now, just below the 740px where the banner stops
    taking extra rows, which is the thing that actually drives the band.

    A JS clamp is kept as a backstop for shapes the media query does not name, so a click can never
    scroll a step off the bottom of the screen; it only binds on something like a 300px-high
    desktop window.

    **Minor, recorded rather than fixed:** a `max-height` media query is re-evaluated when a mobile
    URL bar collapses, so a phone scrolling across the 760px boundary can flip the map between
    sticky and static mid-scroll.

    Verified by real mouse clicks with the scroll settled and `elementFromPoint` asserted, because
    this repo has twice shipped a check that measured something other than what it claimed — and
    this defect is a third instance: the original check asked whether the step's _visible middle_
    was the step, which is true of a step whose head is behind the map.

    **Print is untouched and was measured, not assumed.** The sticky rule and the `vh` cap are
    both reset under `@media print`, since paged media has nothing to stay with and `vh` there is
    the page box. Cold print — never scrolled — is identical before and after: 9/9 viewers
    mounted, 9 overlays, 37 pins, 0 empty boxes, the same four map-art heights, the same 13,724px
    document, and a PDF of 671,206 vs 671,239 bytes carrying **48 embedded image XObjects both
    ways**. Decision 35 stands unchanged.

54. **The chapter's handoff section never folds, and it is chosen by position rather than by its
    heading.** Decision 38 folds a body `<h2>` carrying table rows or any `<li>`, which is the
    right mechanical signal and one silent trap: "where you go next" must never sit behind a
    click, and two bullet points would have put it there — invisibly, because a fold looks
    exactly like an open section until you notice the chevron. It held on chapter 1 only because
    that chapter's handoff happens to be prose-only.

    **Matching the heading text was the obvious fix and it is the wrong one — but not for the
    reason first recorded here.** An earlier draft said the phrase "where you go next" appears
    nowhere in `content/`. **That is false**: `content/kanto/PalletToViridian.md:180` is
    `title: Where you go next`, and it renders as an `<h2>`.

    The true argument is stronger. That heading is the title of the last **walk** section, built
    from `sections:` in frontmatter — and walk sections are never folded. The section the fold
    rule can actually hide is the **body** heading "What is ahead on Route 2". So a lexical rule
    would match "Where you go next", exempt an element that was never at risk, report success, and
    leave the section it was supposed to protect folding exactly as before. **A vocabulary would
    not merely miss the target; it would hit the wrong element and look like it worked** — which
    is worse than no rule, because it would be believed. Verified: the phrase is in the
    frontmatter and not in the markdown body, and the six body `<h2>`s the rule acts on are
    "Picking your starter", "The two rival battles", "What lives in the grass", "What you cannot
    reach yet", "What is ahead on Route 2" and "Before you leave, check you have".

    So the renderer exempts **the last body section before the departure checklist** (or the last
    section outright where there is no checklist). That is the shape the chapter already has, and
    it is stated on the Technical page so authors know where the handoff goes. It costs the
    author nothing to remember, which is the point — the failure this replaces was one nobody
    would remember to avoid. Chapter 1's folds are unchanged at 3 / 3 / 8 / 7.

    **The residual was recorded as benign and half of it is not.** The earlier wording said a
    reference section written after the handoff "renders open instead of folded, which is more
    scrolling, not a hidden instruction". Only the first half is true. Appending a section also
    stops the handoff being last, so the handoff is no longer exempt — and it then folds the
    moment it carries a list, **which is exactly the hidden instruction B4 exists to prevent.**
    Constructed and confirmed: two bullets under "What is ahead on Route 2" plus a `## Trainer
notes` table after it renders **"What is ahead on Route 2 (2)"** behind a chevron while
    "Trainer notes" sits open. Positional does not make the trap unreachable; it moves it.

    **So the build says which section it picked, on every chapter, every build.** Nothing in code
    can tell a handoff from reference material by reading it — that is the same guess as deciding
    which sentences are instructions, which is why decision 55 is a contract and not a check. But
    naming the section the renderer _treated_ as the handoff needs no judgement, and it makes both
    traps visible in build output. A second clause fires on the signal rather than on a rare
    shape: the pick is suspicious exactly when it carries reference rows, since a handoff is prose
    or a short list. On the healthy chapter it prints one line naming "What is ahead on Route 2"
    and nothing more; on the constructed defect it names "Trainer notes", says it carries 1
    reference row, and tells the author to move the handoff last. Silent where it should be,
    loud where it should be. Every other shape was checked and is safe: no checklist → last
    section exempt; checklist first → nothing exempt; empty body → no-op; single section → benign.

55. **The body is not split around the steps, and that is a convention rather than a limitation.**
    Everything in the markdown body renders after every numbered step, whatever it is about. The
    fix is an authoring rule, not a renderer feature: **an instruction belongs in `sections:` as a
    step**, and the body opens with scene-setting and never tells the reader to do anything.
    Splitting the body would need a marker in the markdown, and that marker would be a second way
    to express an instruction — competing directly with the frozen `sections:` contract, whose
    entire purpose is that every instruction gets a number and a pin. A body sentence saying "go
    and do X" gets neither. Written into the schema contract on the Technical page rather than
    into code, because there is nothing here for code to enforce that would not first have to
    guess which sentences are instructions.

56. **The step legend is suppressed where the section has no pins.** `MapViewer`'s `steps` prop
    drew the "1 — Walkthrough step" key, and the empty "Numbered steps" row in the layer control,
    whenever it was set at all — including for a section whose steps all lack an `at:`, which
    draws no pins. That is a key to a symbol that is not on the map. Only the caller can know, so
    the caller passes `null`. It changes nothing on this chapter, where all nine sections carry
    pins; proved on a temporary edit that removed the last section's only `at:` — 9 viewers, 8
    legends, 8 `data-steps` — and the chapter restored byte-identical (`07a6cc09…` both sides).

## 2026-08-07 — M5 prerequisites

57. **The extractors invoke the preprocessor as `cc -E`, not as `cpp`, and pass joined include
    flags.** The repo moved to a macOS checkout and three extractors — `Species`, `Items`,
    `BattleData` — died on a command line that is correct, in two different ways, neither of
    which names its own cause.

    `-I include` separated: Apple's driver takes the directory as a linker input and drops the
    real input file, reporting `cc: error: no input files`. Joined (`-Iinclude`) is what both
    toolchains agree on.

    `cpp`: `/usr/bin/cpp` runs clang in **traditional** mode, where `//` is not a comment. The
    game writes its config as `#define P_MEGA_EVOLUTIONS TRUE // If TRUE, …`, so the comment
    becomes part of the macro body and every `#if` over it fails with "invalid token at start of
    a preprocessor expression". The conditional stack then desynchronises and clang reports
    `#else after #else` and `#endif without #if` **in `include/constants/global.h`, a header that
    is perfectly well formed** — so the first error, and the loudest one, points at the wrong
    file entirely. `cc -E` is modern-mode on both toolchains and keeps the `# lineno "file"`
    linemarkers that `Preprocessed` maps offsets through.

    **The proof that this is a portability fix and not a change of meaning is determinism.** All
    eight files in `data/generated/` rebuild byte-identical to the ones committed from CI's
    Ubuntu runner — `git status data/generated/` is empty after a full run, and `--check-determinism`
    reports 0 changed. The guide is still a pure function of the game version; it is now a pure
    function of it on two operating systems.

58. **The frozen `sections:` contract has a reader that is not a person, and it lives in
    `tools/qa/`, not `tools/validate/` where deferred B3 filed it.** The schema was designed so
    authoring errors are _detectable_ and then nothing detected them: `src/Steps.ts` opens with
    "bad content degrades, it never throws", which is the right rule for a renderer and no rule
    at all for the author. A group of one, a `choice` with no `choice_group`, a `choice_group`
    with no `choice`, a mistyped `at:` — every one renders as an ordinary step and looks like a
    page that simply did not say what you meant.

    **It is Node because the rules must not be copied.** `tools/qa/Chapters.mjs` imports
    `stepsOf` from `src/Steps.ts` and reads its runs back off the renderer's own maximal-run
    pass, so what it reports is the grouping the page will actually draw. A Python re-implementation
    would be a second copy of the thing under test, and this repo has paid that bill twice —
    `slugOf()` drifting from its copy in `Links.mjs` produced 486 phantom orphans, and the
    base-form rule drifted across three copies until decision 29 deleted two. `tools/validate/`
    checks EXTRACTED data and has no TypeScript to defer to; this checks hand-written content
    against code, so it defers to the code. Frontmatter is read with `js-yaml`, which is what
    `@astrojs/markdown-remark` reads it with — promoted from a transitive dependency to a
    declared one rather than relying on a hoist.

    Deferred **B5** rides along, because it is the same class: a section `id` goes raw into a DOM
    id, into `map-<id>`, into a `querySelector` and into a URL fragment, and two sections sharing
    one hands the second viewer the FIRST section's pins. So do `title`, `text`, and a `map:` that
    is not in the manifest — that last one as a warning, since rendering a section with no map is
    a legal decision and only indistinguishable from a typo.

    **The fixture table is the point.** Eighteen constructed chapters, one per rule, run in the
    same invocation: every rule is proved to fire on content that breaks it and the healthy
    fixture is proved silent, with the count asserted too so a rule that fires twice fails there
    rather than in a chapter. `Checklist.mjs` learned this the hard way — its assertion for shape
    six sat green because no shape in its table exercised it, and review found the bug instead.

59. **Deferred B7 is checked in the emitted HTML, because that is the only place it exists.**
    `ol.steps > li::before` renders `counter(step)`; `li[data-step]::before` overrides it with
    `attr(data-step)`; `MapViewer` queries `li[data-step][data-at]`. A step that renders without
    `data-step` therefore still shows a number — the counter's — while the pin script skips it,
    and from there the badges and the pins are numbering two different lists. No source check can
    see this. Both branches were proved by mutating the built page: dropping `data-step` from
    `viridian-city` item 3 and setting it to `9` out of position each produce one error, and the
    page was restored byte-identical (`45047b09…` both sides). The summary line was rewritten
    mid-verification because it printed "data-step present and in order" **while reporting an
    error underneath it** — the fourth instance in this repo of a harness claiming something
    other than what it measured.

60. **The homepage no longer asserts in prose what it can read off the content.** It said "Pick
    Kanto first — it is the region this guide walks you through, and so far the only one with a
    written chapter". `groups` is already filtered to regions that have at least one chapter and
    is in play order, so the region named is now `groups[0]` and the "only one" clause is printed
    only while `groups.length === 1`. Deferred B6, and it was going wrong on the day M5 lands its
    first Johto file — silently, on the homepage, in a sentence telling a new reader where to
    start.

61. **The footer carries both repos and the author's credit.** The guide is only half the project:
    the commit named in the footer is a commit in the GAME repo, and the extractors that read it
    are in the GUIDE repo, so the two links are a pair. The credit is the MadeWithLove bezel,
    ported verbatim in its small variant — the one the archive's own footer demo uses and the one
    every other site of his carries — rather than restyled into this site's palette, because the
    point of a signature is that it is the same everywhere. VT323 is not vendored and this site
    loads no external fonts, so the stack falls through to the platform monospace. In print the
    bezel is stripped to plain text and the blinking cursor is dropped: a phosphor chip prints as
    a black box, and a filled block prints solid to cue an animation that paper does not have.
    Both links are external, so `Links.mjs` does not check them — if either repo ever moves,
    nothing in the gate will notice.

## 2026-08-08 — groups C and D

62. **The step pins leave the tab order rather than being made navigable inside it, and their
    tooltips stop going through `innerHTML`.** Deferred D17 and D21.

    **The fix D17 proposed does not work.** It said "`L.marker`'s `alt` fixes it"; Leaflet only
    assigns `alt` when the icon element is an `<img>`, and every pin here is a `divIcon`. Setting
    it would have shipped, changed nothing, and closed the item. What Leaflet actually does is set
    `tabIndex = 0` and `role="button"` whenever `options.keyboard` is true, which is the default —
    so a chapter handed a keyboard user 37 stops, each announced as its own numeral: "3, button".

    **They are gone from the tab order, not renamed within it.** A pin's entire behaviour is to
    scroll to its step, and that step is the next thing in the document: the `<ol>` under the map
    carries the same numeral and the same sentence in reading order. The pin adds POSITION, which
    is the one thing a tab stop cannot convey. Keeping 37 stops to reach content already reachable
    is cost with no function. They keep `role="img"` and an `aria-label` of "Step N: <sentence>",
    because a pin is still in the accessibility tree and a bare "3" describes nothing; `aria-label`
    and not `title`, which would raise a second native tooltip beside Leaflet's own. The attributes
    are set on the marker's `add` event, since `getElement()` is null until it is on the map.
    Measured on the chapter: 37 pins, 0 with `tabindex`, 0 with `role="button"`, 37/37 named.

    `bindTooltip(String)` assigns through `innerHTML`. Twelve lines above it a comment states that
    the numeral is set with `textContent` "never innerHTML", and the tooltip on the same marker
    was quietly doing the opposite. It takes an element now. Not a vulnerability — every step is
    repo-authored — but a step reading "walk to the < shaped rock" lost the rest of its sentence
    with no error anywhere, and M5 writes 45–58 chapters of sentences. Proved by inserting
    `<b>odd</b>` into a step before its viewer mounted: the tooltip reads it back as characters
    and its `innerHTML` contains no `<b>`.

63. **A map that cannot mount shows the map anyway.** Deferred D20. With the script off the viewer
    never mounts, and the box holds its own aspect ratio regardless — so a chapter reserved nine
    780×480 voids, about 4,300px of nothing, between prose the reader could otherwise follow. Each
    viewer now carries a `<noscript>` still of **the same PNG Leaflet would have tiled in**: it is
    already built, already deployed, and inside `<noscript>` it is not fetched at all by readers
    whose script does run. One rule in `Base.astro`, once per page rather than once per viewer,
    collapses the empty box.

    Verified with JavaScript actually disabled rather than simulated: 9 stills present, the
    `.pw-viewer` box gone entirely, the first still laying out at 780×562. **The chapter gets
    taller — 13,417px against 11,948 with the script — and that is the fix working**, not failing:
    the height is maps now instead of nothing.

    A side effect worth recording, because it is free coverage nobody asked for: the stills put
    every map PNG into the HTML as an `<img src>`, so `Links.mjs` checks them. Internal links
    23,886 → **25,090**, and the +1,204 is exactly 1,195 map pages plus the chapter's 9 sections.
    Leaflet fetches those images at runtime, where the link checker has never been able to see
    them; a rendered map that failed to deploy would previously have been caught by nobody.

64. **The `/maps` filter keeps matching loosely and starts answering precisely.** Deferred D22.
    Typing "route1" returned 101 hits, because route10 and route11 and all their interiors do
    contain "route1". Nothing was wrong with the matching and hiding those would be worse — what
    was wrong is that the map the reader asked for sat somewhere inside an alphabetical hundred.
    The substring stays; the ORDER carries the precision. Exact name or slug first, then the ones
    that start with the query, then everything else, each rank holding its alphabetical run.
    "route1" still returns 101 and now opens with Route 1; "viridian" opens with Viridian City.
    Clearing the box restores the rendered order exactly, which is a stronger promise than a
    stable sort.

    **Reordered in the DOM, not with CSS `order`.** `order` moves the paint and leaves the tab
    sequence where it was, so a keyboard user would tab the old hundred underneath a visibly
    re-sorted list — WCAG 1.3.2, and precisely the shape of defect this pass exists to remove. It
    would also have looked completely fixed in a screenshot.

65. **Two places where the page said the same thing twice, and one where it said it faintly.**
    Deferred D23 and D24. An open `.peek` carried `opacity: 0.7` on the whole control, which faded
    the revealed text — the one thing the reader pressed it to see — to roughly 4.5:1 where the
    prose around it sits near 12:1. The cue that a spoiler is open is its border going solid, so
    the dimming moved to the border alone through `color-mix`, with the flat accent declared first
    as the fallback for an engine that does not know the function. Computed opacity on the open
    control is 1.

    `TrainerCard` printed the trainer's name two lines under a fold summary that had just printed
    it. It takes `showName` now, defaulting to true — M5's 24 boss pages are standalone cards and
    must still say whose party they are — and the map page passes false. `name` stays required
    either way; making it optional would let a boss page ship an anonymous team.

66. **The homepage stops promising the reader they can always leave.** Deferred C15. It said the
    Hub Pass "warps you back to the hub whenever you want, so you are never stuck in the region you
    picked". `CannotUseHubReturnHere()` blocks it in the Safari Zone, the Bug Contest, link and
    union rooms, and Frontier or Trainer Hill runs. None is reachable on turn one, which is why the
    sentence survived this long — but the guide is read by someone deciding whether it is safe to
    commit to a region, and a promise that fails only in the places you cannot leave is the worst
    possible shape for it to fail in.

67. **Two of group C's four items were already done, and the record said otherwise.** C13 claimed
    encounter tables render in source order so DexNav can sit above Tall Grass: `byMethod` has been
    sorting on `METHOD_LABEL`'s key order — land, water, rock_smash, fishing, hidden — with `byRod`
    doing old/good/super one level down, and Route 10 renders exactly that. C14 claimed
    `wildSpecies` counts include disabled slots: decision 39 removed that count from the heading
    entirely, and this pin has 0 disabled slots, so there is no number left to be wrong. Both are
    struck with the evidence rather than deleted. **This is the third time a deferred list has sent
    someone at work that was already finished or, in D17's case, at a fix that does not work — read
    the code before the entry.**

68. **The banner is the lid of the Pokédex; everything below the hinge seam is the page.**
    The guide reads as a device you are holding open to a printed spread, not as a device
    with a screen in it. The shell is FRAME ONLY: `src/styles/Guide.css` restyles `.banner`
    and its nav into red plastic, a lens and three lamps, and touches nothing else. Type,
    tables, folds, maps, spoilers, checklists and page width are exactly what decisions 14
    and 15 made them, at full width, with no bezel.

    **This does not weaken decision 14, it extends it.** No new hue enters the palette: the
    shell is `--trainer` shaded five ways, and the three lamps carry `--item`, `--hidden`
    and `--warp` — the three marker colours the shell itself is not. So the lid states the
    whole map palette without a legend, which is what decision 14 asks colour to do.

    The amber lamp is not decoration: it reports whether spoilers are revealed, driven from
    the same `sync()` that writes the reveal button's label, because two readouts that can
    disagree are worse than one. Its lit state is a WHITE core, not a halo — an amber bloom
    over red-orange plastic was measured at 4× and was indistinguishable from unlit.

    **The seam is a border, not a shadow.** `Base.astro` publishes the banner height from
    `getBoundingClientRect()`, which counts borders and ignores shadows, so a shadow seam
    would desynchronise `--banner-h` from the rendered banner and tuck every sticky
    walkthrough map under it. The 4px seam also moved the desktop banner from 49.5px to
    54px, which is why the `var(--banner-h, …)` fallbacks in the walkthrough page are now
    `3.375rem`. `tools/qa/Chrome.mjs` fails the build if the constant and the rendered
    banner ever disagree.

    **On a phone the shell subtracts.** The banner is sticky, so its height is gone from
    every screen of every page; six nav controls wrapping onto three rows cost 126px at
    390px. Below 700px the lens and two lamps are dropped and the nav becomes one row that
    scrolls inside itself — 85px, a 41px saving on every page. The wrap it replaces existed
    to stop the nav setting the document's scroll width (decision 14's neighbour, the
    comment at `Guide.css:98`); `overflow-x` on the nav preserves that property by a
    different mechanism, and `tools/qa/Chrome.mjs` now asserts it rather than trusting it.

    Cost: the red is the loudest thing above the fold on every page, and the amber nameplate
    now sits on red rather than on near-black. Rejected alternatives: a full LCD treatment of
    the content (fights a 1180px aerial map and rewrites decision 15), and a restrained
    seam-only shell (its device read did not survive the mobile cut, which is where it
    mattered most).
