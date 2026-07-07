import { useEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";
import {
  formatPrice,
  getCart,
  removeCartItem,
  updateCartItem,
  type Cart,
} from "../api/client";
import { useCart } from "../state/cart";
import { tokens } from "../theme/tokens";

// Cart page (Stories 3.3-3.5): line-item rows with a quantity stepper + remove, a sticky order
// summary (subtotal / flat shipping / order total), and an empty state. Every mutation returns the
// recomputed cart from the API; we also refresh the shared header count.
export default function CartPage() {
  const { applyCart } = useCart();
  const [cart, setCart] = useState<Cart | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const requestId = useRef(0);

  async function load() {
    const id = ++requestId.current;
    setError(null);
    try {
      const c = await getCart();
      if (id === requestId.current) setCart(c);
    } catch {
      if (id === requestId.current) setError("Could not load your cart.");
    }
  }

  useEffect(() => {
    void load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function mutate(fn: () => Promise<Cart>) {
    const id = ++requestId.current; // supersede any in-flight load/mutate
    setBusy(true);
    setError(null);
    try {
      const c = await fn();
      if (id !== requestId.current) return; // superseded by a newer action
      setCart(c);
      applyCart(c); // header count from the response — no extra round-trip
      setBusy(false);
    } catch {
      if (id !== requestId.current) return;
      setError("Could not update your cart.");
      setBusy(false); // release the UI BEFORE load() bumps requestId (else finally would skip it)
      void load(); // re-sync with the server (e.g. a line removed in another tab)
    }
  }

  const wrap = { fontFamily: tokens.font, color: tokens.color.ink, background: tokens.color.bg, minHeight: "70vh" } as const;
  const inner = { maxWidth: 1120, margin: "0 auto", padding: "20px" } as const;

  if (!cart && !error) {
    return (
      <main style={wrap}>
        <div style={inner}>
          <p style={{ color: tokens.color.muted }}>Loading…</p>
        </div>
      </main>
    );
  }

  const isEmpty = cart !== null && cart.items.length === 0;

  return (
    <main style={wrap}>
      <div style={inner}>
        <h1 style={{ fontSize: 26, margin: "6px 0 20px" }}>Your cart</h1>
        {error && <p style={{ color: tokens.color.error }}>{error}</p>}

        {isEmpty && (
          <div>
            <p>Your cart is empty.</p>
            <Link to="/" style={{ color: tokens.color.greenDark, fontWeight: 600, textDecoration: "none" }}>
              Browse products
            </Link>
          </div>
        )}

        {cart && cart.items.length > 0 && (
          <div style={{ display: "grid", gridTemplateColumns: "1fr 320px", gap: 24, alignItems: "start" }}>
            {/* Line items */}
            <div style={{ background: tokens.color.surface, border: `1px solid ${tokens.color.line}`, borderRadius: tokens.radius.md, padding: "8px 18px" }}>
              {cart.items.map((it) => (
                <div
                  key={it.productId}
                  style={{
                    display: "grid",
                    gridTemplateColumns: "72px 1fr auto auto auto",
                    gap: 16,
                    alignItems: "center",
                    padding: "18px 0",
                    borderBottom: `1px solid ${tokens.color.line}`,
                  }}
                >
                  <img src={it.imageUrl} alt={it.name} style={{ width: 72, height: 72, objectFit: "cover", borderRadius: 8, background: "#eef0f3" }} />
                  <div>
                    <Link to={`/products/${encodeURIComponent(it.productId)}`} style={{ fontWeight: 600, fontSize: 15, color: "inherit", textDecoration: "none" }}>
                      {it.name}
                    </Link>
                    <div style={{ color: tokens.color.muted, fontSize: 13, marginTop: 4 }}>{formatPrice(it.unitPrice)} each</div>
                  </div>
                  <div style={{ display: "inline-flex", border: `1px solid ${tokens.color.line}`, borderRadius: tokens.radius.sm, overflow: "hidden" }}>
                    <button
                      type="button"
                      onClick={() => void mutate(() => updateCartItem(it.productId, it.quantity - 1))}
                      disabled={busy}
                      aria-label="Decrease quantity"
                      style={{ border: "none", background: "#f3f4f6", width: 34, height: 40, fontSize: 18, cursor: "pointer" }}
                    >
                      −
                    </button>
                    <input value={it.quantity} readOnly aria-label={`Quantity of ${it.name}`} style={{ width: 42, textAlign: "center", border: "none", fontSize: 15 }} />
                    <button
                      type="button"
                      onClick={() => void mutate(() => updateCartItem(it.productId, it.quantity + 1))}
                      disabled={busy || it.quantity >= 999}
                      aria-label="Increase quantity"
                      style={{ border: "none", background: "#f3f4f6", width: 34, height: 40, fontSize: 18, cursor: "pointer" }}
                    >
                      +
                    </button>
                  </div>
                  <div style={{ fontWeight: 800, color: tokens.color.price, minWidth: 96, textAlign: "right" }}>{formatPrice(it.lineTotal)}</div>
                  <button
                    type="button"
                    onClick={() => void mutate(() => removeCartItem(it.productId))}
                    disabled={busy}
                    aria-label={`Remove ${it.name}`}
                    style={{ border: "none", background: "none", color: tokens.color.muted, cursor: "pointer", fontSize: 18 }}
                  >
                    🗑
                  </button>
                </div>
              ))}
            </div>

            {/* Order summary */}
            <aside style={{ background: tokens.color.surface, border: `1px solid ${tokens.color.line}`, borderRadius: tokens.radius.md, padding: 20, position: "sticky", top: 20 }}>
              <h2 style={{ margin: "0 0 14px", fontSize: 17 }}>Order summary</h2>
              <div style={{ display: "flex", justifyContent: "space-between", fontSize: 14, margin: "8px 0", color: "#374151" }}>
                <span>Subtotal</span>
                <span>{formatPrice(cart.subtotal)}</span>
              </div>
              <div style={{ display: "flex", justifyContent: "space-between", fontSize: 14, margin: "8px 0", color: "#374151" }}>
                <span>Shipping (flat)</span>
                <span>{formatPrice(cart.shipping)}</span>
              </div>
              <div style={{ display: "flex", justifyContent: "space-between", fontWeight: 800, fontSize: 20, borderTop: `1px solid ${tokens.color.line}`, marginTop: 12, paddingTop: 12 }}>
                <span>Order total</span>
                <span>{formatPrice(cart.orderTotal)}</span>
              </div>
              <Link
                to="/checkout"
                style={{ display: "block", textAlign: "center", width: "100%", boxSizing: "border-box", background: tokens.color.green, color: "#fff", border: "none", borderRadius: tokens.radius.sm, height: 48, lineHeight: "48px", fontSize: 16, fontWeight: 700, textDecoration: "none", marginTop: 16 }}
              >
                Checkout
              </Link>
            </aside>
          </div>
        )}
      </div>
    </main>
  );
}
