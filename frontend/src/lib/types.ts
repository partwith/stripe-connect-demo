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

export type OrderStatus = "pending" | "processing" | "paid" | "failed";

export interface Order {
  id: string;
  vendor_id: string;
  amount: number;
  application_fee_amount: number;
  idempotency_key: string;
  status: OrderStatus;
  stripe_payment_intent_id: string | null;
  created_at: string;
  updated_at: string;
}

export interface OrderListResponse {
  orders: Order[];
  total: number;
}
