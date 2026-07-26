import type { MessageKey } from "@/lib/i18n";

export type Need = "sleep_tonight" | "basic_needs" | "counselling";

export type NeedOption = {
  value: Need;
  title: MessageKey;
  detail: MessageKey;
  icon: string;
};

export const needs: NeedOption[] = [
  {
    value: "sleep_tonight",
    title: "need.sleep.title",
    detail: "need.sleep.detail",
    icon: "⌂",
  },
  {
    value: "basic_needs",
    title: "need.basic.title",
    detail: "need.basic.detail",
    icon: "+",
  },
  {
    value: "counselling",
    title: "need.counselling.title",
    detail: "need.counselling.detail",
    icon: "→",
  },
];
