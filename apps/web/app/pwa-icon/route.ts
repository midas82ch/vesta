import { createElement } from "react";
import { ImageResponse } from "next/og";
import type { NextRequest } from "next/server";

import { VestaMark } from "@/components/vesta-mark";

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
          borderRadius: maskable ? 0 : size * 0.22,
          display: "flex",
          height: "100%",
          justifyContent: "center",
          padding: size * (maskable ? 0.2 : 0.08),
          width: "100%",
        },
      },
      createElement(VestaMark),
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
