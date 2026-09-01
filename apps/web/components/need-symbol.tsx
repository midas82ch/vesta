import type { NeedIcon } from "@/lib/needs";

type NeedSymbolProps = {
  name: NeedIcon | "other" | "check";
};

export function NeedSymbol({ name }: NeedSymbolProps) {
  return (
    <svg
      aria-hidden="true"
      className="need-symbol"
      fill="none"
      focusable="false"
      viewBox="0 0 24 24"
    >
      {name === "home" && (
        <>
          <path d="m3 10.5 9-7.5 9 7.5" />
          <path d="M5 9.5V21h14V9.5" />
          <path d="M9 21v-6h6v6" />
        </>
      )}
      {name === "food" && (
        <>
          <path d="M4 11h16c0 5-3.6 9-8 9s-8-4-8-9Z" />
          <path d="M6 20h12" />
          <path d="M8 8c-1-1-1-2 0-3" />
          <path d="M12 8c-1-1-1-2 0-3" />
          <path d="M16 8c-1-1-1-2 0-3" />
        </>
      )}
      {name === "book" && (
        <>
          <path d="M4 5.5A3.5 3.5 0 0 1 7.5 2H11v17H7.5A3.5 3.5 0 0 0 4 22Z" />
          <path d="M20 5.5A3.5 3.5 0 0 0 16.5 2H13v17h3.5A3.5 3.5 0 0 1 20 22Z" />
        </>
      )}
      {name === "health" && (
        <>
          <path d="M12 21s-8-4.6-8-11a4.5 4.5 0 0 1 8-2.8A4.5 4.5 0 0 1 20 10c0 6.4-8 11-8 11Z" />
          <path d="M8 12h2l1-2 2 4 1-2h2" />
        </>
      )}
      {name === "clothing" && (
        <>
          <path d="m8 4-5 3 2 4 3-1v11h8V10l3 1 2-4-5-3" />
          <path d="M9 3c.5 2 5.5 2 6 0" />
        </>
      )}
      {name === "shower" && (
        <>
          <path d="M5 8a5 5 0 0 1 10 0" />
          <path d="M15 8h4" />
          <path d="M8 12v.01M12 12v.01M16 12v.01M8 16v.01M12 16v.01M16 16v.01M12 20v.01" />
        </>
      )}
      {name === "support" && (
        <>
          <circle cx="12" cy="7" r="3" />
          <path d="M4 21c.8-5 3.4-8 8-8s7.2 3 8 8" />
          <path d="m8.5 17 3.5 3 3.5-3" />
        </>
      )}
      {name === "other" && (
        <>
          <circle cx="12" cy="12" r="9" />
          <path d="M9.7 9a2.4 2.4 0 1 1 3.4 2.2c-.8.4-1.1.9-1.1 1.8" />
          <path d="M12 17h.01" />
        </>
      )}
      {name === "check" && <path d="m5 12 4 4L19 6" />}
    </svg>
  );
}
