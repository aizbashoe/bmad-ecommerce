import { useEffect, useRef, useState, type FormEvent } from "react";
import {
  formatPrice,
  listCategories,
  listProducts,
  type ProductSummary,
} from "../api/client";

// PLP (Stories 1.3–1.5): paginated product grid with keyword search + category facet.
// Search/facet changes reset pagination and refetch page 1; "Load more" carries the active
// search term and selected categories. Sort controls come in 1.6.
export default function ProductListPage() {
  const [items, setItems] = useState<ProductSummary[]>([]);
  const [cursor, setCursor] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [initialized, setInitialized] = useState(false);
  const [query, setQuery] = useState(""); // text-box value
  const [activeSearch, setActiveSearch] = useState(""); // term applied to results
  const [allCategories, setAllCategories] = useState<string[]>([]); // facet options
  const [selected, setSelected] = useState<string[]>([]); // active category filters
  const requestId = useRef(0); // latest-wins guard against out-of-order responses

  async function fetchPage(opts: { cursor?: string; search: string; categories: string[] }) {
    const id = ++requestId.current;
    setLoading(true);
    setError(null);
    try {
      const page = await listProducts({
        limit: 24,
        cursor: opts.cursor,
        search: opts.search || undefined,
        categories: opts.categories.length ? opts.categories : undefined,
      });
      if (id !== requestId.current) return; // superseded by a newer request — drop it
      setItems((prev) => (opts.cursor ? [...prev, ...page.items] : page.items));
      // Cursor-driven paging (loop-to-fill may return an empty page WITH a cursor).
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
    listCategories()
      .then((c) => setAllCategories(c.categories))
      .catch(() => setAllCategories([]));
    void fetchPage({ search: "", categories: [] });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Reset pagination and refetch page 1 for a given search + category set.
  function applyFilters(search: string, categories: string[]) {
    setItems([]);
    setCursor(null);
    void fetchPage({ search, categories });
  }

  function onSubmit(e: FormEvent) {
    e.preventDefault();
    const term = query.trim();
    setActiveSearch(term);
    applyFilters(term, selected);
  }

  function toggleCategory(cat: string) {
    const next = selected.includes(cat)
      ? selected.filter((c) => c !== cat)
      : [...selected, cat];
    setSelected(next);
    applyFilters(activeSearch, next);
  }

  function clearAll() {
    setQuery("");
    setActiveSearch("");
    setSelected([]);
    applyFilters("", []);
  }

  const hasFilters = activeSearch !== "" || selected.length > 0;
  // Only "empty" once there are no more pages to fetch — loop-to-fill can return an
  // empty page WITH a cursor, in which case "Load more" (not the empty state) shows.
  const isEmpty = initialized && !error && items.length === 0 && !cursor;

  return (
    <main style={{ fontFamily: "system-ui, sans-serif", padding: "1.5rem", maxWidth: 1100, margin: "0 auto" }}>
      <h1>Products</h1>

      <form onSubmit={onSubmit} style={{ display: "flex", gap: "0.5rem", margin: "0.5rem 0 0.75rem" }}>
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
      </form>

      {/* Category facet */}
      {allCategories.length > 0 && (
        <div style={{ display: "flex", flexWrap: "wrap", gap: "0.75rem", margin: "0 0 0.75rem" }}>
          {allCategories.map((cat) => (
            <label key={cat} style={{ display: "inline-flex", gap: "0.35rem", alignItems: "center" }}>
              <input type="checkbox" checked={selected.includes(cat)} onChange={() => toggleCategory(cat)} />
              {cat}
            </label>
          ))}
        </div>
      )}

      {/* Active-filter chips */}
      {hasFilters && (
        <div style={{ display: "flex", flexWrap: "wrap", gap: "0.5rem", alignItems: "center", margin: "0 0 1rem" }}>
          {activeSearch && (
            <Chip label={`search: ${activeSearch}`} onRemove={() => { setQuery(""); setActiveSearch(""); applyFilters("", selected); }} />
          )}
          {selected.map((cat) => (
            <Chip key={cat} label={cat} onRemove={() => toggleCategory(cat)} />
          ))}
          <button type="button" onClick={clearAll} style={{ padding: "0.25rem 0.75rem" }}>
            Clear all
          </button>
        </div>
      )}

      {error && <p style={{ color: "#b91c1c" }}>{error}</p>}

      {isEmpty && (
        <div>
          <p>{hasFilters ? "No products match your filters." : "No products found."}</p>
          {hasFilters && (
            <button type="button" onClick={clearAll} style={{ padding: "0.5rem 1rem" }}>
              Clear all filters
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
            onClick={() => cursor && void fetchPage({ cursor, search: activeSearch, categories: selected })}
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

function Chip({ label, onRemove }: { label: string; onRemove: () => void }) {
  return (
    <span
      style={{
        display: "inline-flex",
        gap: "0.35rem",
        alignItems: "center",
        background: "#eef2ff",
        border: "1px solid #c7d2fe",
        borderRadius: 999,
        padding: "0.2rem 0.6rem",
        fontSize: "0.85rem",
      }}
    >
      {label}
      <button
        type="button"
        onClick={onRemove}
        aria-label={`Remove ${label}`}
        style={{ border: "none", background: "transparent", cursor: "pointer", fontWeight: 700 }}
      >
        ×
      </button>
    </span>
  );
}
