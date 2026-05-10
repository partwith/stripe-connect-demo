// frontend/src/app/subscribe/[tier]/page.tsx
"use client";

import { useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { PLAN_DETAILS, type SubscriptionTier } from "@/lib/types";
import { createSubscription } from "@/lib/api";

export default function SubscribePage() {
  const { tier } = useParams<{ tier: string }>();
  const router = useRouter();
  const plan = PLAN_DETAILS[tier as SubscriptionTier];

  const [email, setEmail] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  if (!plan) {
    return (
      <div className="py-20 text-center">
        <p className="text-red-600">Unknown plan. <Link href="/" className="underline">Go back</Link>.</p>
      </div>
    );
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    if (!email.includes("@")) {
      setError("Please enter a valid email address.");
      return;
    }
    setLoading(true);
    try {
      const sub = await createSubscription({ email, plan_tier: tier });
      router.push(`/subscribe/confirm?id=${sub.id}&tier=${tier}`);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Subscription failed. Please try again.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="max-w-md mx-auto py-16">
      <Link href="/" className="text-sm text-brand-muted hover:text-brand inline-block mb-8">
        ← Back to Plans
      </Link>

      <div className="card space-y-6">
        <div>
          <h1 className="text-2xl font-bold text-brand">{plan.label} Plan</h1>
          <p className="text-brand-muted text-sm mt-1">{plan.description}</p>
        </div>

        <div className="bg-cream-blush rounded-lg p-4 space-y-2 text-sm">
          <div className="flex justify-between">
            <span className="text-brand-muted">Price</span>
            <span className="font-semibold text-brand">${plan.price} / year</span>
          </div>
          <div className="flex justify-between">
            <span className="text-brand-muted">AI Prompts</span>
            <span className="font-semibold text-brand">{plan.prompts.toLocaleString()}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-brand-muted">Billing</span>
            <span className="font-semibold text-brand">Annual (auto-renew)</span>
          </div>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-brand mb-1.5">
              Email address
            </label>
            <input
              type="email"
              required
              placeholder="you@example.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              disabled={loading}
              className="w-full px-3 py-2.5 border border-mauve rounded-lg text-sm text-brand bg-cream
                         focus:outline-none focus:ring-2 focus:ring-brand/20 focus:border-brand
                         disabled:opacity-50 disabled:cursor-not-allowed"
            />
          </div>

          <div className="border border-mauve rounded-lg p-3 space-y-2">
            <p className="text-xs font-medium text-brand-muted uppercase tracking-wide">Payment (Demo)</p>
            <div className="bg-cream-blush rounded px-3 py-2 text-sm text-brand-muted font-mono">
              4242 4242 4242 4242
            </div>
            <p className="text-xs text-brand-muted">
              This is a Stripe test environment. No real charges are made.
            </p>
          </div>

          {error && <p className="text-sm text-red-600">{error}</p>}

          <button
            type="submit"
            disabled={loading}
            className="btn-primary w-full py-3 text-sm disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? "Processing…" : `Subscribe for $${plan.price}/year`}
          </button>
        </form>
      </div>
    </div>
  );
}
