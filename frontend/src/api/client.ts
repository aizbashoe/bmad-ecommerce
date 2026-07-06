// Single typed API-client module (AD-5). Every network call to the backend goes
// through here; components never fetch directly. Base URL is 12-factor config.

// `||` (not `??`) so an explicitly empty VITE_API_BASE_URL falls back rather than
// collapsing to a relative URL against the frontend origin.
const API_BASE_URL: string =
  (import.meta.env.VITE_API_BASE_URL as string | undefined) || "http://localhost:8000";

const DEFAULT_TIMEOUT_MS = 5000;

export interface HealthResponse {
  status: string;
}

async function get<T>(path: string, timeoutMs: number = DEFAULT_TIMEOUT_MS): Promise<T> {
  // Abort a stalled request so callers surface an error instead of hanging forever.
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);
  try {
    const res = await fetch(`${API_BASE_URL}${path}`, { signal: controller.signal });
    if (!res.ok) {
      throw new Error(`Request failed: ${res.status}`);
    }
    return (await res.json()) as T;
  } finally {
    clearTimeout(timer);
  }
}

export function getHealth(): Promise<HealthResponse> {
  return get<HealthResponse>("/health");
}

// --- Catalog (Story 1.3) ---

export interface ProductSummary {
  productId: string;
  name: string;
  price: number; // integer minor units (cents); formatted for display in the UI only
  imageUrl: string;
  category: string;
  available: boolean;
}

export interface ProductPage {
  items: ProductSummary[];
  nextCursor: string | null;
}

export function listProducts(
  params: { limit?: number; cursor?: string; search?: string; categories?: string[] } = {},
): Promise<ProductPage> {
  const qs = new URLSearchParams();
  if (params.limit != null) qs.set("limit", String(params.limit));
  if (params.cursor) qs.set("cursor", params.cursor);
  if (params.search) qs.set("search", params.search);
  for (const c of params.categories ?? []) qs.append("category", c); // repeat for multiple
  const suffix = qs.toString() ? `?${qs}` : "";
  return get<ProductPage>(`/products${suffix}`);
}

export interface CategoryList {
  categories: string[];
}

export function listCategories(): Promise<CategoryList> {
  return get<CategoryList>("/products/categories");
}

/** Format integer cents as a display price. The only place cents becomes a string (AD-6). */
export function formatPrice(cents: number): string {
  return `$${(cents / 100).toFixed(2)}`;
}
