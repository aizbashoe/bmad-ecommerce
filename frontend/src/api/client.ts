// Single typed API-client module (AD-5). Every network call to the backend goes
// through here; components never fetch directly. Base URL is 12-factor config.

import { clearGuestToken, getGuestToken, setGuestToken } from "../state/guestSession";

// `||` (not `??`) so an explicitly empty VITE_API_BASE_URL falls back rather than
// collapsing to a relative URL against the frontend origin.
const API_BASE_URL: string =
  (import.meta.env.VITE_API_BASE_URL as string | undefined) || "http://localhost:8000";

const DEFAULT_TIMEOUT_MS = 5000;

export interface HealthResponse {
  status: string;
}

/**
 * A structured API failure carrying the backend's `{error:{code,message}}` envelope (AD-5).
 * Lets callers branch on `code`/`status` (e.g. render a 404 not-found state distinctly from a
 * generic error). A network/abort/timeout failure throws a plain Error instead — not an ApiError.
 */
export class ApiError extends Error {
  readonly status: number;
  readonly code: string;
  constructor(status: number, code: string, message: string) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.code = code;
  }
}

async function get<T>(path: string, timeoutMs: number = DEFAULT_TIMEOUT_MS): Promise<T> {
  // Abort a stalled request so callers surface an error instead of hanging forever.
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);
  try {
    const res = await fetch(`${API_BASE_URL}${path}`, { signal: controller.signal });
    if (!res.ok) {
      // Parse the {error:{code,message}} envelope so callers can distinguish, e.g., a 404
      // not_found from a 400 invalid_cursor. Fall back if the body isn't the expected shape.
      let code = "http_error";
      let message = `Request failed: ${res.status}`;
      try {
        const body = (await res.json()) as { error?: { code?: string; message?: string } };
        if (body?.error?.code) code = body.error.code;
        if (body?.error?.message) message = body.error.message;
      } catch (err) {
        // If the abort/timeout fired while reading the body, it's a generic failure — not
        // an ApiError (keeps the "network/abort -> plain Error" contract). Otherwise the
        // body just wasn't the expected JSON envelope; keep the fallbacks.
        if (controller.signal.aborted) throw err;
      }
      throw new ApiError(res.status, code, message);
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

export type SortOption = "price_asc" | "price_desc";

export function listProducts(
  params: {
    limit?: number;
    cursor?: string;
    search?: string;
    categories?: string[];
    sort?: SortOption;
  } = {},
): Promise<ProductPage> {
  const qs = new URLSearchParams();
  if (params.limit != null) qs.set("limit", String(params.limit));
  if (params.cursor) qs.set("cursor", params.cursor);
  if (params.search) qs.set("search", params.search);
  for (const c of params.categories ?? []) qs.append("category", c); // repeat for multiple
  if (params.sort) qs.set("sort", params.sort);
  const suffix = qs.toString() ? `?${qs}` : "";
  return get<ProductPage>(`/products${suffix}`);
}

export interface CategoryList {
  categories: string[];
}

export function listCategories(): Promise<CategoryList> {
  return get<CategoryList>("/products/categories");
}

// --- Product detail / PDP (Story 2.1) ---

export interface ProductDetail extends ProductSummary {
  description: string;
}

/** Fetch one product's full detail. A missing id throws ApiError{status:404, code:"not_found"}. */
export function getProduct(productId: string): Promise<ProductDetail> {
  return get<ProductDetail>(`/products/${encodeURIComponent(productId)}`);
}

// --- Cart / guest session (Story 3.1) ---

const GUEST_TOKEN_HEADER = "X-Guest-Token";

export interface Cart {
  guestId: string;
  items: []; // line items arrive in Story 3.2
}

/**
 * Resolve (or establish) the anonymous cart (AD-2). Sends the stored guest token when present,
 * persists the token the API echoes back in the X-Guest-Token response header, and returns the
 * cart. Preserves the abort-timeout + {error:{code,message}} -> ApiError behavior of `get<T>`.
 */
export async function getCart(timeoutMs: number = DEFAULT_TIMEOUT_MS): Promise<Cart> {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);
  try {
    const token = getGuestToken();
    const headers: Record<string, string> = {};
    if (token) headers[GUEST_TOKEN_HEADER] = token;
    const res = await fetch(`${API_BASE_URL}/cart`, { headers, signal: controller.signal });
    if (!res.ok) {
      let code = "http_error";
      let message = `Request failed: ${res.status}`;
      try {
        const body = (await res.json()) as { error?: { code?: string; message?: string } };
        if (body?.error?.code) code = body.error.code;
        if (body?.error?.message) message = body.error.message;
      } catch (err) {
        if (controller.signal.aborted) throw err; // timeout/abort stays a generic error
      }
      // A rejected token would wedge the session in a permanent 400 — drop it so the next
      // call re-establishes a fresh guest session.
      if (code === "invalid_guest_token") clearGuestToken();
      throw new ApiError(res.status, code, message);
    }
    const issued = res.headers.get(GUEST_TOKEN_HEADER);
    if (issued) setGuestToken(issued);
    return (await res.json()) as Cart;
  } finally {
    clearTimeout(timer);
  }
}

/** Format integer cents as a display price. The only place cents becomes a string (AD-6). */
export function formatPrice(cents: number): string {
  return `$${(cents / 100).toFixed(2)}`;
}
