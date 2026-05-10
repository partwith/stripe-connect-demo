import Link from "next/link";

export default function Nav() {
  return (
    <nav className="border-b border-gray-200 bg-white sticky top-0 z-10">
      <div className="max-w-6xl mx-auto px-6 py-4 flex items-center justify-between">
        <Link href="/" className="text-xl font-bold text-brand tracking-tight">
          ConnectDemo
        </Link>
        <div className="flex items-center gap-6 text-sm font-medium text-gray-600">
          <Link href="/vendor/register" className="hover:text-brand transition-colors">
            Become a Vendor
          </Link>
          <Link href="/admin" className="hover:text-brand transition-colors">
            Admin Portal
          </Link>
          <Link href="/vendor/register" className="btn-primary">
            Get Started
          </Link>
        </div>
      </div>
    </nav>
  );
}
