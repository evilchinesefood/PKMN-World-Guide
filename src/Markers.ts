// The event overlay both a map page and an inline chapter map draw, built once so the two
// cannot disagree about what is on a map or what number it carries.
//
// Numbering follows the source order of each event array, so a link to callout 3 keeps
// meaning callout 3 across rebuilds -- and the hidden-items table on a map page numbers its
// rows off the same order (items first, then hidden items).
import { titleOf, prettyConst } from "./Names";

export interface Marker {
  kind: "item" | "hidden_item" | "trainer" | "warp" | "sign";
  n: number;
  x: number;
  y: number;
  label: string;
}

export const isItem = (o: any) => o.graphics_id === "OBJ_EVENT_GFX_ITEM_BALL";
export const isTrainer = (o: any) =>
  o.trainer_type === "TRAINER_TYPE_NORMAL" ||
  o.trainer_type === "TRAINER_TYPE_BURIED";

export function markersOf(m: any): Marker[] {
  let n = 0;
  const at = (kind: Marker["kind"], c: any, label: string): Marker => ({
    kind,
    n: ++n,
    x: c.x,
    y: c.y,
    label,
  });
  const objs: any[] = m.object_events ?? [];
  return [
    ...objs.filter(isItem).map((o) => at("item", o.coord, "Item ball")),
    ...(m.hidden_items ?? []).map((h: any) =>
      at("hidden_item", h.coord, "Hidden: " + prettyConst(h.item, "ITEM_")),
    ),
    ...objs.filter(isTrainer).map((o) => at("trainer", o.coord, "Trainer")),
    ...(m.warps ?? []).map((w: any) =>
      at("warp", w.coord, "To " + titleOf(w.dest_map)),
    ),
    ...(m.signs ?? []).map((s: any) => at("sign", s.coord, "Sign")),
  ];
}
