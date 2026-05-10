import Link from "next/link";

export default function HomePage() {
  return (
    <div className="py-20 text-center">
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
  );
}
