# PKMN-World-Guide

A complete strategy guide for **[Pokémon World](https://github.com/evilchinesefood/PKMN-World)**, a GBA
ROM hack built on pokeemerald-expansion that merges Kanto, Johto and Hoenn into one game.

Modelled on the printed guides of the late 90s and early 2000s — aerial maps with numbered callouts,
every hidden item marked, every trainer's full party, complete walkthroughs, boss strategy pages and
sidebars. The difference is that this site is **generated from the game's own source**, so it can be
exhaustive and stay correct across releases.

## How it works

The game repo enters here as a read-only git submodule at `game/`, pinned to a release tag. Python
extractors under `tools/extract/` read that source and emit deterministic JSON to `data/generated/`.
An Astro site renders those files. Nothing in `data/generated/` is ever hand-edited — if the output is
wrong, the extractor is wrong.

| Path | What it is |
| --- | --- |
| `game/` | submodule, pinned tag, read only — never modified by this repo |
| `tools/extract/` | Python extractors, one module per entity |
| `tools/validate/` | completeness and integrity checks; generates `docs/COMPLETENESS.md` |
| `tools/porymap/` | export helper scripts + checklist generator |
| `data/generated/` | extractor output, committed |
| `data/manifest/` | `map-manifest.json` — the interface between map images and the site |
| `content/` | hand-written markdown (walkthroughs, strategy) |
| `src/` | Astro site |
| `public/maps/` | exported map PNGs |
| `docs/` | `DATA-AUDIT.md`, `SCHEMAS.md`, `COMPLETENESS.md`, `DECISIONS.md` |

## Status

**M0 — Audit.** See [`docs/DATA-AUDIT.md`](docs/DATA-AUDIT.md).

## Disclaimer

Non-commercial and ad-free. This is a fan project. Pokémon and all related names are trademarks of
Nintendo, Creatures Inc. and GAME FREAK Inc. This repository contains no ROM, no build artifacts and
no base ROM, and never will. Nothing here is affiliated with or endorsed by Nintendo.
