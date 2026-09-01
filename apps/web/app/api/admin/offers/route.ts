import {
  proxyAdminRequest,
  rejectCrossSiteMutation,
} from "@/lib/admin-api";

export async function GET(request: Request) {
  const { search } = new URL(request.url);
  return proxyAdminRequest(request, `/v1/admin/offers${search}`, "GET");
}

export async function POST(request: Request) {
  const rejected = rejectCrossSiteMutation(request);
  if (rejected) return rejected;
  return proxyAdminRequest(request, "/v1/admin/offers", "POST");
}
