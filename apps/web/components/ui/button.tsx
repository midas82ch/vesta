import Link from "next/link";
import type {
  AnchorHTMLAttributes,
  ButtonHTMLAttributes,
  ReactNode,
} from "react";

export type ButtonVariant = "primary" | "secondary" | "ghost";
type IconPosition = "start" | "end";

type CommonProps = {
  variant?: ButtonVariant;
  icon?: ReactNode;
  iconPosition?: IconPosition;
  children: ReactNode;
};

type ButtonAsButton = CommonProps &
  Omit<ButtonHTMLAttributes<HTMLButtonElement>, "children"> & {
    href?: undefined;
  };

type ButtonAsLink = CommonProps &
  Omit<AnchorHTMLAttributes<HTMLAnchorElement>, "children" | "href"> & {
    href: string;
  };

export type ButtonProps = ButtonAsButton | ButtonAsLink;

const variantClassName: Record<ButtonVariant, string> = {
  primary: "btn btn-primary",
  secondary: "btn btn-secondary",
  ghost: "btn btn-ghost",
};

function ButtonContent({
  icon,
  iconPosition = "end",
  children,
}: Pick<CommonProps, "icon" | "iconPosition" | "children">) {
  const iconSpan = icon ? (
    <span aria-hidden="true" className="btn-icon">
      {icon}
    </span>
  ) : null;

  return (
    <>
      {iconPosition === "start" && iconSpan}
      <span>{children}</span>
      {iconPosition === "end" && iconSpan}
    </>
  );
}

/**
 * The one place every button-shaped element in the app renders from.
 * Renders a `<Link>` when `href` is given, otherwise a `<button>` - so
 * navigation ("Zurück") and actions ("Vorschlag prüfen") share one import
 * and one visual language instead of drifting apart over time.
 */
export function Button({
  variant = "primary",
  icon,
  iconPosition,
  children,
  href,
  ...rest
}: ButtonProps) {
  const className = variantClassName[variant];

  if (href !== undefined) {
    return (
      <Link
        className={className}
        href={href}
        {...(rest as AnchorHTMLAttributes<HTMLAnchorElement>)}
      >
        <ButtonContent icon={icon} iconPosition={iconPosition}>
          {children}
        </ButtonContent>
      </Link>
    );
  }

  return (
    <button
      className={className}
      type="button"
      {...(rest as ButtonHTMLAttributes<HTMLButtonElement>)}
    >
      <ButtonContent icon={icon} iconPosition={iconPosition}>
        {children}
      </ButtonContent>
    </button>
  );
}
