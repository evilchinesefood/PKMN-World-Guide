// Visual QA: screenshots the built site and reports any JS errors on each page.
import { chromium } from "playwright";

const out = process.argv[2];
const urls = process.argv.slice(3);
const b = await chromium.launch();
const p = await b.newPage({ viewport: { width: 1280, height: 1000 } });
const errs = [];
p.on("console", (m) => m.type() === "error" && errs.push(m.text()));
p.on("pageerror", (e) => errs.push(String(e)));

for (const u of urls) {
  errs.length = 0;
  const name = u.split("/").filter(Boolean).pop();
  await p.goto(u, { waitUntil: "networkidle" });
  await p.waitForTimeout(900);
  await p.screenshot({ path: `${out}/shot_${name}.png`, fullPage: true });
  console.log(`${name}: ${errs.length ? "JS ERRORS -> " + errs.slice(0, 3).join(" | ") : "clean"}`);
}
await b.close();
