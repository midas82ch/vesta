import {
  proxyAdminRequest,
  rejectCrossSiteMutation,
} from "@/lib/admin-api";

export async function POST(
  request: Request,
  context: { params: Promise<{ id: string }> },
) {
  const rejected = rejectCrossSiteMutation(request);
  if (rejected) return rejected;
  const { id } = await context.params;
  return proxyAdminRequest(
    request,
    `/v1/admin/offers/${encodeURIComponent(id)}/lifecycle`,
    "POST",
  );
}
