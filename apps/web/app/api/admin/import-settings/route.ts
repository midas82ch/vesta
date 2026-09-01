import {
  proxyAdminRequest,
  rejectCrossSiteMutation,
} from "@/lib/admin-api";

export async function GET(request: Request) {
  return proxyAdminRequest(request, "/v1/admin/import-settings", "GET");
}

export async function PUT(request: Request) {
  const rejected = rejectCrossSiteMutation(request);
  if (rejected) return rejected;
  return proxyAdminRequest(request, "/v1/admin/import-settings", "PUT");
}
