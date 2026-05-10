"use client";

import { useState } from "react";
import { registerVendor, createOnboardLink } from "@/lib/api";

export default function RegisterPage() {
  const [form, setForm] = useState({ business_name: "", email: "" });
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const vendor = await registerVendor(form);
      const { onboarding_url } = await createOnboardLink(vendor.id);
      window.location.href = onboarding_url;
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Something went wrong");
      setLoading(false);
    }
  }

  return (
    <div className="max-w-md mx-auto py-10">
      <h1 className="text-3xl font-bold text-brand mb-2">Become a Vendor</h1>
      <p className="text-brand-muted mb-8 text-sm">
        Register your business and connect your bank account via Stripe.
      </p>
      <form onSubmit={handleSubmit} className="card space-y-5">
        <div>
          <label className="block text-sm font-medium text-brand mb-1">
            Business Name
          </label>
          <input
            type="text"
            required
            value={form.business_name}
            onChange={(e) => setForm({ ...form, business_name: e.target.value })}
            className="w-full border border-mauve rounded-lg px-3 py-2 text-sm text-brand
                       focus:outline-none focus:ring-2 focus:ring-brand focus:border-transparent bg-cream"
            placeholder="Acme Corp"
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-brand mb-1">
            Email Address
          </label>
          <input
            type="email"
            required
            value={form.email}
            onChange={(e) => setForm({ ...form, email: e.target.value })}
            className="w-full border border-mauve rounded-lg px-3 py-2 text-sm text-brand
                       focus:outline-none focus:ring-2 focus:ring-brand focus:border-transparent bg-cream"
            placeholder="you@example.com"
          />
        </div>
        {error && (
          <p className="text-red-600 text-sm bg-red-50 rounded-lg px-3 py-2">{error}</p>
        )}
        <button
          type="submit"
          disabled={loading}
          className="btn-primary w-full py-3 disabled:opacity-50 disabled:cursor-not-allowed text-center"
        >
          {loading ? "Connecting to Stripe…" : "Continue to Stripe Onboarding"}
        </button>
      </form>
    </div>
  );
}
