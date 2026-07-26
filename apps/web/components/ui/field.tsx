import type { InputHTMLAttributes, ReactNode, TextareaHTMLAttributes } from "react";

type FieldProps = {
  id: string;
  label: ReactNode;
  hint?: ReactNode;
};

/**
 * Label wraps the control implicitly (valid HTML - see MDN/WCAG 1.3.1) so the
 * hint stays a separate sibling, linked via aria-describedby, instead of
 * being folded into the control's accessible name.
 */
export function TextAreaField({
  id,
  label,
  hint,
  ...textareaProps
}: FieldProps & Omit<TextareaHTMLAttributes<HTMLTextAreaElement>, "id">) {
  const hintId = hint ? `${id}-hint` : undefined;

  return (
    <>
      <label className="field" htmlFor={id}>
        {label}
        <textarea id={id} aria-describedby={hintId} {...textareaProps} />
      </label>
      {hint && (
        <p className="field-hint" id={hintId}>
          {hint}
        </p>
      )}
    </>
  );
}

export function NumberField({
  id,
  label,
  hint,
  ...inputProps
}: FieldProps & Omit<InputHTMLAttributes<HTMLInputElement>, "id" | "type">) {
  const hintId = hint ? `${id}-hint` : undefined;

  return (
    <>
      <label className="field" htmlFor={id}>
        {label}
        <input id={id} inputMode="numeric" type="number" aria-describedby={hintId} {...inputProps} />
      </label>
      {hint && (
        <p className="field-hint" id={hintId}>
          {hint}
        </p>
      )}
    </>
  );
}
