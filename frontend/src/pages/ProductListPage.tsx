import { useEffect, useState } from "react";
import { formatPrice, listProducts, type ProductSummary } from "../api/client";

// PLP (Story 1.3): paginated product grid. Fetches page 1 on mount; "Load more"
// appends the next page via the opaque cursor. Search/facets/sort come in 1.4–1.6.
export default function ProductListPage() {
  const [items, setItems] = useState<ProductSummary[]>([]);
  const [cursor, setCursor] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [initialized, setInitialized] = useState(false);

  async function loadPage(next?: string) {
    setLoading(true);
    setError(null);
    try {
      const page = await listProducts({ limit: 24, cursor: next });
      setItems((prev) => (next ? [...prev, ...page.items] : page.items));
      // Guard the exact-page-size boundary: DynamoDB can hand back a cursor for a page
      // that turns out empty. If nothing came back, treat this as the end.
      setCursor(page.items.length > 0 ? page.nextCursor : null);
    } catch {
      setError("Could not load products.");
    } finally {
      setLoading(false);
      setInitialized(true);
    }
  }

  useEffect(() => {
    void loadPage();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <main style={{ fontFamily: "system-ui, sans-serif", padding: "1.5rem", maxWidth: 1100, margin: "0 auto" }}>
      <h1>Products</h1>

      {error && <p style={{ color: "#b91c1c" }}>{error}</p>}
      {initialized && !error && items.length === 0 && <p>No products found.</p>}

      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fill, minmax(200px, 1fr))",
          gap: "1rem",
        }}
      >
        {items.map((p) => (
          <a
            key={p.productId}
            href={`/products/${encodeURIComponent(p.productId)}`}
            style={{
              border: "1px solid #e5e7eb",
              borderRadius: 8,
              padding: "0.75rem",
              textDecoration: "none",
              color: "inherit",
              display: "block",
            }}
          >
            <img
              src={p.imageUrl}
              alt={p.name}
              style={{ width: "100%", aspectRatio: "1 / 1", objectFit: "cover", borderRadius: 6 }}
            />
            <div style={{ marginTop: "0.5rem", fontWeight: 600 }}>{p.name}</div>
            <div style={{ color: "#374151" }}>{formatPrice(p.price)}</div>
            {!p.available && <div style={{ color: "#9ca3af", fontSize: "0.85rem" }}>Out of stock</div>}
          </a>
        ))}
      </div>

      {cursor && (
        <div style={{ textAlign: "center", marginTop: "1.5rem" }}>
          <button onClick={() => void loadPage(cursor)} disabled={loading} style={{ padding: "0.5rem 1.25rem" }}>
            {loading ? "Loading…" : "Load more"}
          </button>
        </div>
      )}
    </main>
  );
}
