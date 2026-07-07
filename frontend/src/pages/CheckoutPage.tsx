import {
  useEffect,
  useRef,
  useState,
  type Dispatch,
  type FormEvent,
  type ReactNode,
  type SetStateAction,
} from "react";
import { Link, useNavigate } from "react-router-dom";
import { ApiError, formatPrice, getCart, placeOrder, type Cart } from "../api/client";
import { useCart } from "../state/cart";
import { tokens } from "../theme/tokens";

// Checkout (Epic 4): shipping-details form + inline validation (4.1), simulated-payment notice
// (4.2), and Place order (4.3) — on a valid submit it POSTs /checkout, which snapshots the
// immutable Order and clears the cart atomically (AD-7), then routes to the summary (4.4).

type Field = "fullName" | "address1" | "address2" | "city" | "region" | "postalCode" | "country" | "email";

const REQUIRED: Field[] = ["fullName", "address1", "city", "region", "postalCode", "country", "email"];
const LABELS: Record<Field, string> = {
  fullName: "Full name",
  address1: "Address line 1",
  address2: "Address line 2 (optional)",
  city: "City",
  region: "Region / oblast",
  postalCode: "Postal code",
  country: "Country",
  email: "Email",
};
const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
const COUNTRIES = ["Ukraine", "Poland", "Germany", "United States"];

type FormState = Record<Field, string>;
const EMPTY: FormState = {
  fullName: "", address1: "", address2: "", city: "", region: "", postalCode: "", country: "", email: "",
};

function fieldError(field: Field, value: string): string | null {
  const v = value.trim();
  if (REQUIRED.includes(field) && !v) return `${LABELS[field].replace(" (optional)", "")} is required.`;
  if (field === "email" && v && !EMAIL_RE.test(v)) return "Enter a valid email.";
  return null;
}

export default function CheckoutPage() {
  const navigate = useNavigate();
  const { refresh } = useCart();
  const [cart, setCart] = useState<Cart | null>(null);
  const [loadError, setLoadError] = useState(false);
  const [form, setForm] = useState<FormState>(EMPTY);
  const [touched, setTouched] = useState<Partial<Record<Field, boolean>>>({});
  const [submitted, setSubmitted] = useState(false);
  const [placing, setPlacing] = useState(false);
  const [placeError, setPlaceError] = useState<string | null>(null);
  const requestId = useRef(0);

  useEffect(() => {
    const id = ++requestId.current;
    getCart()
      .then((c) => {
        if (id !== requestId.current) return;
        if (!c || !Array.isArray(c.items)) setLoadError(true); // guard a malformed cart shape
        else setCart(c);
      })
      .catch(() => id === requestId.current && setLoadError(true));
  }, []);

  const errors: Partial<Record<Field, string>> = {};
  for (const f of Object.keys(LABELS) as Field[]) {
    const e = fieldError(f, form[f]);
    if (e) errors[f] = e;
  }
  const isValid = Object.keys(errors).length === 0;

  function set(field: Field, value: string) {
    setForm((prev) => ({ ...prev, [field]: value }));
  }

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setSubmitted(true); // reveal any field errors
    if (!isValid || placing) return;
    setPlacing(true);
    setPlaceError(null);
    try {
      const order = await placeOrder(form); // form keys match ShippingDetails
      // Order committed + cart cleared (atomic). Navigate first, then refresh the header count
      // (fire-and-forget) so a refresh hiccup can never mask a successful order.
      navigate(`/order/${encodeURIComponent(order.orderId)}`);
      void refresh();
    } catch (err) {
      if (err instanceof ApiError && err.code === "empty_cart") {
        navigate("/cart"); // cart emptied elsewhere — retrying can't succeed
        return;
      }
      setPlaceError("Could not place your order. Please try again.");
      setPlacing(false);
    }
  }

  const wrap = { fontFamily: tokens.font, color: tokens.color.ink, background: tokens.color.bg, minHeight: "70vh" } as const;
  const inner = { maxWidth: 1120, margin: "0 auto", padding: "20px" } as const;

  if (loadError) {
    return (
      <main style={wrap}><div style={inner}><p style={{ color: tokens.color.error }}>Could not load checkout.</p></div></main>
    );
  }
  if (!cart) {
    return <main style={wrap}><div style={inner}><p style={{ color: tokens.color.muted }}>Loading…</p></div></main>;
  }
  if (cart.items.length === 0) {
    return (
      <main style={wrap}>
        <div style={inner}>
          <h1 style={{ fontSize: 26, margin: "6px 0 16px" }}>Checkout</h1>
          <p>Your cart is empty.</p>
          <Link to="/" style={{ color: tokens.color.greenDark, fontWeight: 600, textDecoration: "none" }}>Browse products</Link>
        </div>
      </main>
    );
  }

  const showErr = (f: Field) => (touched[f] || submitted) && errors[f];

  return (
    <main style={wrap}>
      <div style={inner}>
        <h1 style={{ fontSize: 26, margin: "6px 0 20px" }}>Checkout</h1>
        <form onSubmit={onSubmit} style={{ display: "grid", gridTemplateColumns: "1fr 320px", gap: 24, alignItems: "start" }}>
          {/* Left column: shipping form + payment notice */}
          <div style={{ display: "grid", gap: 18 }}>
          <div style={{ background: tokens.color.surface, border: `1px solid ${tokens.color.line}`, borderRadius: tokens.radius.md, padding: 22 }}>
            <h2 style={{ fontSize: 17, margin: "0 0 14px" }}>Shipping details</h2>
            <Row>
              <FieldInput f="fullName" form={form} set={set} setTouched={setTouched} err={showErr("fullName") ? errors.fullName : undefined} />
              <FieldInput f="email" form={form} set={set} setTouched={setTouched} err={showErr("email") ? errors.email : undefined} />
            </Row>
            <FieldInput f="address1" form={form} set={set} setTouched={setTouched} err={showErr("address1") ? errors.address1 : undefined} />
            <FieldInput f="address2" form={form} set={set} setTouched={setTouched} err={undefined} />
            <Row>
              <FieldInput f="city" form={form} set={set} setTouched={setTouched} err={showErr("city") ? errors.city : undefined} />
              <FieldInput f="region" form={form} set={set} setTouched={setTouched} err={showErr("region") ? errors.region : undefined} />
            </Row>
            <Row>
              <FieldInput f="postalCode" form={form} set={set} setTouched={setTouched} err={showErr("postalCode") ? errors.postalCode : undefined} />
              <div>
                <label style={labelStyle}>{LABELS.country} *</label>
                <select
                  value={form.country}
                  onChange={(e) => set("country", e.target.value)}
                  onBlur={() => setTouched((t) => ({ ...t, country: true }))}
                  aria-label="Country"
                  style={{ ...inputStyle, borderColor: showErr("country") ? tokens.color.error : tokens.color.line }}
                >
                  <option value="">Select…</option>
                  {COUNTRIES.map((c) => <option key={c} value={c}>{c}</option>)}
                </select>
                {showErr("country") && <div style={errStyle}>{errors.country}</div>}
              </div>
            </Row>
          </div>

          {/* Payment — simulated, success-only, no card data (FR-13, NFR-4) */}
          <div style={{ background: tokens.color.surface, border: `1px solid ${tokens.color.line}`, borderRadius: tokens.radius.md, padding: 22 }}>
            <h2 style={{ fontSize: 17, margin: "0 0 12px" }}>Payment</h2>
            <div style={{ background: "#f0faf3", border: `1px solid ${tokens.color.green}`, borderRadius: tokens.radius.sm, padding: "14px 16px", fontSize: 14, color: "#374151" }}>
              Simulated payment — <b style={{ color: tokens.color.greenDark }}>always succeeds</b>. No real
              gateway is called and no card data is collected or stored. Placing the order completes payment.
            </div>
          </div>
          </div>

          {/* Right: sticky summary */}
          <aside style={{ background: tokens.color.surface, border: `1px solid ${tokens.color.line}`, borderRadius: tokens.radius.md, padding: 20, position: "sticky", top: 20 }}>
            <h2 style={{ margin: "0 0 14px", fontSize: 17 }}>Summary</h2>
            <SummaryRow label={`Subtotal (${cart.items.reduce((n, i) => n + i.quantity, 0)} items)`} value={formatPrice(cart.subtotal)} />
            <SummaryRow label="Shipping (flat)" value={formatPrice(cart.shipping)} />
            <div style={{ display: "flex", justifyContent: "space-between", fontWeight: 800, fontSize: 20, borderTop: `1px solid ${tokens.color.line}`, marginTop: 12, paddingTop: 12 }}>
              <span>To pay</span><span>{formatPrice(cart.orderTotal)}</span>
            </div>
            <button
              type="submit"
              disabled={placing}
              style={{
                width: "100%", height: 48, marginTop: 16, border: "none", borderRadius: tokens.radius.sm,
                fontSize: 16, fontWeight: 700, color: "#fff",
                background: placing ? "#cbd5e1" : tokens.color.green,
                cursor: placing ? "not-allowed" : "pointer",
              }}
            >
              {placing ? "Placing…" : "Place order"}
            </button>
            {placeError && <p style={{ color: tokens.color.error, fontSize: 13, marginTop: 10 }}>{placeError}</p>}
            <p style={{ color: tokens.color.muted, fontSize: 12, marginTop: 10 }}>
              Simulated, success-only payment (FR-13). Nothing is charged.
            </p>
          </aside>
        </form>
      </div>
    </main>
  );
}

const labelStyle = { display: "block", fontSize: 13, color: "#374151", marginBottom: 5 } as const;
const inputStyle = { width: "100%", border: `1px solid ${tokens.color.line}`, borderRadius: tokens.radius.sm, padding: "10px 12px", fontSize: 14 } as const;
const errStyle = { color: tokens.color.error, fontSize: 12, marginTop: 4 } as const;

function Row({ children }: { children: ReactNode }) {
  return <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 14 }}>{children}</div>;
}

function SummaryRow({ label, value }: { label: string; value: string }) {
  return (
    <div style={{ display: "flex", justifyContent: "space-between", fontSize: 14, margin: "8px 0", color: "#374151" }}>
      <span>{label}</span><span>{value}</span>
    </div>
  );
}

function FieldInput({
  f, form, set, setTouched, err,
}: {
  f: Field;
  form: FormState;
  set: (field: Field, value: string) => void;
  setTouched: Dispatch<SetStateAction<Partial<Record<Field, boolean>>>>;
  err: string | undefined;
}) {
  const required = REQUIRED.includes(f);
  return (
    <div style={{ marginBottom: 14 }}>
      <label style={labelStyle}>{LABELS[f]}{required ? " *" : ""}</label>
      <input
        value={form[f]}
        onChange={(e) => set(f, e.target.value)}
        onBlur={() => setTouched((t) => ({ ...t, [f]: true }))}
        type={f === "email" ? "email" : "text"}
        aria-label={LABELS[f]}
        aria-invalid={err ? true : undefined}
        style={{ ...inputStyle, borderColor: err ? tokens.color.error : tokens.color.line }}
      />
      {err && <div style={errStyle}>{err}</div>}
    </div>
  );
}
