type VestaMarkProps = {
  className?: string;
  title?: string;
};

export function VestaMark({ className, title }: Readonly<VestaMarkProps>) {
  return (
    <svg
      aria-hidden={title ? undefined : true}
      className={className}
      focusable="false"
      height="100%"
      role={title ? "img" : undefined}
      viewBox="0 0 64 64"
      width="100%"
      xmlns="http://www.w3.org/2000/svg"
    >
      {title && <title>{title}</title>}
      <path
        d="M14 18 32 50 50 18"
        fill="none"
        stroke="#fffdf8"
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth="8"
      />
      <circle cx="32" cy="13" fill="#ee774d" r="5" />
    </svg>
  );
}
