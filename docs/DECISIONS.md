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

12. **`Testing/ValidateGen13.py` joins `tools/validate/`.** It is absent at `v1.3.6` but present
    and passing at the new pin, and it is the game's own invariant check — no obtainable content
    references a stripped family, and every Gen 4+ family is stripped. Cheaper and more
    authoritative than reimplementing the same check in the guide.
