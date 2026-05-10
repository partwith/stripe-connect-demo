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

export type SubscriptionTier = "basic" | "standard" | "premium";
export type SubscriptionStatus = "active" | "expired" | "cancelled";

export interface Subscription {
  id: string;
  email: string;
  stripe_customer_id: string;
  plan_tier: SubscriptionTier;
  plan_amount_cents: number;
  ai_prompt_usage_limit: number;
  ai_prompt_usage_used: number;
  status: SubscriptionStatus;
  stripe_payment_intent_id: string | null;
  idempotency_key: string;
  starts_at: string;
  expires_at: string;
  next_charge_due_at: string;
  created_at: string;
  updated_at: string;
}

export interface SubscriptionListResponse {
  subscriptions: Subscription[];
  total: number;
}

export const PLAN_DETAILS: Record<SubscriptionTier, { label: string; price: number; prompts: number; description: string }> = {
  basic:    { label: "Basic",    price: 10,  prompts: 100,  description: "Get started with AI-powered features." },
  standard: { label: "Standard", price: 40,  prompts: 500,  description: "For growing teams with moderate usage." },
  premium:  { label: "Premium",  price: 100, prompts: 2000, description: "Unlimited power for enterprise workloads." },
};
