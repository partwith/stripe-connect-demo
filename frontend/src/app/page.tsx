// frontend/src/app/page.tsx
import Link from "next/link";
import { PLAN_DETAILS } from "@/lib/types";

export default function HomePage() {
  return (
    <div className="py-20">
      {/* Hero */}
      <div className="text-center mb-20">
        <h1 className="text-5xl font-bold text-brand mb-6 tracking-tight">
          Stripe Connect Demo
        </h1>
        <p className="text-xl text-brand-muted max-w-2xl mx-auto mb-12 leading-relaxed">
          A live demo of Stripe Connect onboarding for vendors and an admin portal
          to manage their payment account status.
        </p>
        <div className="flex justify-center gap-4">
          <Link href="/vendor/register" className="btn-primary text-base px-8 py-3">
            Vendor Onboarding
          </Link>
          <Link href="/admin" className="btn-outline text-base px-8 py-3">
            Admin Portal
          </Link>
        </div>
        <div className="mt-20 grid grid-cols-3 gap-8 text-left">
          {[
            {
              title: "Vendor Registration",
              desc: "Vendors sign up with their business name and email.",
            },
            {
              title: "Stripe Express Onboarding",
              desc: "Vendors complete identity and banking details via Stripe's hosted flow.",
            },
            {
              title: "Admin Review",
              desc: "Admins see live onboarding status, charges_enabled, and payouts_enabled.",
            },
          ].map((f) => (
            <div key={f.title} className="card">
              <h3 className="font-semibold text-brand mb-2">{f.title}</h3>
              <p className="text-sm text-brand-muted">{f.desc}</p>
            </div>
          ))}
        </div>
      </div>

      {/* Subscription Plans */}
      <div className="border-t border-mauve pt-20">
        <div className="text-center mb-12">
          <h2 className="text-3xl font-bold text-brand mb-3">Subscription Plans</h2>
          <p className="text-brand-muted max-w-xl mx-auto">
            Unlock AI prompt features with an annual plan. Billed once for 12 months — auto-renews 3 days before expiry.
          </p>
        </div>

        <div className="grid grid-cols-3 gap-6 max-w-4xl mx-auto">
          {(["basic", "standard", "premium"] as const).map((tier) => {
            const plan = PLAN_DETAILS[tier];
            const isPopular = tier === "standard";
            return (
              <div
                key={tier}
                className={`card flex flex-col gap-4 relative ${isPopular ? "ring-2 ring-brand" : ""}`}
              >
                {isPopular && (
                  <span className="absolute -top-3 left-1/2 -translate-x-1/2 bg-brand text-white text-xs font-semibold px-3 py-1 rounded-full">
                    Most Popular
                  </span>
                )}
                <div>
                  <h3 className="text-lg font-bold text-brand">{plan.label}</h3>
                  <p className="text-brand-muted text-sm mt-1">{plan.description}</p>
                </div>
                <div className="flex items-end gap-1">
                  <span className="text-4xl font-bold text-brand">${plan.price}</span>
                  <span className="text-brand-muted text-sm mb-1">/year</span>
                </div>
                <ul className="space-y-2 text-sm text-brand-muted flex-1">
                  <li className="flex items-center gap-2">
                    <span className="text-green-600 font-bold">✓</span>
                    {plan.prompts.toLocaleString()} AI prompts
                  </li>
                  <li className="flex items-center gap-2">
                    <span className="text-green-600 font-bold">✓</span>
                    Annual billing cycle
                  </li>
                  <li className="flex items-center gap-2">
                    <span className="text-green-600 font-bold">✓</span>
                    Auto-renew reminder 3 days early
                  </li>
                </ul>
                <Link
                  href={`/subscribe/${tier}`}
                  className="btn-primary text-center text-sm py-2.5 mt-2"
                >
                  Get {plan.label}
                </Link>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
