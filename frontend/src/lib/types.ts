export interface Vendor {
  id: string;
  business_name: string;
  email: string;
  stripe_account_id: string | null;
  onboarding_status: "pending" | "in_progress" | "complete" | "restricted";
  charges_enabled: boolean;
  payouts_enabled: boolean;
  details_submitted: boolean;
  created_at: string;
  updated_at: string;
}

export interface VendorListResponse {
  vendors: Vendor[];
  total: number;
}
