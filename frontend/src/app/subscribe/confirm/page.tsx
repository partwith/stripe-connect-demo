// frontend/src/app/subscribe/confirm/page.tsx
"use client";

import { useSearchParams } from "next/navigation";
import Link from "next/link";
import { PLAN_DETAILS, type SubscriptionTier } from "@/lib/types";
import { Suspense } from "react";

function ConfirmContent() {
  const params = useSearchParams();
  const tier = params.get("tier") as SubscriptionTier | null;
  const id = params.get("id");
  const plan = tier ? PLAN_DETAILS[tier] : null;

  return (
    <div className="max-w-md mx-auto py-20 text-center space-y-6">
      <div className="text-5xl">✓</div>
      <h1 className="text-2xl font-bold text-brand">Subscription Activated!</h1>
      {plan && (
        <div className="card text-left space-y-3 text-sm">
          <div className="flex justify-between">
            <span className="text-brand-muted">Plan</span>
            <span className="font-semibold text-brand">{plan.label}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-brand-muted">AI Prompts</span>
            <span className="font-semibold text-brand">{plan.prompts.toLocaleString()}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-brand-muted">Subscription ID</span>
            <span className="font-mono text-xs text-brand-muted truncate max-w-[200px]">{id}</span>
          </div>
        </div>
      )}
      <p className="text-brand-muted text-sm">
        Your subscription is active for 1 year. You'll receive a renewal notice 3 days before expiry.
      </p>
      <Link href="/" className="btn-primary inline-block px-8 py-3 text-sm">
        Back to Home
      </Link>
    </div>
  );
}

export default function ConfirmPage() {
  return (
    <Suspense>
      <ConfirmContent />
    </Suspense>
  );
}
