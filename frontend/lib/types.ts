// Types matching backend Pydantic schemas

export interface Offer {
  id: string;
  dealer_id: string;
  dealer_name: string;
  dealer_city: string | null;

  // Vehicle info
  year: number;
  make: string;
  model: string;
  trim: string | null;

  // Offer details
  offer_type: "lease" | "finance";
  monthly_payment: string | null;
  down_payment: string | null;
  term_months: number | null;
  annual_mileage: number | null;
  apr: string | null;
  msrp: string | null;

  // Source & quality
  source_url: string | null;
  image_url: string | null;
  confidence_score: string;
  updated_at: string;
}

export interface Dealer {
  id: string;
  name: string;
  slug: string;
  city: string | null;
  state: string;
  website: string | null;
  specials_url: string;
  phone: string | null;
}

export interface ChatResponse {
  response: string;
  offers: Offer[];
  search_params: Record<string, unknown> | null;
  remaining_prompts: number | null;
  daily_limit: number | null;
  is_premium: boolean;
}

export interface ChatUsageResponse {
  used: number;
  limit: number;
  remaining: number;
  is_premium: boolean;
}

export interface SearchResponse {
  offers: Offer[];
  total: number;
  filters_applied: Record<string, unknown>;
}

export interface HealthResponse {
  status: string;
  offers_count: number;
  dealers_count: number;
  last_scrape: string | null;
}

export interface SearchParams {
  model?: string;
  max_monthly_payment?: number;
  offer_type?: "lease" | "finance";
  max_down_payment?: number;
  min_term_months?: number;
  max_term_months?: number;
  limit?: number;
  sort_by?: string;
}
