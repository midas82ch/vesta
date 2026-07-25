import type { MetadataRoute } from "next";


export default function manifest(): MetadataRoute.Manifest {
  return {
    name: "Vesta – Berner Sozial-Lotse",
    short_name: "Vesta",
    description:
      "Verständliche und verifizierte Orientierung zu sozialen Angeboten in Bern.",
    start_url: "/",
    display: "standalone",
    background_color: "#f4efe5",
    theme_color: "#f4efe5",
    lang: "de-CH",
    icons: [
      {
        src: "/icon",
        sizes: "512x512",
        type: "image/png",
      },
    ],
  };
}
