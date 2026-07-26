// Viewport-only screenshot, for judging above-the-fold layout rather than whole-page structure.
import { chromium } from "playwright";
const [out, url, h] = process.argv.slice(2);
const b = await chromium.launch();
const p = await b.newPage({
  viewport: { width: 1280, height: Number(h) || 900 },
});
await p.goto(url, { waitUntil: "networkidle" });
await p.waitForTimeout(700);
await p.screenshot({ path: out });
await b.close();
