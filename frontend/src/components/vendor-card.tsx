import Link from "next/link";
import StatusBadge from "./status-badge";
import type { Vendor } from "@/lib/types";

export default function VendorCard({ vendor }: { vendor: Vendor }) {
  return (
    <div className="card hover:shadow-md transition-shadow">
      <div className="flex items-start justify-between mb-3">
        <div>
          <p className="font-semibold text-brand">{vendor.business_name}</p>
          <p className="text-sm text-brand-muted">{vendor.email}</p>
        </div>
        <StatusBadge status={vendor.onboarding_status} />
      </div>
      <div className="flex gap-4 text-xs text-brand-muted mb-4">
        <span>
          Charges:{" "}
          <span className="font-medium text-brand-light">
            {vendor.charges_enabled ? "✓" : "✗"}
          </span>
        </span>
        <span>
          Payouts:{" "}
          <span className="font-medium text-brand-light">
            {vendor.payouts_enabled ? "✓" : "✗"}
          </span>
        </span>
        <span>
          Details:{" "}
          <span className="font-medium text-brand-light">
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
