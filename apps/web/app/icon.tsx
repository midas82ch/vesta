import { ImageResponse } from "next/og";


export const size = {
  width: 512,
  height: 512,
};

export const contentType = "image/png";

export default function Icon() {
  return new ImageResponse(
    (
      <div
        style={{
          alignItems: "center",
          background: "#164f47",
          color: "#fffaf0",
          display: "flex",
          fontSize: 280,
          fontWeight: 750,
          height: "100%",
          justifyContent: "center",
          letterSpacing: "-0.1em",
          width: "100%",
        }}
      >
        V
      </div>
    ),
    size,
  );
}
