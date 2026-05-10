"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import StatusBadge from "@/components/status-badge";
import type { Vendor, Order } from "@/lib/types";
import { getAdminVendor, syncVendorStatus, createCharge, listOrders } from "@/lib/api";

type OrderStatusStyle = {
  label: string;
  classes: string;
};

const ORDER_STATUS_CONFIG: Record<string, OrderStatusStyle> = {
  pending:    { label: "Pending",    classes: "bg-mauve text-brand-mid" },
  processing: { label: "Processing", classes: "bg-accent text-brand" },
  paid:       { label: "Paid",       classes: "bg-green-100 text-green-800" },
  failed:     { label: "Failed",     classes: "bg-red-100 text-red-700" },
};

function OrderStatusBadge({ status }: { status: string }) {
  const s = ORDER_STATUS_CONFIG[status] ?? ORDER_STATUS_CONFIG.pending;
  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${s.classes}`}>
      {s.label}
    </span>
  );
}

function formatDollars(cents: number) {
  return `$${(cents / 100).toFixed(2)}`;
}

export default function VendorDetailPage() {
  const { id } = useParams<{ id: string }>();
  const [vendor, setVendor] = useState<Vendor | null>(null);
  const [orders, setOrders] = useState<Order[]>([]);
  const [syncing, setSyncing] = useState(false);
  const [charging, setCharging] = useState(false);
  const [amountInput, setAmountInput] = useState("");
  const [chargeError, setChargeError] = useState("");
  const [error, setError] = useState("");

  useEffect(() => {
    getAdminVendor(id)
      .then(setVendor)
      .catch(() => setError("Vendor not found."));
    refreshOrders();
  }, [id]);

  async function refreshOrders() {
    try {
      const data = await listOrders(id);
      setOrders(data.orders);
    } catch {
      // non-fatal — orders table stays empty
    }
  }

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

  async function handleCharge(e: React.FormEvent) {
    e.preventDefault();
    setChargeError("");
    const dollars = parseFloat(amountInput);
    if (isNaN(dollars) || dollars <= 0) {
      setChargeError("Enter a valid amount greater than $0.");
      return;
    }
    const cents = Math.round(dollars * 100);
    setCharging(true);
    try {
      await createCharge(id, cents);
      setAmountInput("");
      await refreshOrders();
    } catch (err: unknown) {
      setChargeError(err instanceof Error ? err.message : "Charge failed.");
    } finally {
      setCharging(false);
    }
  }

  if (error) return <p className="text-red-600 py-10 text-center">{error}</p>;
  if (!vendor) return <p className="text-brand-muted py-10 text-center">Loading…</p>;

  const canCharge = vendor.charges_enabled && vendor.stripe_account_id;

  return (
    <div className="max-w-2xl mx-auto py-10 space-y-6">
      <Link
        href="/admin"
        className="text-sm text-brand-muted hover:text-brand inline-block"
      >
        ← Back to Admin
      </Link>

      {/* Vendor Info Card */}
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
            { label: "Created", value: new Date(vendor.created_at).toLocaleDateString() },
            { label: "Charges Enabled", value: vendor.charges_enabled ? "Yes ✓" : "No ✗" },
            { label: "Payouts Enabled", value: vendor.payouts_enabled ? "Yes ✓" : "No ✗" },
            { label: "Details Submitted", value: vendor.details_submitted ? "Yes ✓" : "No ✗" },
            { label: "Last Updated", value: new Date(vendor.updated_at).toLocaleString() },
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

      {/* Charge Demo Card */}
      <div className="card space-y-4">
        <h2 className="text-lg font-semibold text-brand">Charge Demo</h2>
        <p className="text-sm text-brand-muted">
          Creates a destination charge via Stripe. Platform keeps a <strong>10% application fee</strong>.
        </p>
        {!canCharge && (
          <p className="text-sm text-red-600 bg-red-50 border border-red-200 rounded-lg px-3 py-2">
            Charges are not enabled for this vendor. Complete KYC onboarding first.
          </p>
        )}
        <form onSubmit={handleCharge} className="flex gap-2">
          <div className="relative flex-1">
            <span className="absolute left-3 top-1/2 -translate-y-1/2 text-brand-muted text-sm">$</span>
            <input
              type="number"
              min="0.01"
              step="0.01"
              placeholder="100.00"
              value={amountInput}
              onChange={(e) => setAmountInput(e.target.value)}
              disabled={!canCharge || charging}
              className="w-full pl-7 pr-3 py-2.5 border border-mauve rounded-lg text-sm text-brand bg-cream
                         focus:outline-none focus:ring-2 focus:ring-brand/20 focus:border-brand
                         disabled:opacity-50 disabled:cursor-not-allowed"
            />
          </div>
          <button
            type="submit"
            disabled={!canCharge || charging}
            className="btn-primary py-2.5 px-5 disabled:opacity-50 disabled:cursor-not-allowed whitespace-nowrap text-sm"
          >
            {charging ? "Charging…" : "Create Charge"}
          </button>
        </form>
        {chargeError && (
          <p className="text-sm text-red-600">{chargeError}</p>
        )}
      </div>

      {/* Orders Table */}
      <div className="card space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-semibold text-brand">Orders</h2>
          <button
            onClick={refreshOrders}
            className="text-xs text-brand-muted hover:text-brand transition-colors"
          >
            Refresh
          </button>
        </div>
        {orders.length === 0 ? (
          <p className="text-sm text-brand-muted text-center py-6">No orders yet. Create a charge above.</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-left text-xs text-brand-muted border-b border-mauve">
                  <th className="pb-2 pr-4 font-medium">Total</th>
                  <th className="pb-2 pr-4 font-medium">App Fee (10%)</th>
                  <th className="pb-2 pr-4 font-medium">Idempotency Key</th>
                  <th className="pb-2 pr-4 font-medium">Status</th>
                  <th className="pb-2 font-medium">Created</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-mauve/50">
                {orders.map((order) => (
                  <tr key={order.id}>
                    <td className="py-2.5 pr-4 font-medium text-brand">
                      {formatDollars(order.amount)}
                    </td>
                    <td className="py-2.5 pr-4 text-brand-muted">
                      {formatDollars(order.application_fee_amount)}
                    </td>
                    <td className="py-2.5 pr-4 font-mono text-xs text-brand-muted truncate max-w-[160px]">
                      {order.idempotency_key}
                    </td>
                    <td className="py-2.5 pr-4">
                      <OrderStatusBadge status={order.status} />
                    </td>
                    <td className="py-2.5 text-brand-muted text-xs">
                      {new Date(order.created_at).toLocaleString()}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
