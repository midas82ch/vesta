import { proxyAdminRequest, rejectCrossSiteMutation } from "@/lib/admin-api";

export async function POST(request: Request, context: { params: Promise<{ id: string }> }) {
  const rejection = rejectCrossSiteMutation(request);
  if (rejection) return rejection;
  const { id } = await context.params;
  return proxyAdminRequest(
    request,
    `/v1/admin/offer-import-jobs/${encodeURIComponent(id)}/retry`,
    "POST",
  );
}
