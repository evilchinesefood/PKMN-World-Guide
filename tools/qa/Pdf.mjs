// Print QA: prints a page and counts what landed in the PDF, instead of looking at it.
//
// DECISIONS.md 35 fixed a chapter that printed eight empty map boxes and closed with a rule --
// "Measure printed output by counting embedded image XObjects in the PDF. The preview lies." --
// but shipped no tool, so the 46 images and 573,354 bytes it records have been unreproducible
// since the day they were written, and decisions 35 and 36 rest on a measurement nobody can
// repeat. This is that tool. It does not reproduce 46 — the same chapter measures 100 images
// today, on a page that decisions 36-38 and M5 rebuilt underneath it — and the third bullet is
// why that is expected rather than a regression.
//
// WHY IT WALKS THE PAGE BEFORE PRINTING. The walk below is deliberately the same 600px/80ms one
// Shot.mjs does, so the two tools warm a page identically and their numbers can be compared.
// Shot.mjs's header explains the mechanism; the stakes are higher here. A chapter's map viewers
// mount on IntersectionObserver, so until something scrolls they are absent from the document
// rather than merely unpainted, and page.pdf() re-lays-out for print without ever scrolling.
// Skipping the walk therefore measures the COLD path -- the one decision 35 says printed 41 of
// 46 images -- while the output line claims the warm one. PDF_COLD=1 asks for cold deliberately;
// either way the line names the path, because the two numbers are not interchangeable and the
// interesting result is whether they still agree.
//
// WHAT `images` IS, AND WHAT IT IS NOT. It counts `/Subtype /Image` XObject dictionaries, which
// is decision 35's construction, and three things about that number are not obvious:
//
//   - Skia dedupes by content, so the chapter's nine <img> tags drawn from six distinct files
//     embed six images, not nine.
//   - A soft mask is itself an image XObject, so one PNG with alpha embeds as two.
//   - Skia rasterises composited CSS -- gradients, shadows, luminosity masks, page backgrounds
//     under printBackground -- into image XObjects with no <img> behind them. On the Kanto
//     chapter today that is 94 of 100. So the count answers "how many rasters did this print
//     embed", which is what decision 35 needed in order to tell a painted map from a black box,
//     and it is NOT "how many pictures a reader sees". It moves when the print stylesheet moves.
//
// Object dictionaries are plain text, but the streams between them are compressed binary that
// can spell anything, so the scan skips each stream by its declared /Length. proveCounter()
// shows that skipping is load-bearing rather than defensive: it embeds a JPEG whose comment
// segment carries the marker text, where a whole-file regex reports three images and there is
// one. The known hole is /Title, which Chromium copies from document.title verbatim into the
// plaintext Info dictionary -- a page titled "/Subtype /Image" would over-count by one.

import { chromium } from "playwright";

const IMAGE = /\/Subtype\s*\/Image\b/g;
// `/Pages` is the page-tree node, not a page; the lookahead is the whole reason for the regex.
const PAGE = /\/Type\s*\/Page(?![a-zA-Z])/g;
const MARKER = "/Subtype /Image";

const fail = (why) => {
  console.error(`Pdf.mjs is not measuring what it claims: ${why}`);
  process.exit(1);
};

// Everything outside `stream`/`endstream`, as one string. latin1 is one char per byte, so string
// offsets are byte offsets and no multi-byte decoding can shift a match.
function dictionaries(pdf) {
  const bytes = pdf.toString("latin1");
  const kept = [];
  const opener = /(?<![a-z])stream\r?\n/g; // the lookbehind is what stops `endstream` matching
  let cursor = 0;

  for (let m; (m = opener.exec(bytes));) {
    kept.push(bytes.slice(cursor, m.index));
    const body = m.index + m[0].length;
    // Hunting for `endstream` instead would be one accidental occurrence in compressed bytes
    // away from resuming the scan inside binary, and a desynced scan produces a plausible
    // number rather than an error. Trust the declared length, then check it landed.
    const declared = [
      ...bytes
        .slice(Math.max(0, m.index - 512), m.index)
        .matchAll(/\/Length (\d+)\s*[/>]/g),
    ].pop();
    let end = declared ? body + Number(declared[1]) : -1;
    if (end < 0 || !/^\s{0,2}endstream/.test(bytes.slice(end, end + 12))) {
      end = bytes.indexOf("endstream", body); // indirect /Length, or a length that lies
    }
    if (end < 0)
      fail("a stream never ends — the PDF is truncated, so no count is safe");
    cursor = end;
    opener.lastIndex = end;
  }
  kept.push(bytes.slice(cursor));
  return kept.join("");
}

function measure(pdf) {
  const dicts = dictionaries(pdf);
  return {
    bytes: pdf.length,
    images: (dicts.match(IMAGE) || []).length,
    pages: (dicts.match(PAGE) || []).length,
  };
}

// 1x1 opaque PNGs in three colours. Distinct pixels because Skia dedupes by content, and three
// copies of one file would embed once and quietly turn the fixture below into a test of nothing.
const PNGS = [
  "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAIAAACQd1PeAAAADElEQVR4nGP4z8AAAAMBAQDJ/pLvAAAAAElFTkSuQmCC",
  "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAIAAACQd1PeAAAADElEQVR4nGNg+M8AAAICAQB7CYF4AAAAAElFTkSuQmCC",
  "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAIAAACQd1PeAAAADElEQVR4nGNgYPgPAAEDAQAIicLsAAAAAElFTkSuQmCC",
];

// Two inputs whose answers are known by construction, run every time, because a counter's
// failure mode is a number and a number always looks like a measurement. tools/qa/Checklist.mjs
// learned this the expensive way: an assertion sat green because no fixture exercised it.
async function proveCounter(p) {
  await p.setContent(
    `<!doctype html><meta charset=utf-8>` +
      PNGS.map(
        (d) =>
          `<div style="break-after:page"><img src="data:image/png;base64,${d}"></div>`,
      ).join(""),
  );
  const known = measure(await p.pdf({ format: "A4" }));
  if (known.images !== 3 || known.pages !== 3) {
    fail(
      `three images on three pages came back as ${known.images} images, ${known.pages} pages`,
    );
  }

  // Skia passes a JPEG through as DCTDecode rather than re-encoding it, so bytes put in a COM
  // segment survive into the PDF verbatim -- the one way to plant chosen text inside a stream.
  const jpeg = Buffer.from(
    await p.evaluate(() => {
      const c = Object.assign(document.createElement("canvas"), {
        width: 32,
        height: 32,
      });
      const g = c.getContext("2d");
      g.fillStyle = "#c33";
      g.fillRect(0, 0, 32, 32);
      g.fillStyle = "#39c";
      g.fillRect(4, 4, 12, 20);
      return c.toDataURL("image/jpeg", 0.9).split(",")[1];
    }),
    "base64",
  );
  const comment = Buffer.from(`${MARKER} ${MARKER}`, "latin1");
  const n = comment.length + 2; // a COM segment's big-endian length counts its own two bytes
  const trap = Buffer.concat([
    jpeg.subarray(0, 2), // SOI
    Buffer.from([0xff, 0xfe, n >> 8, n & 0xff]),
    comment,
    jpeg.subarray(2),
  ]);
  await p.setContent(
    `<!doctype html><img src="data:image/jpeg;base64,${trap.toString("base64")}">`,
  );
  const pdf = await p.pdf({ format: "A4" });
  const counted = measure(pdf).images;
  const naive = (pdf.toString("latin1").match(IMAGE) || []).length;
  if (counted !== 1) fail(`one JPEG came back as ${counted} images`);
  if (naive <= counted) {
    fail(
      `the planted marker never reached the PDF — a whole-file regex sees ${naive}, so the stream-skipping is unproven and this fixture asserts nothing`,
    );
  }
}

const out = process.argv[2];
const urls = process.argv.slice(3);
const cold = process.env.PDF_COLD === "1";

const b = await chromium.launch();
const p = await b.newPage({ viewport: { width: 1280, height: 1000 } });
await proveCounter(p);

for (const u of urls) {
  const name = u.split("/").filter(Boolean).pop();
  await p.goto(u, { waitUntil: "networkidle" });
  if (!cold) {
    const h = await p.evaluate(() => document.body.scrollHeight);
    for (let y = 0; y < h; y += 600) {
      await p.evaluate((y) => window.scrollTo(0, y), y);
      await p.waitForTimeout(80);
    }
    await p.evaluate(() => window.scrollTo(0, 0));
    await p.waitForTimeout(900);
  }
  // page.pdf() forces print emulation, so @media print applies without an emulateMedia call.
  const pdf = await p.pdf({
    path: `${out}/print_${name}.pdf`,
    printBackground: true,
    format: "A4",
  });
  const m = measure(pdf);
  console.log(
    `${name}: ${m.bytes} bytes, ${m.images} images, ${m.pages} pages (${cold ? "cold" : "warm"})`,
  );
}
await b.close();
