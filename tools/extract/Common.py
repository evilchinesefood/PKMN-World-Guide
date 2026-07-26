"""Shared foundation for every extractor. See docs/DATA-AUDIT.md and docs/SCHEMAS.md."""

import json, os, re, functools

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
GAME = os.path.join(ROOT, "game")
OUT = os.path.join(ROOT, "data", "generated")
MANIFEST = os.path.join(ROOT, "data", "manifest")


def g(*p):
    return os.path.join(GAME, *p)


def load(*p):
    with open(g(*p), encoding="utf-8") as f:
        return json.load(f)


def read(*p):
    with open(g(*p), encoding="utf-8", errors="replace") as f:
        return f.read()


# --- region ------------------------------------------------------------------
# The ONE place the region rule lives. Replicates GetRegionForSectionId in
# include/regions.h. Do not reimplement this anywhere else, and do not use
# map.json's `region` field: it is absent on every Johto map and disagrees with
# runtime on the 5 FRLG link rooms. See DATA-AUDIT.md 2.1.

NEUTRAL_MAPSECS = {"MAPSEC_DYNAMIC", "MAPSEC_SECRET_BASE", "MAPSEC_SPECIAL_AREA"}


@functools.lru_cache(maxsize=1)
def mapsec_order():
    d = load("src", "data", "region_map", "region_map_sections.json")
    secs = d["map_sections"] if isinstance(d, dict) else d
    return {s["id"]: i for i, s in enumerate(secs)}


@functools.lru_cache(maxsize=1)
def _bounds():
    o = mapsec_order()
    # Kanto's upper bound is EXCLUSIVE of MAPSEC_SPECIAL_AREA. KANTO_MAPSEC_END is
    # deliberately inclusive of it for the map-name popup; using it here is a bug.
    return (
        o["MAPSEC_PALLET_TOWN"],
        o["MAPSEC_SPECIAL_AREA"],
        o["MAPSEC_NEW_BARK_TOWN"],
        o["MAPSEC_JOHTO_INDIGO_PLATEAU"],
    )


def region_of_mapsec(sec):
    if sec in NEUTRAL_MAPSECS:
        return "shared"
    i = mapsec_order().get(sec)
    if i is None:
        return None
    k0, kend, j0, j1 = _bounds()
    if k0 <= i < kend:
        return "kanto"
    if j0 <= i <= j1:
        return "johto"
    return "hoenn"


def region_of_map(m):
    return region_of_mapsec(m.get("region_map_section"))


# Kanto splits further: the Sevii Islands are ~38% of all Kanto maps and get their own atlas
# views. The mapping is parsed out of sKantoSubregionMapsecs in src/regions.c rather than
# hand-listed, so it tracks the source if islands are added or moved.
@functools.lru_cache(maxsize=1)
def kanto_subregions():
    txt = read("src", "regions.c")
    body = txt[txt.index("sKantoSubregionMapsecs") : txt.index("enum KantoSubRegion GetKantoSubregion")]
    out = {}
    for m in re.finditer(r"\[(KANTO_SUBREGION_\w+)\]\s*=\s*\{(.*?)\}", body, re.S):
        name = m.group(1)[len("KANTO_SUBREGION_") :].lower()
        for sec in re.findall(r"MAPSEC_\w+", m.group(2)):
            if sec != "MAPSEC_NONE":
                out[sec] = name
    return out


def subregion_of_map(m):
    """`sevii123` / `sevii45` / `sevii67` for Sevii maps, else None."""
    if region_of_map(m) != "kanto":
        return None
    return kanto_subregions().get(m.get("region_map_section"))


# --- maps and layouts --------------------------------------------------------


@functools.lru_cache(maxsize=1)
def maps():
    out = {}
    d = g("data", "maps")
    for name in sorted(os.listdir(d)):
        p = os.path.join(d, name, "map.json")
        if os.path.isfile(p):
            with open(p, encoding="utf-8") as f:
                m = json.load(f)
            m["_dir"] = name
            out[m["id"]] = m
    return out


@functools.lru_cache(maxsize=1)
def layouts():
    return {l["id"]: l for l in load("data", "layouts", "layouts.json")["layouts"]}


def live_layout_ids():
    return {m["layout"] for m in maps().values() if m.get("layout")}


# --- record helpers ----------------------------------------------------------


def source(file, key=None, line=None):
    return {"file": file, "key": key, "line": line}


def gap(field, reason, audit=None):
    return {"field": field, "reason": reason, "audit": audit}


# --- text --------------------------------------------------------------------
# Decodes in-game strings for HTML. See DATA-AUDIT.md 5B.11.
# `\p` splits paragraphs, `\n` and `\l` are line breaks within one box, `$` ends.
# POKe's accented e is a real charmap glyph and is kept.

_TOKENS = {
    "{PKMN}": "Pokémon",
    "{POKEBLOCK}": "Pokéblock",
    "{PLAYER}": "{PLAYER}",
    "{STR_VAR_1}": "…",
    "{STR_VAR_2}": "…",
    "{STR_VAR_3}": "…",
    "{KUN}": "",
    "{NAME_END}": "",
    "{PAUSE_UNTIL_PRESS}": "",
}
_DROP = re.compile(r"\{(COLOR|HIGHLIGHT|SHADOW|FONT|TEXT_COLORS|CLEAR|CLEAR_TO|SKIP)[^}]*\}")


def decode_text(s):
    """Returns a list of paragraphs, each a list of lines."""
    s = s.rstrip("$")
    s = _DROP.sub("", s)
    for k, v in _TOKENS.items():
        s = s.replace(k, v)
    return [[ln for ln in para.replace("\\l", "\\n").split("\\n")] for para in s.split("\\p")]


def text_to_html(s):
    paras = decode_text(s)
    import html

    return "".join(
        "<p>" + "<br>".join(html.escape(ln.strip()) for ln in p) + "</p>" for p in paras if any(p)
    )


def assert_decoded(s):
    """Guard: no residual escapes or unexpanded tokens should survive decoding."""
    bad = re.findall(r"\\[a-zA-Z]|\{[A-Z_0-9]+\}", s)
    return [b for b in bad if b != "{PLAYER}"]


# --- output ------------------------------------------------------------------


def write(name, payload, where=None):
    """Deterministic: sorted keys, fixed separators, trailing newline, no timestamps."""
    d = where or OUT
    os.makedirs(d, exist_ok=True)
    p = os.path.join(d, name)
    with open(p, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=1, sort_keys=True, ensure_ascii=False)
        f.write("\n")
    return p


def game_commit():
    # game/.git is a real dir when the submodule was cloned before `submodule add`,
    # and a gitfile pointing into .git/modules/game otherwise. Handle both.
    d = os.path.join(GAME, ".git")
    if os.path.isfile(d):
        with open(d) as f:
            d = os.path.normpath(os.path.join(GAME, f.read().split(":", 1)[1].strip()))
    try:
        with open(os.path.join(d, "HEAD")) as f:
            v = f.read().strip()
        if not v.startswith("ref:"):
            return v
        with open(os.path.join(d, v[5:].strip())) as f:
            return f.read().strip()
    except OSError:
        return None


def header():
    return {"game_commit": game_commit()}
