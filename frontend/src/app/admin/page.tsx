// frontend/src/app/admin/page.tsx
import type { VendorListResponse, SubscriptionListResponse, SubscriptionTier } from "@/lib/types";
import { PLAN_DETAILS } from "@/lib/types";
import VendorCard from "@/components/vendor-card";
import Link from "next/link";

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
const ADMIN_KEY = process.env.NEXT_PUBLIC_ADMIN_KEY ?? "demo-admin-key-change-me";

async function fetchVendors(): Promise<VendorListResponse> {
  const res = await fetch(`${API_BASE}/api/admin/vendors`, {
    headers: { "X-Admin-Key": ADMIN_KEY },
    cache: "no-store",
  });
  if (!res.ok) throw new Error("Failed to load vendors");
  return res.json();
}

async function fetchSubscriptions(): Promise<SubscriptionListResponse> {
  const res = await fetch(`${API_BASE}/api/admin/subscriptions`, {
    headers: { "X-Admin-Key": ADMIN_KEY },
    cache: "no-store",
  });
  if (!res.ok) throw new Error("Failed to load subscriptions");
  return res.json();
}

function formatDate(iso: string) {
  return new Date(iso).toLocaleDateString(undefined, { year: "numeric", month: "short", day: "numeric" });
}

const STATUS_CLASSES: Record<string, string> = {
  active:    "bg-green-100 text-green-800",
  expired:   "bg-red-100 text-red-700",
  cancelled: "bg-mauve text-brand-muted",
};

export default async function AdminPage() {
  let vendors: VendorListResponse;
  let subscriptions: SubscriptionListResponse;

  try {
    [vendors, subscriptions] = await Promise.all([fetchVendors(), fetchSubscriptions()]);
  } catch {
    return (
      <div className="py-10 text-center">
        <p className="text-red-600">Failed to connect to backend.</p>
      </div>
    );
  }

  const statusGroups = {
    complete:    vendors.vendors.filter((v) => v.onboarding_status === "complete"),
    in_progress: vendors.vendors.filter((v) => v.onboarding_status === "in_progress"),
    pending:     vendors.vendors.filter((v) => v.onboarding_status === "pending"),
    restricted:  vendors.vendors.filter((v) => v.onboarding_status === "restricted"),
  };

  return (
    <div className="space-y-16">
      {/* ── Section 1: Stripe Connect Vendors ── */}
      <section>
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-3xl font-bold text-brand">Stripe Connect Vendors</h1>
            <p className="text-brand-muted text-sm mt-1">
              {vendors.total} vendor{vendors.total !== 1 ? "s" : ""} total
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

        {vendors.vendors.length === 0 ? (
          <div className="text-center py-20">
            <p className="text-brand-muted">No vendors yet.</p>
            <Link href="/vendor/register" className="btn-primary mt-4 inline-block">
              Onboard first vendor
            </Link>
          </div>
        ) : (
          <div className="grid grid-cols-2 gap-4">
            {vendors.vendors.map((vendor) => (
              <VendorCard key={vendor.id} vendor={vendor} />
            ))}
          </div>
        )}
      </section>

      {/* ── Section 2: Subscription Customers ── */}
      <section>
        <div className="mb-8">
          <h2 className="text-3xl font-bold text-brand">Subscription Customers</h2>
          <p className="text-brand-muted text-sm mt-1">
            {subscriptions.total} subscription{subscriptions.total !== 1 ? "s" : ""} total
          </p>
        </div>

        {subscriptions.subscriptions.length === 0 ? (
          <div className="card text-center py-12">
            <p className="text-brand-muted">No subscriptions yet.</p>
            <Link href="/" className="btn-outline mt-4 inline-block text-sm">
              View Plans
            </Link>
          </div>
        ) : (
          <div className="card overflow-x-auto p-0">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-left text-xs text-brand-muted border-b border-mauve">
                  <th className="px-4 py-3 font-medium">Email</th>
                  <th className="px-4 py-3 font-medium">Plan</th>
                  <th className="px-4 py-3 font-medium">AI Prompts</th>
                  <th className="px-4 py-3 font-medium">Expires</th>
                  <th className="px-4 py-3 font-medium">Next Charge</th>
                  <th className="px-4 py-3 font-medium">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-mauve/50">
                {subscriptions.subscriptions.map((sub) => {
                  const plan = PLAN_DETAILS[sub.plan_tier as SubscriptionTier];
                  const usageLeft = sub.ai_prompt_usage_limit - sub.ai_prompt_usage_used;
                  const statusClass = STATUS_CLASSES[sub.status] ?? STATUS_CLASSES.cancelled;
                  return (
                    <tr key={sub.id} className="hover:bg-cream-blush/30 transition-colors">
                      <td className="px-4 py-3 text-brand font-medium">{sub.email}</td>
                      <td className="px-4 py-3">
                        <span className="font-semibold text-brand">{plan?.label ?? sub.plan_tier}</span>
                        <span className="text-brand-muted ml-1 text-xs">(${(sub.plan_amount_cents / 100).toFixed(0)}/yr)</span>
                      </td>
                      <td className="px-4 py-3">
                        <span className="text-brand">{usageLeft.toLocaleString()}</span>
                        <span className="text-brand-muted"> / {sub.ai_prompt_usage_limit.toLocaleString()} left</span>
                      </td>
                      <td className="px-4 py-3 text-brand-muted">{formatDate(sub.expires_at)}</td>
                      <td className="px-4 py-3 text-brand-muted">{formatDate(sub.next_charge_due_at)}</td>
                      <td className="px-4 py-3">
                        <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium capitalize ${statusClass}`}>
                          {sub.status}
                        </span>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </div>
  );
}
