import { useEffect, useRef, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { ApiError, formatPrice, getOrder, type Order } from "../api/client";
import { tokens } from "../theme/tokens";

// Order Summary (Story 4.4): the post-checkout confirmation, fetched by id (scoped to the guest
// token). Shows reference, line items, totals, and shipping. Not a history page (FR-15).
type LoadState =
  | { kind: "loading" }
  | { kind: "ok"; order: Order }
  | { kind: "not-found" }
  | { kind: "error" };

export default function OrderSummaryPage() {
  const { orderId } = useParams<{ orderId: string }>();
  const [state, setState] = useState<LoadState>({ kind: "loading" });
  const requestId = useRef(0);

  useEffect(() => {
    const id = ++requestId.current;
    setState({ kind: "loading" });
    if (!orderId) {
      setState({ kind: "not-found" });
      return;
    }
    getOrder(orderId)
      .then((order) => {
        if (id !== requestId.current) return;
        if (!order || !Array.isArray(order.items)) setState({ kind: "error" }); // guard shape
        else setState({ kind: "ok", order });
      })
      .catch((err) => {
        if (id !== requestId.current) return;
        if (err instanceof ApiError && (err.status === 404 || err.code === "not_found")) {
          setState({ kind: "not-found" });
        } else {
          setState({ kind: "error" });
        }
      });
  }, [orderId]);

  const wrap = { fontFamily: tokens.font, color: tokens.color.ink, background: tokens.color.bg, minHeight: "70vh" } as const;
  const inner = { maxWidth: 760, margin: "0 auto", padding: "24px 20px" } as const;
  const card = { background: tokens.color.surface, border: `1px solid ${tokens.color.line}`, borderRadius: tokens.radius.md, padding: 22, marginBottom: 18 } as const;

  if (state.kind === "loading") {
    return <main style={wrap}><div style={inner}><p style={{ color: tokens.color.muted }}>Loading…</p></div></main>;
  }
  if (state.kind === "not-found") {
    return (
      <main style={wrap}><div style={inner}>
        <h1 style={{ fontSize: 22, margin: "0 0 8px" }}>Order not found.</h1>
        <Link to="/" style={{ color: tokens.color.greenDark, fontWeight: 600, textDecoration: "none" }}>← Continue shopping</Link>
      </div></main>
    );
  }
  if (state.kind === "error") {
    return (
      <main style={wrap}><div style={inner}>
        <p style={{ color: tokens.color.error }}>Could not load your order.</p>
        <Link to="/" style={{ color: tokens.color.greenDark, fontWeight: 600, textDecoration: "none" }}>← Continue shopping</Link>
      </div></main>
    );
  }

  const o = state.order;
  const sd = o.shippingDetails;
  return (
    <main style={wrap}>
      <div style={inner}>
        <div style={{ display: "flex", alignItems: "center", gap: 12, background: "#f0faf3", border: `1px solid ${tokens.color.green}`, borderRadius: tokens.radius.md, padding: "18px 20px", marginBottom: 20 }}>
          <div style={{ width: 36, height: 36, borderRadius: 999, background: tokens.color.green, color: "#fff", display: "grid", placeItems: "center", fontSize: 20 }}>✓</div>
          <div>
            <h1 style={{ fontSize: 20, margin: 0 }}>Thank you — your order is placed</h1>
            <div style={{ color: tokens.color.muted, fontSize: 14, marginTop: 2 }}>
              Reference <b style={{ color: tokens.color.ink }}>{o.reference}</b> · Placed {new Date(o.createdAt).toLocaleString()}
            </div>
          </div>
        </div>

        <div style={card}>
          <h2 style={{ fontSize: 16, margin: "0 0 14px" }}>Items</h2>
          {o.items.map((it) => (
            <div key={it.productId} style={{ display: "grid", gridTemplateColumns: "56px 1fr auto", gap: 12, alignItems: "center", padding: "10px 0", borderBottom: `1px solid ${tokens.color.line}` }}>
              <img src={it.imageUrl} alt={it.name} style={{ width: 56, height: 56, objectFit: "cover", borderRadius: 8, background: "#eef0f3" }} />
              <div>{it.name}<br /><span style={{ color: tokens.color.muted }}>{formatPrice(it.unitPrice)} × {it.quantity}</span></div>
              <div style={{ fontWeight: 700 }}>{formatPrice(it.lineTotal)}</div>
            </div>
          ))}
          <div style={{ display: "flex", justifyContent: "space-between", fontSize: 14, margin: "12px 0 0", color: "#374151" }}><span>Subtotal</span><span>{formatPrice(o.subtotal)}</span></div>
          <div style={{ display: "flex", justifyContent: "space-between", fontSize: 14, margin: "8px 0", color: "#374151" }}><span>Shipping (flat)</span><span>{formatPrice(o.shipping)}</span></div>
          <div style={{ display: "flex", justifyContent: "space-between", fontWeight: 800, fontSize: 18, borderTop: `1px solid ${tokens.color.line}`, marginTop: 8, paddingTop: 12 }}><span>Order total</span><span>{formatPrice(o.orderTotal)}</span></div>
        </div>

        <div style={card}>
          <h2 style={{ fontSize: 16, margin: "0 0 10px" }}>Shipping to</h2>
          <p style={{ margin: "2px 0", color: "#374151", fontSize: 14 }}>{sd.fullName} · {sd.email}</p>
          <p style={{ margin: "2px 0", color: "#374151", fontSize: 14 }}>
            {[sd.address1, sd.address2, sd.city, sd.region, sd.postalCode, sd.country].filter(Boolean).join(", ")}
          </p>
        </div>

        <Link to="/" style={{ color: tokens.color.greenDark, fontWeight: 600, textDecoration: "none" }}>← Continue shopping</Link>
      </div>
    </main>
  );
}
