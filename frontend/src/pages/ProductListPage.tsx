import { useEffect, useRef, useState, type FormEvent } from "react";
import { formatPrice, listProducts, type ProductSummary } from "../api/client";

// PLP (Story 1.3 + 1.4): paginated product grid with keyword search.
// Search resets pagination and fetches page 1 for the term; "Load more" carries the
// active term. Empty results show a message + clear-search. Facets/sort come in 1.5–1.6.
export default function ProductListPage() {
  const [items, setItems] = useState<ProductSummary[]>([]);
  const [cursor, setCursor] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [initialized, setInitialized] = useState(false);
  const [query, setQuery] = useState(""); // text-box value
  const [activeSearch, setActiveSearch] = useState(""); // term applied to results
  const requestId = useRef(0); // latest-wins guard against out-of-order responses

  async function fetchPage(opts: { cursor?: string; search: string }) {
    const id = ++requestId.current;
    setLoading(true);
    setError(null);
    try {
      const page = await listProducts({
        limit: 24,
        cursor: opts.cursor,
        search: opts.search || undefined,
      });
      if (id !== requestId.current) return; // a newer request superseded this one — drop it
      setItems((prev) => (opts.cursor ? [...prev, ...page.items] : page.items));
      // Pagination is driven by the cursor, not item count: the backend may return an
      // empty page WITH a cursor while loop-to-fill digs for sparse matches.
      setCursor(page.nextCursor);
    } catch {
      if (id !== requestId.current) return;
      setError("Could not load products.");
    } finally {
      if (id === requestId.current) {
        setLoading(false);
        setInitialized(true);
      }
    }
  }

  useEffect(() => {
    void fetchPage({ search: "" });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  function onSubmit(e: FormEvent) {
    e.preventDefault();
    const term = query.trim();
    setActiveSearch(term);
    setItems([]);
    setCursor(null);
    void fetchPage({ search: term });
  }

  function onClear() {
    setQuery("");
    setActiveSearch("");
    setItems([]);
    setCursor(null);
    void fetchPage({ search: "" });
  }

  const isEmpty = initialized && !error && items.length === 0;

  return (
    <main style={{ fontFamily: "system-ui, sans-serif", padding: "1.5rem", maxWidth: 1100, margin: "0 auto" }}>
      <h1>Products</h1>

      <form onSubmit={onSubmit} style={{ display: "flex", gap: "0.5rem", margin: "0.5rem 0 1.25rem" }}>
        <input
          type="search"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Search products…"
          aria-label="Search products"
          style={{ flex: 1, padding: "0.5rem 0.75rem", maxWidth: 360 }}
        />
        <button type="submit" disabled={loading} style={{ padding: "0.5rem 1rem" }}>
          Search
        </button>
        {activeSearch && (
          <button type="button" onClick={onClear} disabled={loading} style={{ padding: "0.5rem 1rem" }}>
            Clear
          </button>
        )}
      </form>

      {activeSearch && !isEmpty && (
        <p style={{ color: "#6b7280" }}>Results for “{activeSearch}”</p>
      )}

      {error && <p style={{ color: "#b91c1c" }}>{error}</p>}

      {isEmpty && (
        <div>
          <p>{activeSearch ? `No products match “${activeSearch}”.` : "No products found."}</p>
          {activeSearch && (
            <button type="button" onClick={onClear} style={{ padding: "0.5rem 1rem" }}>
              Clear search
            </button>
          )}
        </div>
      )}

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
          <button
            onClick={() => cursor && void fetchPage({ cursor, search: activeSearch })}
            disabled={loading}
            style={{ padding: "0.5rem 1.25rem" }}
          >
            {loading ? "Loading…" : "Load more"}
          </button>
        </div>
      )}
    </main>
  );
}
