import { NeedSymbol } from "@/components/need-symbol";
import type { ServiceIcon } from "@/lib/needs";

export type IconChoiceOption = {
  value: string;
  label: string;
  icon: ServiceIcon;
};

type IconChoiceGridProps = {
  options: IconChoiceOption[];
  selectedValues: string[];
  onToggle: (value: string) => void;
  disabled?: boolean;
};

export function IconChoiceGrid({
  options,
  selectedValues,
  onToggle,
  disabled,
}: IconChoiceGridProps) {
  return (
    <div className="icon-choice-grid">
      {options.map((option) => {
        const selected = selectedValues.includes(option.value);
        return (
          <button
            aria-pressed={selected}
            className={
              selected
                ? "icon-choice-item icon-choice-item--selected"
                : "icon-choice-item"
            }
            disabled={disabled}
            key={option.value}
            onClick={() => onToggle(option.value)}
            type="button"
          >
            <span aria-hidden="true" className="icon-choice-symbol">
              <NeedSymbol name={option.icon} />
            </span>
            <span>{option.label}</span>
            {selected && (
              <span aria-hidden="true" className="icon-choice-check">
                <NeedSymbol name="check" />
              </span>
            )}
          </button>
        );
      })}
    </div>
  );
}
