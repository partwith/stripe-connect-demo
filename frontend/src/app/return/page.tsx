"use client";

import { Suspense, useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import Link from "next/link";
import { getVendor } from "@/lib/api";
import StatusBadge from "@/components/status-badge";
import type { VendorPublic } from "@/lib/types";

function ReturnContent() {
  const params = useSearchParams();
  const vendorId = params.get("vendor_id");
  const [vendor, setVendor] = useState<VendorPublic | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!vendorId) return;
    getVendor(vendorId)
      .then(setVendor)
      .catch(() => setError("Could not load vendor status."));
  }, [vendorId]);

  if (error) return <p className="text-red-600">{error}</p>;
  if (!vendor) return <p className="text-brand-muted">Loading your status…</p>;

  const isComplete = vendor.onboarding_status === "complete";

  return (
    <div className="max-w-md mx-auto py-10">
      <div className="card text-center space-y-4">
        <div className="text-4xl">{isComplete ? "🎉" : "⏳"}</div>
        <h1 className="text-2xl font-bold text-brand">
          {isComplete ? "You're all set!" : "Almost there"}
        </h1>
        <p className="text-brand-muted text-sm">
          {isComplete
            ? "Your Stripe account is connected. You can now receive payments."
            : "Stripe is still reviewing your information. We'll update your status automatically."}
        </p>
        <div className="flex justify-center">
          <StatusBadge status={vendor.onboarding_status} />
        </div>
        <div className="text-xs text-brand-muted space-y-1 pt-2">
          <p>
            Charges enabled:{" "}
            <span className="font-medium">{vendor.charges_enabled ? "Yes" : "No"}</span>
          </p>
          <p>
            Payouts enabled:{" "}
            <span className="font-medium">{vendor.payouts_enabled ? "Yes" : "No"}</span>
          </p>
        </div>
        <Link href="/" className="text-sm text-brand-muted hover:text-brand block">
          ← Back to home
        </Link>
      </div>
    </div>
  );
}

export default function ReturnPage() {
  return (
    <Suspense fallback={<p className="text-brand-muted text-center py-20">Loading…</p>}>
      <ReturnContent />
    </Suspense>
  );
}
