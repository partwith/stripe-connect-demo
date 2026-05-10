import Link from "next/link";
import StatusBadge from "./status-badge";
import type { Vendor } from "@/lib/types";

export default function VendorCard({ vendor }: { vendor: Vendor }) {
  return (
    <div className="card hover:shadow-md transition-shadow">
      <div className="flex items-start justify-between mb-3">
        <div>
          <p className="font-semibold text-gray-900">{vendor.business_name}</p>
          <p className="text-sm text-gray-500">{vendor.email}</p>
        </div>
        <StatusBadge status={vendor.onboarding_status} />
      </div>
      <div className="flex gap-4 text-xs text-gray-500 mb-4">
        <span>
          Charges:{" "}
          <span className="font-medium text-gray-700">
            {vendor.charges_enabled ? "✓" : "✗"}
          </span>
        </span>
        <span>
          Payouts:{" "}
          <span className="font-medium text-gray-700">
            {vendor.payouts_enabled ? "✓" : "✗"}
          </span>
        </span>
        <span>
          Details:{" "}
          <span className="font-medium text-gray-700">
            {vendor.details_submitted ? "✓" : "✗"}
          </span>
        </span>
      </div>
      <Link
        href={`/admin/${vendor.id}`}
        className="text-xs font-medium text-brand hover:underline"
      >
        View details →
      </Link>
    </div>
  );
}
