// The site is served from a subdirectory (dev.jdayers.com/pkmn-world), so nothing may
// emit a root-absolute path. Everything user-facing goes through here.
const BASE = import.meta.env.BASE_URL.replace(/\/$/, "");

export function url(path: string) {
  return BASE + "/" + path.replace(/^\//, "");
}

import { slugOf } from "./Names";

export function mapUrl(id: string) {
  return url("maps/" + slugOf(id) + "/");
}
