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
