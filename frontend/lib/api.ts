import { ChatResponse, ChatUsageResponse, SearchResponse, HealthResponse, SearchParams, Offer } from "./types";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
const API_KEY = process.env.NEXT_PUBLIC_API_KEY || "";

class ApiError extends Error {
  status: number;
  data?: Record<string, unknown>;

  constructor(status: number, message: string, data?: Record<string, unknown>) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.data = data;
  }
}

async function fetchApi<T>(
  endpoint: string,
  options: RequestInit = {},
  authToken?: string
): Promise<T> {
  const url = `${API_URL}${endpoint}`;

  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(options.headers as Record<string, string>),
  };

  // Include auth token if provided
  if (authToken) {
    headers["Authorization"] = `Bearer ${authToken}`;
  }

  // Include API key if configured (fallback for non-auth endpoints)
  if (API_KEY && !authToken) {
    headers["X-API-Key"] = API_KEY;
  }

  const response = await fetch(url, {
    ...options,
    headers,
  });

  if (!response.ok) {
    let data: Record<string, unknown> | undefined;
    try {
      data = await response.json();
    } catch {
      // Response may not be JSON
    }
    throw new ApiError(response.status, `API Error: ${response.statusText}`, data);
  }

  return response.json();
}

// Chat API
export async function sendChat(message: string, authToken?: string): Promise<ChatResponse> {
  return fetchApi<ChatResponse>("/api/chat", {
    method: "POST",
    body: JSON.stringify({ message }),
  }, authToken);
}

// Chat usage check
export async function getChatUsage(authToken: string): Promise<ChatUsageResponse> {
  return fetchApi<ChatUsageResponse>("/api/chat/usage", {}, authToken);
}

// Search API
export async function searchOffers(params: SearchParams = {}): Promise<SearchResponse> {
  const queryParams = new URLSearchParams();

  if (params.model) queryParams.set("model", params.model);
  if (params.max_monthly_payment) queryParams.set("max_monthly_payment", params.max_monthly_payment.toString());
  if (params.offer_type) queryParams.set("offer_type", params.offer_type);
  if (params.max_down_payment) queryParams.set("max_down_payment", params.max_down_payment.toString());
  if (params.min_term_months) queryParams.set("min_term_months", params.min_term_months.toString());
  if (params.max_term_months) queryParams.set("max_term_months", params.max_term_months.toString());
  if (params.limit) queryParams.set("limit", params.limit.toString());
  if (params.sort_by) queryParams.set("sort_by", params.sort_by);

  const queryString = queryParams.toString();
  const endpoint = queryString ? `/api/offers/search?${queryString}` : "/api/offers/search";

  return fetchApi<SearchResponse>(endpoint);
}

// Get single offer
export async function getOffer(id: string): Promise<Offer> {
  return fetchApi<Offer>(`/api/offers/${id}`);
}

// Health check
export async function getHealth(): Promise<HealthResponse> {
  return fetchApi<HealthResponse>("/api/health");
}

export { ApiError };
