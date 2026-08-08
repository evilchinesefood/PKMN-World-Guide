// Print QA: prints a page and counts what landed in the PDF, instead of looking at it.
//
// DECISIONS.md 35 fixed a chapter that printed eight empty map boxes and closed with a rule --
// "Measure printed output by counting embedded image XObjects in the PDF. The preview lies." --
// but shipped no tool, so the 46 images and 573,354 bytes it records have been unreproducible
// ever since, and decisions 35 and 36 rest on a measurement nobody can repeat. This is that
// tool, and it does not reproduce 46: the same chapter measures 100 rasters today, 6 of which
// came from a picture. The likely reason is that this is not the page 35 measured -- decisions
// 36-38 and M5 rewrote the print stylesheet underneath it -- but that is an explanation, not a
// proof, because the 2026-07-26 tree cannot be rebuilt to check it. What IS checked is the
// property 35's fix exists to hold: cold and warm still print the same file, byte for byte
// once the embedded timestamp is normalised.
//
// WHY IT WALKS THE PAGE BEFORE PRINTING. The walk below is deliberately the same 600px/80ms one
// Shot.mjs does, so the two tools warm a page identically and their numbers can be compared.
// Shot.mjs's header explains the mechanism; the stakes are higher here. A chapter's map viewers
// mount on IntersectionObserver, so until something scrolls they are absent from the document
// rather than merely unpainted, and page.pdf() re-lays-out for print without ever scrolling.
// Skipping the walk therefore measures the COLD path -- the one decision 35 says printed 41 of
// 46 images -- while the output line claims the warm one. PDF_COLD=1 asks for cold deliberately;
// either way the line names the path, because the interesting result is whether they agree.
//
// TWO NUMBERS, AND WHY NEITHER IS ENOUGH ALONE. `images` counts /Subtype /Image XObjects, which
// is decision 35's construction and a poor headline figure: Skia dedupes by content (the
// chapter's nine <img> tags draw six files and embed six), a soft mask is itself an image
// XObject, and Skia rasterises composited CSS -- gradients, shadows, luminosity masks, page
// backgrounds under printBackground -- into image XObjects with no <img> behind them. On the
// Kanto chapter that is 94 of 100, so the total tracks the print stylesheet far more closely
// than it tracks the pictures, and on its own it cannot tell a map that stopped printing from a
// gradient somebody deleted on purpose.
//
// `content` is the subset that came from a picture: not greyscale, and not as wide as the paper
// (the media-box width is read out of the file rather than assumed). Both halves are claims
// about Skia's habits rather than facts about PDF -- it renders its luminosity masks greyscale
// and paints backgrounds and hairline seams at exactly the media-box width, while a decoded
// picture lands at its own pixel size in colour. Two things would break it: a
// content image that is genuinely page-width, and a greyscale one. Neither exists on this site,
// where every map render is a colour PNG narrower than the paper, and proveCounter() checks the
// split discriminates rather than trusting that it does. Both numbers are printed because you
// need both: `content` moving is a defect, only `images` moving is the stylesheet.
//
// Object dictionaries are plain text, but the streams between them are compressed binary that
// can spell anything, so the scan skips each stream by its declared /Length. proveCounter()
// shows that skip is load-bearing rather than defensive: it embeds a JPEG whose comment segment
// carries two complete fake object headers, and without the skip the same counter reports two
// images and two pages where there is one of each. The known hole is /Title, which Chromium
// copies from document.title verbatim into the plaintext Info dictionary, so a page titled
// "/Subtype /Image" would add one to both raster counts.

import { chromium } from "playwright";

const IMAGE = /\/Subtype\s*\/Image\b/;
// `/Pages` is the page-tree node, not a page; the lookahead is the whole reason for the regex.
const PAGE = /\/Type\s*\/Page(?![a-zA-Z])/;
const OBJSTM = /\/Type\s*\/ObjStm/;
const MEDIABOX = /\/MediaBox\s*\[\s*[\d.-]+\s+[\d.-]+\s+([\d.]+)/;
const WIDTH = /\/Width (\d+)/;
const GREY = /\/ColorSpace\s*\/DeviceGray/;
// What the JPEG fixture smuggles into a compressed stream: two complete object headers, not a
// bare marker. count() counts objects, so text that lands inside an object already counted
// changes nothing -- only a fake object boundary can lie to it, which makes this the plant that
// actually tests the stream skipping.
const PLANT =
  "\n900 0 obj\n<</Type /XObject /Subtype /Image /Width 1 /Height 1>>\n901 0 obj\n<</Type /Page>>\n";

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

// One body per object, so a dictionary is counted once however many times it says a thing.
function count(text) {
  const objects = text.split(/\d+ \d+ obj/);
  const paper = new Set();
  for (const o of objects) {
    const box = MEDIABOX.exec(o);
    if (box) paper.add(Math.ceil(Number(box[1])));
  }
  const images = objects.filter((o) => IMAGE.test(o));
  return {
    images: images.length,
    content: images.filter(
      (o) => !GREY.test(o) && !paper.has(Number(WIDTH.exec(o)?.[1] ?? -1)),
    ).length,
    pages: objects.filter((o) => PAGE.test(o)).length,
    objstm: objects.some((o) => OBJSTM.test(o)),
  };
}

function measure(pdf) {
  const { objstm, ...counts } = count(dictionaries(pdf));
  // An image XObject is a stream object, so its dictionary can never be compressed away and the
  // raster counts are safe by construction. A /Type /Page dictionary is an ordinary object, and a
  // writer using object streams would hide it inside one -- which this scan would report as a
  // shorter document rather than as an error, the exact silence the tool exists to break.
  // Chromium emits a plain xref table today. A cross-reference STREAM on its own is harmless for
  // the same reason image XObjects are, so it is not a trigger; only the container that swallows
  // whole objects is.
  if (objstm) {
    fail(
      "the PDF uses object streams, so /Type /Page dictionaries may be hidden from this scan",
    );
  }
  return { bytes: pdf.length, ...counts };
}

// 1x1 opaque PNGs in three saturated colours. Distinct pixels because Skia dedupes by content,
// and three copies of one file embed once and turn the fixture below into a test of nothing.
const PNGS = [
  "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAIAAACQd1PeAAAADElEQVR4nGP4z8AAAAMBAQDJ/pLvAAAAAElFTkSuQmCC",
  "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAIAAACQd1PeAAAADElEQVR4nGNg+M8AAAICAQB7CYF4AAAAAElFTkSuQmCC",
  "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAIAAACQd1PeAAAADElEQVR4nGNgYPgPAAEDAQAIicLsAAAAAElFTkSuQmCC",
];

// Two inputs whose answers are known by construction, run every time, because a counter's
// failure mode is a number and a number always looks like a measurement. tools/qa/Checklist.mjs
// learned this the expensive way: an assertion sat green because no fixture exercised it.
async function proveCounter(p) {
  // Three pictures on three pages, and one of each kind of furniture the content split has to
  // throw away: a full-bleed gradient, which Skia answers with rasters at media-box width, and a
  // box-shadow, which it answers with a greyscale luminosity mask at no particular size. Both are
  // here because a fixture that omits one leaves that half of the split asserting nothing while
  // still returning 3.
  await p.setContent(
    `<!doctype html><meta charset=utf-8><style>html{background:linear-gradient(#f00,#00f)}` +
      `div{break-after:page}.shadow{display:block;width:200px;height:100px;box-shadow:0 0 20px #000}</style>` +
      PNGS.map(
        (d, i) =>
          `<div><img src="data:image/png;base64,${d}">${i ? "" : "<span class=shadow></span>"}</div>`,
      ).join(""),
  );
  const proof = await p.pdf({ printBackground: true, format: "A4" });
  const known = measure(proof);
  if (known.content !== 3 || known.pages !== 3) {
    fail(
      `three pictures on three pages came back as ${known.content} content images, ${known.pages} pages`,
    );
  }
  if (known.images - known.content < 2) {
    fail(
      `the gradient and the shadow embedded ${known.images - known.content} rasters between them, so the content split is untested`,
    );
  }
  if (!GREY.test(proof.toString("latin1"))) {
    fail(
      "the shadow embedded no greyscale mask, so the split's greyscale half is untested",
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
  const comment = Buffer.from(PLANT, "latin1");
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
  const honest = measure(pdf);
  const naive = count(pdf.toString("latin1")); // the same counter, without the stream skipping
  if (honest.images !== 1 || honest.pages !== 1) {
    fail(
      `one JPEG on one page came back as ${honest.images} images, ${honest.pages} pages`,
    );
  }
  if (naive.images <= honest.images || naive.pages <= honest.pages) {
    fail(
      `the planted objects never reached the PDF — unskipped, the same counter sees ${naive.images} images and ${naive.pages} pages, so the stream skipping is unproven and this fixture asserts nothing`,
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
    `${name}: ${m.bytes} bytes, ${m.content} content image${m.content === 1 ? "" : "s"} of ${m.images} rasters, ${m.pages} pages (${cold ? "cold" : "warm"})`,
  );
}
await b.close();
