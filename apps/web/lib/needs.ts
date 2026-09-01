import type { MessageKey } from "@/lib/i18n";

export type Need = string;
export type NeedIcon =
  | "home"
  | "food"
  | "book"
  | "health"
  | "clothing"
  | "shower"
  | "support"
  | "other";

export type NeedOption = {
  value: Need;
  title: MessageKey;
  detail: MessageKey;
  icon: NeedIcon;
};

export const needs: NeedOption[] = [
  {
    value: "sleep_tonight",
    title: "need.sleep.title",
    detail: "need.sleep.detail",
    icon: "home",
  },
  {
    value: "basic_needs",
    title: "need.basic.title",
    detail: "need.basic.detail",
    icon: "food",
  },
  {
    value: "counselling",
    title: "need.counselling.title",
    detail: "need.counselling.detail",
    icon: "book",
  },
];
