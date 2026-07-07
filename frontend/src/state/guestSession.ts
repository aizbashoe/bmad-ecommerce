// Anonymous guest session token (AD-2). The opaque `guestId` the API issues on the first
// cart interaction is stored here and sent as `X-Guest-Token` on cart/order requests, so the
// cart persists across reloads with no login. localStorage is guarded so an unavailable store
// (private mode, storage disabled) degrades to no-persistence instead of throwing.

const KEY = "bmad_guest_token";

export function getGuestToken(): string | null {
  try {
    return localStorage.getItem(KEY);
  } catch {
    return null;
  }
}

export function setGuestToken(token: string): void {
  try {
    localStorage.setItem(KEY, token);
  } catch {
    // storage unavailable — the token just won't persist across reloads this session
  }
}

/** Drop a stored token the server rejected, so the next request re-establishes a fresh session. */
export function clearGuestToken(): void {
  try {
    localStorage.removeItem(KEY);
  } catch {
    // storage unavailable — nothing to clear
  }
}
