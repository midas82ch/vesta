import { proxyAdminRequest, rejectCrossSiteMutation } from "@/lib/admin-api";

export async function PUT(
  request: Request,
  context: { params: Promise<{ id: string; locale: string }> },
) {
  const rejection = rejectCrossSiteMutation(request);
  if (rejection) return rejection;
  const { id, locale } = await context.params;
  return proxyAdminRequest(
    request,
    `/v1/admin/offers/${encodeURIComponent(id)}/localizations/${encodeURIComponent(locale)}`,
    "PUT",
  );
}
