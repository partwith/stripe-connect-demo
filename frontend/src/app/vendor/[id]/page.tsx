import type { VendorPublic } from "@/lib/types";
import StatusBadge from "@/components/status-badge";
import Link from "next/link";

async function getVendorServer(id: string): Promise<VendorPublic> {
  const apiBase = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
  const res = await fetch(`${apiBase}/api/vendors/${id}`, { cache: "no-store" });
  if (!res.ok) throw new Error("Vendor not found");
  return res.json();
}

export default async function VendorStatusPage({
  params,
}: {
  params: { id: string };
}) {
  let vendor: VendorPublic;
  try {
    vendor = await getVendorServer(params.id);
  } catch {
    return (
      <div className="max-w-md mx-auto py-10 text-center">
        <p className="text-red-600">Vendor not found.</p>
        <Link href="/" className="btn-primary mt-4 inline-block">
          Home
        </Link>
      </div>
    );
  }

  return (
    <div className="max-w-md mx-auto py-10">
      <div className="card space-y-3">
        <div className="flex items-start justify-between">
          <div>
            <h2 className="text-xl font-bold text-brand">{vendor.business_name}</h2>
            <p className="text-sm text-brand-muted">{vendor.email}</p>
          </div>
          <StatusBadge status={vendor.onboarding_status} />
        </div>
        <hr className="border-mauve" />
        <div className="grid grid-cols-2 gap-3 text-sm">
          <div className="bg-cream-blush rounded-lg p-3">
            <p className="text-brand-muted text-xs mb-1">Charges enabled</p>
            <p className="font-semibold text-brand">{vendor.charges_enabled ? "Yes" : "No"}</p>
          </div>
          <div className="bg-cream-blush rounded-lg p-3">
            <p className="text-brand-muted text-xs mb-1">Payouts enabled</p>
            <p className="font-semibold text-brand">{vendor.payouts_enabled ? "Yes" : "No"}</p>
          </div>
        </div>
        <Link href="/" className="text-sm text-brand-muted hover:text-brand block pt-2">
          ← Back to home
        </Link>
      </div>
    </div>
  );
}
