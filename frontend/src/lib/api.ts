const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
const ADMIN_KEY = process.env.NEXT_PUBLIC_ADMIN_KEY ?? "demo-admin-key-change-me";

export async function registerVendor(data: { business_name: string; email: string }) {
  const res = await fetch(`${API_BASE}/api/vendors/`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Request failed" }));
    throw new Error(err.detail ?? "Failed to register vendor");
  }
  return res.json();
}

export async function createOnboardLink(vendorId: string) {
  const res = await fetch(`${API_BASE}/api/vendors/${vendorId}/onboard`, { method: "POST" });
  if (!res.ok) throw new Error("Failed to create onboarding link");
  return res.json() as Promise<{ onboarding_url: string }>;
}

export async function getVendor(vendorId: string) {
  const res = await fetch(`${API_BASE}/api/vendors/${vendorId}`);
  if (!res.ok) throw new Error("Vendor not found");
  return res.json();
}

export async function listAdminVendors() {
  const res = await fetch(`${API_BASE}/api/admin/vendors`, {
    headers: { "X-Admin-Key": ADMIN_KEY },
  });
  if (!res.ok) throw new Error("Unauthorized");
  return res.json();
}

export async function getAdminVendor(vendorId: string) {
  const res = await fetch(`${API_BASE}/api/admin/vendors/${vendorId}`, {
    headers: { "X-Admin-Key": ADMIN_KEY },
  });
  if (!res.ok) throw new Error("Vendor not found");
  return res.json();
}

export async function syncVendorStatus(vendorId: string) {
  const res = await fetch(`${API_BASE}/api/admin/vendors/${vendorId}/sync`, {
    method: "POST",
    headers: { "X-Admin-Key": ADMIN_KEY },
  });
  if (!res.ok) throw new Error("Sync failed");
  return res.json();
}
