import type { VendorListResponse } from "@/lib/types";
import VendorCard from "@/components/vendor-card";
import Link from "next/link";

async function fetchVendors(): Promise<VendorListResponse> {
  const apiBase = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
  const adminKey = process.env.NEXT_PUBLIC_ADMIN_KEY ?? "demo-admin-key-change-me";
  const res = await fetch(`${apiBase}/api/admin/vendors`, {
    headers: { "X-Admin-Key": adminKey },
    cache: "no-store",
  });
  if (!res.ok) throw new Error("Failed to load vendors");
  return res.json();
}

export default async function AdminPage() {
  let data: VendorListResponse;
  try {
    data = await fetchVendors();
  } catch {
    return (
      <div className="py-10 text-center">
        <p className="text-red-600">Failed to connect to backend.</p>
      </div>
    );
  }

  const statusGroups = {
    complete: data.vendors.filter((v) => v.onboarding_status === "complete"),
    in_progress: data.vendors.filter((v) => v.onboarding_status === "in_progress"),
    pending: data.vendors.filter((v) => v.onboarding_status === "pending"),
    restricted: data.vendors.filter((v) => v.onboarding_status === "restricted"),
  };

  return (
    <div>
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-3xl font-bold text-brand">Admin Portal</h1>
          <p className="text-brand-muted text-sm mt-1">
            {data.total} vendor{data.total !== 1 ? "s" : ""} total
          </p>
        </div>
        <Link href="/vendor/register" className="btn-primary text-sm">
          + Add Vendor
        </Link>
      </div>

      <div className="grid grid-cols-4 gap-4 mb-10">
        {(["complete", "in_progress", "pending", "restricted"] as const).map((s) => (
          <div key={s} className="card text-center">
            <p className="text-3xl font-bold text-brand">{statusGroups[s].length}</p>
            <p className="text-xs text-brand-muted mt-1 capitalize">{s.replace("_", " ")}</p>
          </div>
        ))}
      </div>

      {data.vendors.length === 0 ? (
        <div className="text-center py-20">
          <p className="text-brand-muted">No vendors yet.</p>
          <Link href="/vendor/register" className="btn-primary mt-4 inline-block">
            Onboard first vendor
          </Link>
        </div>
      ) : (
        <div className="grid grid-cols-2 gap-4">
          {data.vendors.map((vendor) => (
            <VendorCard key={vendor.id} vendor={vendor} />
          ))}
        </div>
      )}
    </div>
  );
}
