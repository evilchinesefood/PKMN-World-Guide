// Visual QA: screenshots the built site and reports any JS errors on each page.
import { chromium } from "playwright";

const out = process.argv[2];
const urls = process.argv.slice(3);
// A guide read on a phone is the common case, and the layout defects that only show up
// there (a banner that will not wrap, a map box wider than the screen) are invisible at
// desktop width. SHOT_WIDTH=390 photographs the same pages as a phone.
const width = Number(process.env.SHOT_WIDTH) || 1280;
const b = await chromium.launch();
const p = await b.newPage({ viewport: { width, height: 1000 } });
const errs = [];
p.on("console", (m) => m.type() === "error" && errs.push(m.text()));
p.on("pageerror", (e) => errs.push(String(e)));

for (const u of urls) {
  errs.length = 0;
  const name = u.split("/").filter(Boolean).pop();
  await p.goto(u, { waitUntil: "networkidle" });
  // A chapter's inline maps mount only when they scroll into view, and a fullPage capture
  // does NOT scroll the page -- it grows the capture instead. Walk the page first or the
  // shot shows eight empty boxes no real reader ever sees.
  const h = await p.evaluate(() => document.body.scrollHeight);
  for (let y = 0; y < h; y += 600) {
    await p.evaluate((y) => window.scrollTo(0, y), y);
    await p.waitForTimeout(80);
  }
  await p.evaluate(() => window.scrollTo(0, 0));
  await p.waitForTimeout(900);
  await p.screenshot({ path: `${out}/shot_${name}.png`, fullPage: true });
  console.log(
    `${name}: ${errs.length ? "JS ERRORS -> " + errs.slice(0, 3).join(" | ") : "clean"}`,
  );
}
await b.close();
