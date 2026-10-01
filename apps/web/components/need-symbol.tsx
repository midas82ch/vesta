import type { ServiceIcon } from "@/lib/needs";

type NeedSymbolProps = {
  name: ServiceIcon | "check";
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
      {name === "meal" && (
        <>
          <path d="M4 12h16a8 8 0 0 1-16 0Z" />
          <path d="M7 8h10M9 5h6M6 20h12" />
        </>
      )}
      {name === "groceries" && (
        <>
          <path d="M5 8h14l-1 13H6Z" />
          <path d="M9 8a3 3 0 0 1 6 0" />
          <path d="M9 13h6" />
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
      {name === "laundry" && (
        <>
          <rect x="4" y="2" width="16" height="20" rx="2" />
          <circle cx="12" cy="14" r="5" />
          <path d="M7 6h.01M10 6h6" />
        </>
      )}
      {name === "toilet" && (
        <>
          <path d="M7 3v7a5 5 0 0 0 5 5h5" />
          <path d="M7 7h7v4a4 4 0 0 1-4 4" />
          <path d="M12 15v6M17 15v6M10 21h9" />
        </>
      )}
      {name === "locker" && (
        <>
          <rect x="5" y="2" width="14" height="20" rx="1" />
          <path d="M12 2v20M9 8h.01M15 8h.01" />
        </>
      )}
      {name === "chat" && (
        <>
          <path d="M4 5h16v11H9l-5 4Z" />
          <path d="M8 9h8M8 12h5" />
        </>
      )}
      {name === "housing" && (
        <>
          <path d="m3 11 9-8 9 8" />
          <path d="M5 10v11h14V10M9 21v-6h6v6" />
          <circle cx="18" cy="17" r="2" />
        </>
      )}
      {name === "wallet" && (
        <>
          <rect x="3" y="6" width="18" height="14" rx="2" />
          <path d="M3 9h18M15 13h6v4h-6a2 2 0 0 1 0-4Z" />
        </>
      )}
      {name === "mental-health" && (
        <>
          <path d="M15 20H8a5 5 0 0 1-5-5V9a6 6 0 0 1 12 0v2l3 3-3 1Z" />
          <path d="M8 10c1-2 3-2 4 0 1-2 3-2 4 0 0 3-4 5-4 5s-4-2-4-5Z" />
        </>
      )}
      {name === "legal" && (
        <>
          <path d="M12 3v18M5 6h14M4 19h16" />
          <path d="m6 6-3 6h6ZM18 6l-3 6h6Z" />
        </>
      )}
      {name === "alcohol" && (
        <>
          <path d="M7 3h10l-2 7a3 3 0 0 1-6 0Z" />
          <path d="M12 13v6M8 21h8" />
        </>
      )}
      {name === "medication" && (
        <>
          <path d="M8 5a4 4 0 0 1 6 0l5 5a4 4 0 0 1-6 6l-5-5a4 4 0 0 1 0-6Z" />
          <path d="m10 13 6-6" />
        </>
      )}
      {name === "substances" && (
        <>
          <circle cx="8" cy="8" r="3" />
          <circle cx="16" cy="9" r="2" />
          <circle cx="12" cy="16" r="4" />
        </>
      )}
      {name === "multiple" && (
        <>
          <circle cx="7" cy="7" r="3" />
          <circle cx="17" cy="7" r="3" />
          <circle cx="7" cy="17" r="3" />
          <circle cx="17" cy="17" r="3" />
        </>
      )}
      {name === "question" && (
        <>
          <circle cx="12" cy="12" r="9" />
          <path d="M9.5 9a2.7 2.7 0 1 1 3.8 2.5c-.9.5-1.3 1-1.3 2" />
          <path d="M12 17h.01" />
        </>
      )}
      {name === "daytime" && (
        <>
          <path d="M3 19h18M6 19v-7h12v7" />
          <path d="M9 12V8h6v4M12 3v2M5 6l2 2M19 6l-2 2" />
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
