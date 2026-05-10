import type { Vendor } from "@/lib/types";
import StatusBadge from "@/components/status-badge";
import Link from "next/link";

async function getVendorServer(id: string): Promise<Vendor> {
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
  let vendor: Vendor;
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
            <p className="text-sm text-gray-500">{vendor.email}</p>
          </div>
          <StatusBadge status={vendor.onboarding_status} />
        </div>
        <hr className="border-gray-100" />
        <div className="grid grid-cols-2 gap-3 text-sm">
          <div className="bg-gray-50 rounded-lg p-3">
            <p className="text-gray-500 text-xs mb-1">Charges enabled</p>
            <p className="font-semibold">{vendor.charges_enabled ? "Yes" : "No"}</p>
          </div>
          <div className="bg-gray-50 rounded-lg p-3">
            <p className="text-gray-500 text-xs mb-1">Payouts enabled</p>
            <p className="font-semibold">{vendor.payouts_enabled ? "Yes" : "No"}</p>
          </div>
        </div>
        <Link href="/" className="text-sm text-gray-400 hover:text-brand block pt-2">
          ← Back to home
        </Link>
      </div>
    </div>
  );
}
