import { createElement } from "react";
import { ImageResponse } from "next/og";
import type { NextRequest } from "next/server";

export function GET(request: NextRequest) {
  const requestedSize = Number(request.nextUrl.searchParams.get("size"));
  const size = requestedSize === 192 ? 192 : 512;
  const maskable = request.nextUrl.searchParams.get("maskable") === "1";

  const response = new ImageResponse(
    createElement(
      "div",
      {
        style: {
          alignItems: "center",
          background: "#164f47",
          color: "#fffdf8",
          display: "flex",
          fontFamily: "Georgia, serif",
          fontSize: size * (maskable ? 0.46 : 0.56),
          fontWeight: 700,
          height: "100%",
          justifyContent: "center",
          width: "100%",
        },
      },
      "V",
    ),
    {
      width: size,
      height: size,
    },
  );

  response.headers.set(
    "Cache-Control",
    "public, max-age=31536000, immutable",
  );
  return response;
}
