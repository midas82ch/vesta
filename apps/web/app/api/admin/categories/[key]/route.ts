import {
  proxyAdminRequest,
  rejectCrossSiteMutation,
} from "@/lib/admin-api";

export async function PUT(
  request: Request,
  context: { params: Promise<{ key: string }> },
) {
  const rejected = rejectCrossSiteMutation(request);
  if (rejected) return rejected;
  const { key } = await context.params;
  return proxyAdminRequest(
    request,
    `/v1/admin/categories/${encodeURIComponent(key)}`,
    "PUT",
  );
}
