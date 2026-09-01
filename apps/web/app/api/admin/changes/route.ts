import { proxyAdminRequest } from "@/lib/admin-api";

export async function GET(request: Request) {
  const { search } = new URL(request.url);
  return proxyAdminRequest(request, `/v1/admin/changes${search}`, "GET");
}
