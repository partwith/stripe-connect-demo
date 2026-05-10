export interface VendorPublic {
  id: string;
  business_name: string;
  onboarding_status: "pending" | "in_progress" | "complete" | "restricted";
  charges_enabled: boolean;
  payouts_enabled: boolean;
  details_submitted: boolean;
}

export interface Vendor extends VendorPublic {
  email: string;
  stripe_account_id: string | null;
  created_at: string;
  updated_at: string;
}

export interface VendorListResponse {
  vendors: Vendor[];
  total: number;
}
