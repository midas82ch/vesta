import type { MetadataRoute } from "next";

export default function manifest(): MetadataRoute.Manifest {
  return {
    id: "/",
    name: "Vesta – Berner Sozial-Lotse",
    short_name: "Vesta",
    description:
      "Der verifizierte, mehrsprachige Sozial-Lotse für Bern: passende Hilfe finden, Fachpersonen entlasten und Systemlücken sichtbar machen.",
    start_url: "/?source=pwa",
    scope: "/",
    display: "standalone",
    orientation: "any",
    background_color: "#f4efe5",
    theme_color: "#164f47",
    lang: "de-CH",
    categories: ["social", "utilities"],
    icons: [
      {
        src: "/pwa-icon?size=192",
        sizes: "192x192",
        type: "image/png",
        purpose: "any",
      },
      {
        src: "/pwa-icon?size=512",
        sizes: "512x512",
        type: "image/png",
        purpose: "any",
      },
      {
        src: "/pwa-icon?size=512&maskable=1",
        sizes: "512x512",
        type: "image/png",
        purpose: "maskable",
      },
    ],
  };
}
