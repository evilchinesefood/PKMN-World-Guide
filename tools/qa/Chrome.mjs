// Geometry guard for the device shell. Three properties, all of them things a CSS
// edit can silently break and no human reliably notices:
//
//   1. The document never scrolls sideways. This is what the nav-wrap rule in
//      Guide.css exists to protect -- a nav that cannot wrap sets the scroll width
//      of the whole page and drags it under the reader's thumb. The shell replaces
//      that wrap with a nav that scrolls INSIDE ITSELF, which preserves the property
//      by a different mechanism, so the property now needs an actual assertion.
//   2. The sticky banner stays within its mobile budget. It is sticky, so its height
//      is subtracted from every screen of every page; it is the number that decides
//      whether the guide is pleasant on a phone.
//   3. The desktop banner height matches the --banner-h CSS fallback constant. The
//      fallback is what a browser without ResizeObserver uses to place sticky
//      walkthrough maps. If the two disagree, those maps sit under the banner on
//      exactly the browsers least able to cope.
//
// Serves dist/ itself rather than requiring `astro preview` in another terminal, so
// `npm run qa` stays one command. The site's assets are root-absolute under
// /pkmn-world, which is why file:// URLs cannot be used here.
import { chromium } from "playwright";
import { createServer } from "node:http";
import { readFileSync, readdirSync, existsSync, statSync } from "node:fs";
import { join, extname } from "node:path";

const DIST = "dist";
const BASE = "/pkmn-world";
const PORT = 8788;

// Budget for the sticky banner on a phone. Today's three-row banner is 126px; the
// shell lands 85px. 96px leaves room for a font that loads differently without
// letting a future edit quietly reintroduce a three-row header.
const MAX_STICKY_390 = 96;

const PAGES = [
  "/",
  "/species/",
  "/species/006/",
  "/maps/",
  "/walkthrough/pallettoviridian/",
];

const TYPES = {
  ".html": "text/html; charset=utf-8",
  ".css": "text/css",
  ".js": "text/javascript",
  ".json": "application/json",
  ".png": "image/png",
  ".jpg": "image/jpeg",
  ".webp": "image/webp",
  ".svg": "image/svg+xml",
};

if (!existsSync(DIST)) {
  console.error(`${DIST}/ not found — run the build first.`);
  process.exit(1);
}

const server = createServer((req, res) => {
  let p = decodeURIComponent(req.url.split("?")[0]);
  if (p.startsWith(BASE)) p = p.slice(BASE.length);
  let f = join(DIST, p);
  if (existsSync(f) && statSync(f).isDirectory()) f = join(f, "index.html");
  if (!existsSync(f)) {
    res.writeHead(404);
    return res.end("not found");
  }
  res.writeHead(200, {
    "content-type": TYPES[extname(f)] ?? "application/octet-stream",
  });
  res.end(readFileSync(f));
});
await new Promise((r) => server.listen(PORT, "127.0.0.1", r));

const browser = await chromium.launch();
const failures = [];
let desktopBanner = 0;

for (const path of PAGES) {
  for (const width of [390, 1280]) {
    const ctx = await browser.newContext({
      viewport: { width, height: 900 },
      isMobile: width === 390,
      hasTouch: width === 390,
    });
    const page = await ctx.newPage();
    await page.goto(`http://127.0.0.1:${PORT}${BASE}${path}`, {
      waitUntil: "networkidle",
    });

    const m = await page.evaluate(() => {
      const b = document.querySelector(".banner");
      return {
        banner: b ? b.getBoundingClientRect().height : null,
        doc: document.documentElement.scrollWidth,
        vp: document.documentElement.clientWidth,
      };
    });

    // A missing banner is a FAILURE, not a zero. PAGES hard-codes routes, and a
    // renamed chapter or a moved index would serve this a 404 -- which has no
    // .banner, measures 0px, and sails under every budget below. A guard that
    // passes because it loaded the wrong page is worse than no guard.
    if (m.banner === null) {
      failures.push(
        `${path} @${width}: no .banner on the page — route missing, or the banner was renamed`,
      );
      await ctx.close();
      continue;
    }

    if (m.doc > m.vp) {
      failures.push(
        `${path} @${width}: document scrolls sideways — ${m.doc}px of content in a ${m.vp}px viewport`,
      );
    }

    if (width === 390 && m.banner > MAX_STICKY_390) {
      failures.push(
        `${path} @390: sticky banner is ${Math.round(m.banner)}px, over the ${MAX_STICKY_390}px budget`,
      );
    }

    if (width === 1280) desktopBanner = m.banner;

    await ctx.close();
  }
}

// The walkthrough page hard-codes a fallback for --banner-h -- the value a browser
// with no ResizeObserver uses to place the sticky chapter map, because Base.astro
// never publishes the real height there. Nothing keeps that constant in step with the
// banner it is standing in for, and the failure is invisible: the map renders, it just
// sits under the banner, on the browsers least able to cope.
//
// Read as text rather than measured in the page, deliberately. The sticky rule is
// `.walk-map:has(.leaflet-container)`, so it only applies once Leaflet has mounted,
// which needs the map scrolled into view and a lazy mount awaited. Reading the
// declaration is exact, fast, and cannot pass for the wrong reason.
{
  const dir = join(DIST, "walkthrough");
  const chapters = existsSync(dir)
    ? readdirSync(dir).map((d) => join(dir, d, "index.html")).filter(existsSync)
    : [];

  const declared = new Set();
  for (const f of chapters) {
    for (const m of readFileSync(f, "utf8").matchAll(/--banner-h,\s*([\d.]+)rem/g)) {
      declared.add(Number(m[1]));
    }
  }

  if (!declared.size) {
    failures.push(
      "no --banner-h fallback found in any built walkthrough page — the guard is looking in the wrong place",
    );
  }

  for (const rem of declared) {
    const px = rem * 16; // html sets no font-size, so rem is 16px
    if (Math.abs(desktopBanner - px) > 1) {
      failures.push(
        `--banner-h fallback is ${rem}rem (${px}px) but the desktop banner renders at ` +
          `${desktopBanner.toFixed(1)}px — a browser without ResizeObserver would place ` +
          `the sticky chapter map ${(desktopBanner - px).toFixed(1)}px wrong`,
      );
    }
  }
}

// The amber lamp claims to report whether spoilers are revealed. Two readouts that
// can disagree are worse than one, so this asserts the lamp and the button's label
// are driven from the same state -- and, separately, that the lamp actually LOOKS
// different in the two states. The second half is not pedantry: the first attempt at
// this was a halo-only change that was invisible against red plastic, and a lamp
// that reports a state nobody can see reports nothing.
{
  const ctx = await browser.newContext({ viewport: { width: 1280, height: 900 } });
  const page = await ctx.newPage();
  await page.goto(`http://127.0.0.1:${PORT}${BASE}/species/006/`, {
    waitUntil: "networkidle",
  });

  const read = () =>
    page.evaluate(() => {
      const l = document.querySelector(".lamp-item");
      const s = getComputedStyle(l);
      return {
        revealed: document.documentElement.classList.contains("pw-revealed"),
        look: `${s.backgroundImage}|${s.boxShadow}`,
        label: document.getElementById("reveal-all").textContent.trim(),
      };
    });

  const before = await read();
  await page.click("#reveal-all");
  const after = await read();

  if (before.revealed === after.revealed) {
    failures.push("reveal-all did not toggle html.pw-revealed");
  }
  if (after.revealed !== (after.label === "Hide spoilers")) {
    failures.push(
      `the lamp and the button disagree: class=${after.revealed}, label="${after.label}"`,
    );
  }
  if (before.look === after.look) {
    failures.push(
      "the amber lamp renders identically revealed and hidden — it reports nothing",
    );
  }

  await ctx.close();
}

// Every nav control has to be REACHABLE on a phone, and reachable is not the same as
// present. A control can sit in the DOM, inside the banner's box, and still be off the
// right edge of a horizontal scroller -- which is exactly what the first mobile shell did
// to "Reveal everything" and, at 320px, to four of the seven controls. A reader does not
// swipe a row that looks complete, so a control behind that swipe is a control they do not
// have.
//
// "Reachable" here means: open whatever disclosure the banner offers, then every control
// must be inside the viewport and unclipped by any scrolling ancestor. A design that keeps
// them all on screen passes without a menu; a design that hides them behind a swipe fails.
{
  for (const width of [390, 320]) {
    const ctx = await browser.newContext({
      viewport: { width, height: 844 },
      isMobile: true,
      hasTouch: true,
    });
    const page = await ctx.newPage();
    await page.goto(`http://127.0.0.1:${PORT}${BASE}/species/006/`, {
      waitUntil: "networkidle",
    });

    const closedH = await page.evaluate(
      () => document.querySelector(".banner").getBoundingClientRect().height,
    );

    // CLICK the key rather than setting .open, because "the panel can be opened" is the
    // claim, and setting the property proves only that the panel exists. A key that is
    // off-screen, zero-sized or under something else fails a click and passes a property
    // set -- which is exactly the class of defect this block is here to catch.
    const key = await page.$(".banner details > summary");
    if (key) {
      await key.click({ timeout: 2000 }).catch((e) => {
        failures.push(`@${width}: the nav menu key could not be clicked — ${e.message.split("\n")[0]}`);
      });
    }

    const r = await page.evaluate(() => {
      const nav = document.querySelector(".banner nav");
      const nb = nav.getBoundingClientRect();
      const out = [...nav.children].map((el) => {
        const b = el.getBoundingClientRect();
        const clipped = b.right > nb.right + 0.5 || b.left < nb.left - 0.5;
        const offscreen = b.left < 0 || b.right > window.innerWidth + 0.5;
        // Vertical too. The panel is pinned to a sticky banner, so a control that runs
        // past the bottom of the viewport cannot be scrolled to -- the panel does not
        // scroll with the page, it sits on it. On a short viewport that silently puts the
        // last row out of reach, which is the same defect as the horizontal one and was
        // invisible to a horizontal-only check.
        const belowFold = b.bottom > window.innerHeight + 0.5 || b.top < 0;
        return { label: el.textContent.trim(), ok: !clipped && !offscreen && !belowFold };
      });
      return {
        unreachable: out.filter((x) => !x.ok).map((x) => x.label),
        openH: document.querySelector(".banner").getBoundingClientRect().height,
      };
    });

    if (r.unreachable.length) {
      failures.push(
        `@${width}: ${r.unreachable.length} nav control(s) need a horizontal swipe to reach — ${r.unreachable.join(", ")}`,
      );
    }

    // Opening the menu must not resize the banner. Base.astro publishes the banner height
    // as --banner-h, and the walkthrough's sticky map is positioned from it; a menu that
    // pushes the page down instead of overlaying it would move that map out from under the
    // reader mid-tap. The panel therefore has to overlay, and this is what says so.
    if (Math.abs(r.openH - closedH) > 0.5) {
      failures.push(
        `@${width}: opening the nav menu changed the banner from ${closedH.toFixed(1)}px to ${r.openH.toFixed(1)}px — it must overlay, not push`,
      );
    }

    await ctx.close();
  }
}

await browser.close();
server.close();

if (failures.length) {
  console.error(`chrome: ${failures.length} failure(s)`);
  for (const f of failures) console.error(`  ${f}`);
  process.exit(1);
}
console.log(`chrome: ${PAGES.length} pages × 2 widths OK`);
