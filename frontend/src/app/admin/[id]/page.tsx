"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import StatusBadge from "@/components/status-badge";
import type { Vendor } from "@/lib/types";
import { getAdminVendor, syncVendorStatus } from "@/lib/api";

export default function VendorDetailPage() {
  const { id } = useParams<{ id: string }>();
  const [vendor, setVendor] = useState<Vendor | null>(null);
  const [syncing, setSyncing] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    getAdminVendor(id)
      .then(setVendor)
      .catch(() => setError("Vendor not found."));
  }, [id]);

  async function handleSync() {
    if (!vendor) return;
    setSyncing(true);
    try {
      const updated = await syncVendorStatus(id);
      setVendor(updated);
    } catch {
      setError("Sync failed.");
    } finally {
      setSyncing(false);
    }
  }

  if (error) return <p className="text-red-600 py-10 text-center">{error}</p>;
  if (!vendor) return <p className="text-brand-muted py-10 text-center">Loading…</p>;

  return (
    <div className="max-w-xl mx-auto py-10">
      <Link
        href="/admin"
        className="text-sm text-brand-muted hover:text-brand mb-6 inline-block"
      >
        ← Back to Admin
      </Link>
      <div className="card space-y-4">
        <div className="flex items-start justify-between">
          <div>
            <h1 className="text-2xl font-bold text-brand">{vendor.business_name}</h1>
            <p className="text-sm text-brand-muted">{vendor.email}</p>
          </div>
          <StatusBadge status={vendor.onboarding_status} />
        </div>
        <hr className="border-mauve" />
        <div className="grid grid-cols-2 gap-3 text-sm">
          {[
            { label: "Stripe Account", value: vendor.stripe_account_id ?? "—" },
            {
              label: "Created",
              value: new Date(vendor.created_at).toLocaleDateString(),
            },
            {
              label: "Charges Enabled",
              value: vendor.charges_enabled ? "Yes ✓" : "No ✗",
            },
            {
              label: "Payouts Enabled",
              value: vendor.payouts_enabled ? "Yes ✓" : "No ✗",
            },
            {
              label: "Details Submitted",
              value: vendor.details_submitted ? "Yes ✓" : "No ✗",
            },
            {
              label: "Last Updated",
              value: new Date(vendor.updated_at).toLocaleString(),
            },
          ].map(({ label, value }) => (
            <div key={label} className="bg-cream-blush rounded-lg p-3">
              <p className="text-brand-muted text-xs mb-1">{label}</p>
              <p className="font-medium text-brand text-sm truncate">{value}</p>
            </div>
          ))}
        </div>
        <button
          onClick={handleSync}
          disabled={syncing}
          className="btn-primary w-full py-2.5 disabled:opacity-50 disabled:cursor-not-allowed text-center text-sm"
        >
          {syncing ? "Syncing with Stripe…" : "Sync Stripe Status"}
        </button>
      </div>
    </div>
  );
}
