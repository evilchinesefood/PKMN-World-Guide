import { defineConfig } from "astro/config";

// Deployed under a subpath at dev.jdayers.com/pkmn-world (DECISIONS.md 4), so `base`
// is set and every asset/link must be subpath-relative. Use the Url() helper in
// src/Url.ts rather than writing root-absolute paths.
export default defineConfig({
  site: "https://dev.jdayers.com",
  base: "/pkmn-world",
  trailingSlash: "always",
  output: "static",
  build: { format: "directory" },
});
