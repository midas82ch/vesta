import { proxyAdminRequest } from "@/lib/admin-api";

export async function GET(request: Request, context: { params: Promise<{ id: string }> }) {
  const { id } = await context.params;
  return proxyAdminRequest(
    request,
    `/v1/admin/offer-import-jobs/${encodeURIComponent(id)}`,
    "GET",
  );
}
