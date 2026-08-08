--[[ Capture.lua -- loaded ONCE from mGBA's Tools > Scripting > Load Script..., with a ROM
already open. Reads tools/mgba/shots.json, and for each entry loads a savestate, advances a
fixed number of frames, and writes public/screenshots/<id>.png plus a manifest recording what
it did. There is no other automation surface: mGBA 0.10.5's --help has no flag that loads a
script, none that runs headless, and none that bounds a run by frame count (see the CLI
findings in the M6 task brief) -- so this file, run by hand from the GUI, IS the tool.

WHAT IS ACTUALLY PROVEN HERE, AND HOW. This script has never been executed inside mGBA: there
is no ROM and no savestate on the machine that wrote it, and the GUI's scripting console cannot
be driven from that environment. Every claim below about mGBA's own runtime behaviour is sourced
from reading mgba-emu/mgba's tagged v0.10.5 release (commit 26b7884, the exact commit `git
describe`/the releases API resolves 0.10.5 to), not from running it. Treat the citations as
"the shipped source says this", not "this was seen to work".

  - A script's OWN DIRECTORY. Nothing in mgba.io/docs/scripting.html documents a `script`
    global, an `arg`, or any getScriptDir()-shaped call -- the API reference lists only
    C, callbacks, console, util, emu and socket, and none of them expose the loaded file's
    path. Guessing at a plausible-sounding call here is exactly the mistake this task is
    supposed to avoid, so this reaches for something verifiable instead: plain Lua's
    debug.getinfo. src/script/engines/lua.c:837-869 (_luaLoad) builds the chunk name it
    hands to lua_load as "@" followed by whatever filename it was given, and
    src/platform/qt/scripting/ScriptingView.cpp:60 shows that filename comes straight from
    Qt's file-open dialog (GBAApp::getOpenFileName), which returns an absolute path.
    ScriptingController.cpp:63-71 passes that path through unchanged. So inside the running
    script, `debug.getinfo(1, "S").source` is "@<absolute path to this file>" -- ordinary
    Lua stack introspection, not an mGBA API, applied to a fact about mGBA's loader that
    only the source confirms.
  - That `debug`, `io` and `os` are even present to call. src/script/engines/lua.c:385 calls
    luaL_openlibs() unconditionally when a script context is created, and nothing later in
    that file removes a library or a global -- no sandboxing pass, no stripped `_G`. That is
    what makes reading shots.json with io.open possible, and would make shelling out to
    create public/screenshots/ with os.execute possible too -- deliberately not done here,
    see below.
  - emu:loadStateFile(path) returns a real boolean. src/core/scripting.c:393-401
    (_mScriptCoreLoadStateFile) opens the file itself and returns false if that open fails,
    before mGBA ever touches the emulated state -- so checking its return value catches a
    missing savestate.
  - emu:screenshot(path) does NOT. It is declared as a bare `void` script method
    (src/core/scripting.c:466), and its implementation (_mScriptCoreTakeScreenshot,
    lines 402-413) is `if (!vf) { return; }` on a failed VFileOpen -- no error, no log, no
    signal of any kind reaches Lua. THE CONCRETE FAILURE THIS FILE EXISTS TO AVOID: a script
    that calls emu:screenshot(path) and moves on believes it succeeded whenever
    public/screenshots/ doesn't exist yet, and produces a manifest describing PNGs that were
    never written. This script therefore re-opens every path it just asked emu:screenshot to
    write and checks it is there and non-empty (see the readback in captureShot, below) --
    that check is the only place this failure becomes visible, because mGBA will not report it.
  - The top-level chunk runs inside a real lua_pcall (src/script/engines/lua.c:987, called
    from _luaRun via _luaInvoke), so a plain Lua `error()` call aborts the rest of the script
    and mGBA surfaces the message as a console error -- the same path _luaError itself uses.
    That is why this file calls `error()` rather than logging and carrying on: a shot that
    fails must stop the run, not leave a partial manifest next to shots it never got to.
  - `emu` is nil until a ROM is loaded. Documented as "CoreAdapter instance available when a
    game is loaded", and confirmed by mGBA's own bundled scripts/pokemon.lua, which guards
    its own startup with `if emu then detectGame() end`.

WHAT IS NOT ADDRESSED, ON PURPOSE. public/screenshots/ is required to already exist rather
than created here. Creating it would mean shelling out (os.execute("mkdir -p ...")) since
standard Lua has no mkdir and mGBA does not bundle LuaFileSystem -- os.execute is confirmed
present (see above) but whether the packaged macOS .app's process is free to spawn a shell
was never exercised, and this task's whole premise is to stop guessing at the boundary of what
was actually checked. Requiring the directory up front and failing with the OS's own error
text if it is missing or unwritable is simpler, and the failure is exactly as loud either way.

DETERMINISM, HONESTLY. Two runs with the same shots.json produce byte-identical PNGs ONLY to
the extent that "same savestate, same frame count" pins the game's state -- which is not very
far. A savestate freezes RNG seed and every counter at the instant it was made, but anything
the game advances on a wall-clock-independent per-frame timer (tile animations, water
shimmer, flickering signs, NPC walk cycles) is still ticking during the fixed frame-advance
below, and two captures that ask for the same frame count from the same savestate will still
show that timer at whatever phase 60 (or however many) frames happens to land on -- which is
reproducible run-to-run on this machine, but not something this file can claim matches a
frame count picked to "look right" once and never re-derived. This is screenshotting, not the
sprite/map extractors' from-source rendering: it is only as deterministic as "fixed inputs,
same emulator build", not "recomputed from source every time".

shots.json's SCHEMA IS VALIDATED ELSEWHERE, ON PURPOSE. tools/mgba/Check.py is the schema
authority (unique ids, kebab-case shape, non-empty savestate, positive integer frames, no
output-path collisions) precisely so this file does not carry a second, drifting copy of
those rules -- the same reasoning tools/qa/Chapters.mjs gives for not re-implementing its
rules in Python. This file still guards the few things that would misdirect an mGBA call
(nil id, wrong-typed savestate/frames) rather than trust an unchecked file blindly, but a
maintainer should run Check.py first; the error messages below say so.
]]

local function dirname(path)
	return path:match("^(.*)[/\\][^/\\]*$")
end

-- The one place this file reads its own location. See the docstring's first citation.
local function scriptDir()
	local source = debug.getinfo(1, "S").source
	local path = source:sub(1, 1) == "@" and source:sub(2) or source
	local dir = dirname(path)
	if not dir then
		error("Capture.lua: debug.getinfo did not return a file path ('" .. tostring(source) ..
			"'). This script must be loaded from a .lua file on disk, not typed into the console.", 0)
	end
	return dir
end

local SCRIPT_DIR = scriptDir()
-- tools/mgba -> tools -> repo root: the same two hops up that tools/extract/Common.py takes
-- from its own containing directory (tools/extract) to reach C.ROOT.
local ROOT = dirname(dirname(SCRIPT_DIR))
local OUTDIR = ROOT .. "/public/screenshots"
local SAVESTATE_DIR = SCRIPT_DIR .. "/savestates"

local function fail(msg)
	-- Level 0: the message is already specific about where it came from, and Lua's own
	-- "input:N:" prefix would just be the line inside this file, never the shot at fault.
	error("Capture.lua: " .. msg, 0)
end

-- --- a JSON reader, because none is bundled ----------------------------------------------
-- mGBA's Lua API surface (C, callbacks, console, util, emu, socket) has no JSON decoder, and
-- the standard library that luaL_openlibs opens does not include one either. This is a real,
-- general recursive-descent JSON parser rather than a regex that assumes shots.json's exact
-- current formatting -- the lesson this repo's extractors keep re-learning (see the #if trap
-- in tools/sprites/Extract.py) is that a format-shaped scan breaks the moment the format's
-- shape changes, silently. \u escapes are only supported below U+0080: nothing this file's
-- schema needs (kebab-case ids, filenames) is outside plain ASCII, and pretending to handle
-- wider code points without a real UTF-8 encoder would be exactly the kind of "looks done"
-- shortcut this task is meant to avoid.

local function jsonDecode(text)
	local i, n = 1, #text

	local function err(msg)
		error("shots.json: " .. msg .. " at byte " .. i, 0)
	end

	local function skipWs()
		while i <= n do
			local c = text:sub(i, i)
			if c == " " or c == "\t" or c == "\n" or c == "\r" then
				i = i + 1
			else
				break
			end
		end
	end

	local parseValue

	local function parseString()
		i = i + 1 -- opening quote
		local parts = {}
		while true do
			if i > n then err("unterminated string") end
			local c = text:sub(i, i)
			if c == '"' then
				i = i + 1
				return table.concat(parts)
			elseif c == "\\" then
				local e = text:sub(i + 1, i + 1)
				local simple = { ['"'] = '"', ["\\"] = "\\", ["/"] = "/", b = "\b", f = "\f", n = "\n", r = "\r", t = "\t" }
				if simple[e] then
					parts[#parts + 1] = simple[e]
					i = i + 2
				elseif e == "u" then
					local hex = text:sub(i + 2, i + 5)
					local code = tonumber(hex, 16)
					if not code then err("bad \\u escape") end
					if code >= 0x80 then
						err("\\u escape above U+007F is not supported (no UTF-8 encoder here; " ..
							"this file's schema is plain ASCII)")
					end
					parts[#parts + 1] = string.char(code)
					i = i + 6
				else
					err("unknown escape \\" .. e)
				end
			else
				parts[#parts + 1] = c
				i = i + 1
			end
		end
	end

	local function parseNumber()
		local start = i
		if text:sub(i, i) == "-" then i = i + 1 end
		while i <= n and text:sub(i, i):match("%d") do i = i + 1 end
		if text:sub(i, i) == "." then
			i = i + 1
			while i <= n and text:sub(i, i):match("%d") do i = i + 1 end
		end
		if text:sub(i, i) == "e" or text:sub(i, i) == "E" then
			i = i + 1
			if text:sub(i, i) == "+" or text:sub(i, i) == "-" then i = i + 1 end
			while i <= n and text:sub(i, i):match("%d") do i = i + 1 end
		end
		local num = tonumber(text:sub(start, i - 1))
		if not num then err("invalid number") end
		return num
	end

	local function parseArray()
		i = i + 1
		local out = {}
		skipWs()
		if text:sub(i, i) == "]" then
			i = i + 1
			return out
		end
		while true do
			skipWs()
			out[#out + 1] = parseValue()
			skipWs()
			local c = text:sub(i, i)
			if c == "," then
				i = i + 1
			elseif c == "]" then
				i = i + 1
				return out
			else
				err("expected ',' or ']' in array")
			end
		end
	end

	local function parseObject()
		i = i + 1
		local out = {}
		skipWs()
		if text:sub(i, i) == "}" then
			i = i + 1
			return out
		end
		while true do
			skipWs()
			if text:sub(i, i) ~= '"' then err("expected a string key") end
			local key = parseString()
			skipWs()
			if text:sub(i, i) ~= ":" then err("expected ':' after key") end
			i = i + 1
			skipWs()
			out[key] = parseValue()
			skipWs()
			local c = text:sub(i, i)
			if c == "," then
				i = i + 1
			elseif c == "}" then
				i = i + 1
				return out
			else
				err("expected ',' or '}' in object")
			end
		end
	end

	parseValue = function()
		skipWs()
		local c = text:sub(i, i)
		if c == '"' then
			return parseString()
		elseif c == "{" then
			return parseObject()
		elseif c == "[" then
			return parseArray()
		elseif c == "-" or c:match("%d") then
			return parseNumber()
		elseif text:sub(i, i + 3) == "true" then
			i = i + 4
			return true
		elseif text:sub(i, i + 4) == "false" then
			i = i + 5
			return false
		elseif text:sub(i, i + 3) == "null" then
			i = i + 4
			return nil
		else
			err("unexpected character '" .. c .. "'")
		end
	end

	skipWs()
	local value = parseValue()
	skipWs()
	if i <= n then err("trailing data after the JSON value") end
	return value
end

-- --- filesystem helpers -------------------------------------------------------------------

local function readFile(path)
	local f, openErr = io.open(path, "rb")
	if not f then return nil, openErr end
	local content = f:read("*a")
	f:close()
	return content
end

-- Probing with a real write is the only way to learn "unwritable" from Lua: there is no
-- stat()/access() in the standard library, and mGBA does not bundle LuaFileSystem. A failed
-- open also covers "the directory does not exist at all", with the OS's own reason attached.
local function checkOutdirWritable()
	local probe = OUTDIR .. "/.capture-write-test"
	local f, openErr = io.open(probe, "wb")
	if not f then
		fail(("output directory %s is not writable (%s). Create it first -- this script " ..
			"does not create it for you; see the docstring for why."):format(OUTDIR, tostring(openErr)))
	end
	f:close()
	os.remove(probe)
end

local function jsonEscape(s)
	return (s:gsub('[%c"\\]', function(c)
		if c == '"' then return '\\"'
		elseif c == "\\" then return "\\\\"
		elseif c == "\n" then return "\\n"
		elseif c == "\r" then return "\\r"
		elseif c == "\t" then return "\\t"
		else return string.format("\\u%04x", c:byte()) end
	end))
end

-- The output is small and fixed-shape (id, savestate, frames, image, always in that order),
-- so a hand-written writer is simpler and no less correct than round-tripping through a
-- generic encoder for a shape this file already knows completely.
local function writeManifest(entries)
	table.sort(entries, function(a, b) return a.id < b.id end)
	local lines = { "{\n", ' "generator": "tools/mgba/Capture.lua",\n', ' "shots": [\n' }
	for idx, e in ipairs(entries) do
		lines[#lines + 1] = string.format(
			'  {"id": "%s", "savestate": "%s", "frames": %d, "image": "%s"}%s\n',
			jsonEscape(e.id), jsonEscape(e.savestate), e.frames, jsonEscape(e.image),
			idx < #entries and "," or "")
	end
	lines[#lines + 1] = " ]\n}\n"

	local path = OUTDIR .. "/manifest.json"
	local f, openErr = io.open(path, "wb")
	if not f then
		fail(("cannot write %s (%s)"):format(path, tostring(openErr)))
	end
	f:write(table.concat(lines))
	f:close()
	return path
end

-- --- the run --------------------------------------------------------------------------

local function loadShots()
	local path = SCRIPT_DIR .. "/shots.json"
	local raw, readErr = readFile(path)
	if not raw then
		fail(("cannot read %s (%s)"):format(path, tostring(readErr)))
	end
	local ok, shotsOrErr = pcall(jsonDecode, raw)
	if not ok then
		fail(tostring(shotsOrErr))
	end
	if type(shotsOrErr) ~= "table" then
		fail("shots.json must decode to a JSON array of shot objects")
	end
	return shotsOrErr
end

-- Re-checks only what would misdirect the calls below (a nil/wrong-typed field feeding
-- loadStateFile or the frame-advance loop) -- shape, kebab-case, uniqueness and output-path
-- collisions are tools/mgba/Check.py's job, not duplicated here. See the docstring.
local function captureShot(shot, index)
	local id, savestate, frames = shot.id, shot.savestate, shot.frames

	if type(id) ~= "string" or id == "" then
		fail(("entry %d: `id` is missing or not a string -- run tools/mgba/Check.py"):format(index))
	end
	if type(savestate) ~= "string" or savestate == "" then
		fail(("%s: `savestate` is missing or not a string -- run tools/mgba/Check.py"):format(id))
	end
	if type(frames) ~= "number" or frames ~= math.floor(frames) or frames <= 0 then
		fail(("%s: `frames` is not a positive integer -- run tools/mgba/Check.py"):format(id))
	end

	local savestatePath = SAVESTATE_DIR .. "/" .. savestate
	local probe = io.open(savestatePath, "rb")
	if not probe then
		fail(("%s: no savestate at %s. Create it in mGBA (right-click the screen -> Save State) " ..
			"before running this script."):format(id, savestatePath))
	end
	probe:close()

	if not emu:loadStateFile(savestatePath) then
		fail(("%s: mGBA refused to load %s -- likely the wrong ROM revision, or a corrupt file.")
			:format(id, savestatePath))
	end

	for _ = 1, frames do
		emu:runFrame()
	end

	local outPath = OUTDIR .. "/" .. id .. ".png"
	emu:screenshot(outPath)

	-- The only place a failed screenshot becomes visible -- see the docstring's note on
	-- emu:screenshot's void, silently-no-op-on-failure C implementation.
	local written = io.open(outPath, "rb")
	if not written then
		fail(("%s: emu:screenshot() did not produce %s. It has no return value and does not " ..
			"report failure on its own -- this readback is the only check there is."):format(id, outPath))
	end
	local size = written:seek("end")
	written:close()
	if size == 0 then
		fail(("%s: %s was written but is 0 bytes."):format(id, outPath))
	end

	console:log(("Capture.lua: %s -> %s (%d frames from %s)"):format(id, outPath, frames, savestate))
	return { id = id, savestate = savestate, frames = frames, image = "screenshots/" .. id .. ".png" }
end

local function main()
	if not emu then
		fail("no ROM is loaded. Open the game first (File > Open...), then Tools > Scripting > " ..
			"Load Script to run this again.")
	end

	checkOutdirWritable()

	local shots = loadShots()
	local entries = {}
	for i, shot in ipairs(shots) do
		entries[#entries + 1] = captureShot(shot, i)
	end

	local manifestPath = writeManifest(entries)
	console:log(("Capture.lua: wrote %d screenshot(s) and %s"):format(#entries, manifestPath))
end

main()
