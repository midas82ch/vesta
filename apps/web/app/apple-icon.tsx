import { ImageResponse } from "next/og";

import { VestaMark } from "@/components/vesta-mark";

export const size = {
  width: 180,
  height: 180,
};

export const contentType = "image/png";

export default function AppleIcon() {
  return new ImageResponse(
    (
      <div
        style={{
          alignItems: "center",
          background: "#164f47",
          borderRadius: 40,
          display: "flex",
          height: "100%",
          justifyContent: "center",
          width: "100%",
        }}
      >
        <VestaMark />
      </div>
    ),
    size,
  );
}
