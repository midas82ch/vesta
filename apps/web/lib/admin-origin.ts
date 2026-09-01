export function isAllowedAdminMutationOrigin(request: Request) {
  const origin = request.headers.get("origin");
  const requestUrl = new URL(request.url);
  const host = request.headers.get("host");
  const forwardedProtocol = request.headers.get("x-forwarded-proto");
  const protocol = forwardedProtocol
    ? forwardedProtocol.split(",", 1)[0].trim().replace(/:$/, "")
    : requestUrl.protocol.replace(/:$/, "");
  const allowedOrigins = new Set([requestUrl.origin]);
  if (host) allowedOrigins.add(`${protocol}://${host}`);
  return Boolean(origin && allowedOrigins.has(origin));
}
