import {
  proxyAdminRequest,
  rejectCrossSiteMutation,
} from "@/lib/admin-api";

export async function GET(request: Request) {
  return proxyAdminRequest(request, "/v1/admin/services", "GET");
}

export async function POST(request: Request) {
  const rejected = rejectCrossSiteMutation(request);
  if (rejected) return rejected;
  return proxyAdminRequest(request, "/v1/admin/services", "POST");
}
