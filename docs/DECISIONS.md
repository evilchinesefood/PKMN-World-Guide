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
    only real question is which occurrence pays for it. The first is the one that may already be
    ticked in a reader's browser, and a chapter that _gains_ a duplicate must not silently reset
    the line that was always there. Suffixing every occurrence, including the first, was rejected
    for exactly that: it would make adding a duplicate reset an unrelated tick.

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
    rendered a page that looked correct and did the wrong thing. Anything added here should be
    assumed to have a sixth shape until the markdown that produces it has been enumerated.
