import { proxyAdminRequest, rejectCrossSiteMutation } from "@/lib/admin-api";

export async function GET(request: Request) {
  const search = new URL(request.url).search;
  return proxyAdminRequest(request, `/v1/admin/offer-import-jobs${search}`, "GET");
}

export async function POST(request: Request) {
  const rejection = rejectCrossSiteMutation(request);
  if (rejection) return rejection;
  return proxyAdminRequest(request, "/v1/admin/offer-import-jobs", "POST");
}
