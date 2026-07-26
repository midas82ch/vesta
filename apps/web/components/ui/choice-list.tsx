import type { ReactNode } from "react";

export type ChoiceOption = {
  value: string;
  label: ReactNode;
  detail?: ReactNode;
  icon?: ReactNode;
};

type ChoiceListProps = {
  options: ChoiceOption[];
  onSelect: (value: string) => void;
  selectedValue?: string;
  disabled?: boolean;
};

/**
 * One "pick one of N" pattern for the need-picker, yes/no questions,
 * single-choice questions and the AI-proposal confirmation, instead of
 * cards for one and orange pill-buttons for the others.
 */
export function ChoiceList({ options, onSelect, selectedValue, disabled }: ChoiceListProps) {
  return (
    <div className="choice-list">
      {options.map((option) => (
        <button
          className={
            option.value === selectedValue
              ? "choice-item choice-item-selected"
              : "choice-item"
          }
          disabled={disabled}
          key={option.value}
          onClick={() => onSelect(option.value)}
          type="button"
        >
          {option.icon && (
            <span aria-hidden="true" className="choice-icon">
              {option.icon}
            </span>
          )}
          <span className="choice-copy">
            <strong>{option.label}</strong>
            {option.detail && <small>{option.detail}</small>}
          </span>
          <span aria-hidden="true" className="btn-icon">
            →
          </span>
        </button>
      ))}
    </div>
  );
}
