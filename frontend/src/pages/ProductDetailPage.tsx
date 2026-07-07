import { useEffect, useRef, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { addToCart, ApiError, formatPrice, getProduct, type ProductDetail } from "../api/client";
import { useCart } from "../state/cart";
import { tokens } from "../theme/tokens";

// PDP (Story 2.1): two-column layout (image gallery / action panel) + breadcrumb + About.
// Unknown id -> a distinct not-found state (from the 404 not_found envelope), NOT the generic
// error state. Add-to-cart is shown but disabled (wired in Epic 3).
type LoadState =
  | { kind: "loading" }
  | { kind: "ok"; product: ProductDetail }
  | { kind: "not-found" }
  | { kind: "error" };

export default function ProductDetailPage() {
  const { id } = useParams<{ id: string }>();
  const [state, setState] = useState<LoadState>({ kind: "loading" });
  const requestId = useRef(0); // latest-wins guard against out-of-order responses

  useEffect(() => {
    const rid = ++requestId.current;
    setState({ kind: "loading" });
    if (!id) {
      setState({ kind: "not-found" });
      return;
    }
    getProduct(id)
      .then((product) => {
        if (rid === requestId.current) setState({ kind: "ok", product });
      })
      .catch((err) => {
        if (rid !== requestId.current) return;
        // A 404 / not_found is the not-found state; anything else is a generic error.
        if (err instanceof ApiError && (err.status === 404 || err.code === "not_found")) {
          setState({ kind: "not-found" });
        } else {
          setState({ kind: "error" });
        }
      });
  }, [id]);

  return (
    <main style={{ fontFamily: tokens.font, color: tokens.color.ink, background: tokens.color.bg, minHeight: "60vh" }}>
      <div style={{ maxWidth: 1180, margin: "0 auto", padding: "18px 20px" }}>
        {state.kind === "loading" && <p style={{ color: tokens.color.muted }}>Loading…</p>}

        {state.kind === "not-found" && (
          <div style={{ padding: "2rem 0" }}>
            <h1 style={{ fontSize: 22, margin: "0 0 8px" }}>This product isn't available.</h1>
            <p style={{ color: tokens.color.muted, margin: "0 0 16px" }}>
              It may have been removed or the link is incorrect.
            </p>
            <Link to="/" style={{ color: tokens.color.greenDark, fontWeight: 600, textDecoration: "none" }}>
              ← Back to products
            </Link>
          </div>
        )}

        {state.kind === "error" && (
          <div style={{ padding: "2rem 0" }}>
            <p style={{ color: tokens.color.error }}>Could not load this product.</p>
            <Link to="/" style={{ color: tokens.color.greenDark, fontWeight: 600, textDecoration: "none" }}>
              ← Back to products
            </Link>
          </div>
        )}

        {state.kind === "ok" && <ProductView product={state.product} />}
      </div>
    </main>
  );
}

function ProductView({ product: p }: { product: ProductDetail }) {
  return (
    <>
      <nav style={{ color: tokens.color.muted, fontSize: 13, marginBottom: 16 }} aria-label="Breadcrumb">
        <Link to="/" style={{ color: tokens.color.muted, textDecoration: "none" }}>
          Home
        </Link>{" "}
        / <span>{p.category}</span> / {p.name}
      </nav>

      <div
        style={{
          display: "grid",
          gridTemplateColumns: "1.15fr 1fr",
          gap: 28,
          background: tokens.color.surface,
          border: `1px solid ${tokens.color.line}`,
          borderRadius: tokens.radius.md,
          padding: 22,
        }}
      >
        {/* Gallery — single image; the data model has one imageUrl (no multi-image data). */}
        <div style={{ position: "relative" }}>
          <img
            src={p.imageUrl}
            alt={p.name}
            style={{ width: "100%", aspectRatio: "1 / 1", objectFit: "cover", borderRadius: 10, background: "#eef0f3" }}
          />
          <span
            style={{
              position: "absolute",
              top: 12,
              left: 12,
              background: tokens.color.badge,
              color: "#fff",
              fontSize: 12,
              fontWeight: 700,
              textTransform: "uppercase",
              letterSpacing: "0.03em",
              padding: "4px 10px",
              borderRadius: tokens.radius.pill,
            }}
          >
            {p.category}
          </span>
        </div>

        {/* Action panel */}
        <AddToCartPanel product={p} />
      </div>

      <section
        style={{
          background: tokens.color.surface,
          border: `1px solid ${tokens.color.line}`,
          borderRadius: tokens.radius.md,
          padding: 22,
          marginTop: 20,
        }}
      >
        <h2 style={{ fontSize: 17, margin: "0 0 10px" }}>About this product</h2>
        <p style={{ color: "#374151", lineHeight: 1.65, margin: 0 }}>{p.description}</p>
      </section>
    </>
  );
}

// Action panel: quantity stepper + Add to cart (Story 3.2). Adds to the guest cart and refreshes
// the header count. Disabled for out-of-stock products.
function AddToCartPanel({ product: p }: { product: ProductDetail }) {
  const { applyCart } = useCart();
  const [qty, setQty] = useState(1);
  const [busy, setBusy] = useState(false);
  const [added, setAdded] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const addedTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const disabled = !p.available || busy;

  useEffect(() => () => {
    if (addedTimer.current) clearTimeout(addedTimer.current); // clear on unmount
  }, []);

  async function onAdd() {
    setBusy(true);
    setError(null);
    try {
      const cart = await addToCart(p.productId, qty);
      applyCart(cart); // update header count from the response — no extra round-trip
      setAdded(true);
      if (addedTimer.current) clearTimeout(addedTimer.current);
      addedTimer.current = setTimeout(() => setAdded(false), 2000);
    } catch {
      setError("Could not add to cart.");
    } finally {
      setBusy(false);
    }
  }

  const stepBtn = { border: "none", background: "#f3f4f6", width: 38, height: 46, fontSize: 18, cursor: "pointer" } as const;

  return (
    <div>
      <h1 style={{ fontSize: 22, margin: "0 0 6px", lineHeight: 1.25 }}>{p.name}</h1>
      <div style={{ color: tokens.color.muted, fontSize: 13, marginBottom: 18 }}>Category: {p.category}</div>
      <div style={{ fontWeight: 700, marginBottom: 6, color: p.available ? tokens.color.stockIn : tokens.color.stockOut }}>
        {p.available ? "In stock" : "Out of stock"}
      </div>
      <div style={{ color: tokens.color.price, fontWeight: 800, fontSize: 30, marginBottom: 18 }}>
        {formatPrice(p.price)}
      </div>
      <div style={{ display: "flex", gap: 12, alignItems: "center", marginBottom: 10 }}>
        <div style={{ display: "inline-flex", border: `1px solid ${tokens.color.line}`, borderRadius: tokens.radius.sm, overflow: "hidden" }}>
          <button type="button" onClick={() => setQty((q) => Math.max(1, q - 1))} disabled={disabled} aria-label="Decrease quantity" style={stepBtn}>
            −
          </button>
          <input value={qty} readOnly aria-label="Quantity" style={{ width: 46, textAlign: "center", border: "none", fontSize: 16 }} />
          <button type="button" onClick={() => setQty((q) => Math.min(999, q + 1))} disabled={disabled || qty >= 999} aria-label="Increase quantity" style={stepBtn}>
            +
          </button>
        </div>
        <button
          type="button"
          onClick={onAdd}
          disabled={disabled}
          style={{
            flex: 1,
            background: disabled ? "#cbd5e1" : tokens.color.green,
            color: "#fff",
            border: "none",
            borderRadius: tokens.radius.sm,
            height: 48,
            fontSize: 16,
            fontWeight: 700,
            cursor: disabled ? "not-allowed" : "pointer",
          }}
        >
          {busy ? "Adding…" : "Add to cart"}
        </button>
      </div>
      {added && <div style={{ color: tokens.color.stockIn, fontSize: 13, fontWeight: 600 }}>Added to cart ✓</div>}
      {error && <div style={{ color: tokens.color.error, fontSize: 13 }}>{error}</div>}
      {!p.available && <div style={{ color: tokens.color.muted, fontSize: 12 }}>This item is out of stock.</div>}
    </div>
  );
}
