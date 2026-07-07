import { useEffect, useRef, useState, type FormEvent } from "react";
import { Link } from "react-router-dom";
import {
  ApiError,
  formatPrice,
  listCategories,
  listProducts,
  type ProductSummary,
  type SortOption,
} from "../api/client";
import { tokens } from "../theme/tokens";

// PLP (Stories 1.3–1.6; restyled to the UX design in Story 5.1): paginated product grid with
// keyword search, a left-sidebar category facet, and price sort. Search/facet/sort changes reset
// pagination and refetch page 1; "Load more" carries the active search term, categories, and sort.
// Styling comes from the shared DESIGN.md tokens; the shared StoreHeader renders above this page.
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
  const [sort, setSort] = useState<SortOption>("price_asc"); // sort order
  const requestId = useRef(0); // latest-wins guard against out-of-order responses

  async function fetchPage(opts: {
    cursor?: string;
    search: string;
    categories: string[];
    sort: SortOption;
  }) {
    const id = ++requestId.current;
    setLoading(true);
    setError(null);
    try {
      const page = await listProducts({
        limit: 24,
        cursor: opts.cursor,
        search: opts.search || undefined,
        categories: opts.categories.length ? opts.categories : undefined,
        sort: opts.sort,
      });
      if (id !== requestId.current) return; // superseded by a newer request — drop it
      setItems((prev) => (opts.cursor ? [...prev, ...page.items] : page.items));
      // Cursor-driven paging (loop-to-fill may return an empty page WITH a cursor).
      setCursor(page.nextCursor);
    } catch (err) {
      if (id !== requestId.current) return;
      // A stale "Load more" cursor -> 400 invalid_cursor. Drop it and reload page 1 with the
      // same filters (once — the retry sends no cursor, so it can't re-trigger this branch).
      if (err instanceof ApiError && err.code === "invalid_cursor" && opts.cursor) {
        // Keep existing items (the page-1 retry replaces them on success; a failed retry
        // then leaves the grid intact rather than blank). Just drop the stale cursor.
        setCursor(null);
        void fetchPage({ search: opts.search, categories: opts.categories, sort: opts.sort });
        return;
      }
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
    void fetchPage({ search: "", categories: [], sort: "price_asc" });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Reset pagination and refetch page 1 for a given search + category set + sort.
  function applyFilters(search: string, categories: string[], sortOpt: SortOption) {
    setItems([]);
    setCursor(null);
    void fetchPage({ search, categories, sort: sortOpt });
  }

  function onSubmit(e: FormEvent) {
    e.preventDefault();
    const term = query.trim();
    setActiveSearch(term);
    applyFilters(term, selected, sort);
  }

  function toggleCategory(cat: string) {
    const next = selected.includes(cat)
      ? selected.filter((c) => c !== cat)
      : [...selected, cat];
    setSelected(next);
    applyFilters(activeSearch, next, sort);
  }

  function onSortChange(next: SortOption) {
    setSort(next);
    applyFilters(activeSearch, selected, next);
  }

  function clearAll() {
    setQuery("");
    setActiveSearch("");
    setSelected([]);
    applyFilters("", [], sort); // sort is a persistent control, not a filter — keep it
  }

  const hasFilters = activeSearch !== "" || selected.length > 0;
  // Only "empty" once there are no more pages to fetch — loop-to-fill can return an
  // empty page WITH a cursor, in which case "Load more" (not the empty state) shows.
  const isEmpty = initialized && !error && items.length === 0 && !cursor;

  return (
    <main
      style={{
        fontFamily: tokens.font,
        color: tokens.color.ink,
        background: tokens.color.bg,
        minHeight: "70vh",
      }}
    >
      <div style={{ maxWidth: 1240, margin: "0 auto", padding: "20px" }}>
        <h1 style={{ fontSize: 24, margin: "4px 0 16px" }}>Products</h1>

        <form onSubmit={onSubmit} style={{ display: "flex", gap: 0, marginBottom: 20, maxWidth: 520 }}>
          <input
            type="search"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search products…"
            aria-label="Search products"
            style={{
              flex: 1,
              padding: "11px 14px",
              border: `1px solid ${tokens.color.line}`,
              borderRight: "none",
              borderRadius: `${tokens.radius.sm}px 0 0 ${tokens.radius.sm}px`,
              fontSize: 15,
            }}
          />
          <button
            type="submit"
            disabled={loading}
            style={{
              border: "none",
              background: tokens.color.green,
              color: "#fff",
              fontWeight: 700,
              padding: "0 22px",
              borderRadius: `0 ${tokens.radius.sm}px ${tokens.radius.sm}px 0`,
              cursor: "pointer",
            }}
          >
            Search
          </button>
        </form>

        <div style={{ display: "grid", gridTemplateColumns: "250px 1fr", gap: 24, alignItems: "start" }}>
          {/* Left facet sidebar */}
          <aside
            style={{
              background: tokens.color.surface,
              border: `1px solid ${tokens.color.line}`,
              borderRadius: tokens.radius.md,
              padding: 18,
            }}
          >
            <h3 style={{ margin: "0 0 12px", fontSize: 15 }}>Category</h3>
            {allCategories.length === 0 ? (
              <p style={{ color: tokens.color.muted, fontSize: 14, margin: 0 }}>No categories</p>
            ) : (
              allCategories.map((cat) => (
                <label
                  key={cat}
                  style={{
                    display: "flex",
                    alignItems: "center",
                    gap: 9,
                    padding: "6px 0",
                    fontSize: 14,
                    color: "#374151",
                    cursor: "pointer",
                  }}
                >
                  <input
                    type="checkbox"
                    checked={selected.includes(cat)}
                    onChange={() => toggleCategory(cat)}
                    style={{ width: 16, height: 16, accentColor: tokens.color.green }}
                  />
                  {cat}
                </label>
              ))
            )}
          </aside>

          {/* Results column */}
          <section>
            {/* Toolbar: result context + sort */}
            <div
              style={{
                display: "flex",
                alignItems: "center",
                justifyContent: "space-between",
                marginBottom: 16,
              }}
            >
              <span style={{ color: tokens.color.muted, fontSize: 14 }}>
                {loading
                  ? "Loading…"
                  : error
                    ? ""
                    : `Showing ${items.length} product${items.length === 1 ? "" : "s"}${cursor ? " (more available)" : ""}`}
              </span>
              <label style={{ display: "inline-flex", gap: 8, alignItems: "center", fontSize: 14 }}>
                Sort:
                <select
                  value={sort}
                  onChange={(e) => onSortChange(e.target.value as SortOption)}
                  aria-label="Sort products"
                  style={{ padding: "8px 10px", border: `1px solid ${tokens.color.line}`, borderRadius: tokens.radius.sm }}
                >
                  <option value="price_asc">Price: Low → High</option>
                  <option value="price_desc">Price: High → Low</option>
                </select>
              </label>
            </div>

            {/* Active-filter chips */}
            {hasFilters && (
              <div style={{ display: "flex", flexWrap: "wrap", gap: 8, alignItems: "center", marginBottom: 16 }}>
                {activeSearch && (
                  <Chip
                    label={`search: ${activeSearch}`}
                    onRemove={() => {
                      setQuery("");
                      setActiveSearch("");
                      applyFilters("", selected, sort);
                    }}
                  />
                )}
                {selected.map((cat) => (
                  <Chip key={cat} label={cat} onRemove={() => toggleCategory(cat)} />
                ))}
                <button
                  type="button"
                  onClick={clearAll}
                  style={{
                    padding: "4px 12px",
                    border: "none",
                    background: "none",
                    color: tokens.color.green,
                    fontWeight: 600,
                    cursor: "pointer",
                  }}
                >
                  Clear all
                </button>
              </div>
            )}

            {error && <p style={{ color: tokens.color.error }}>{error}</p>}

            {isEmpty && (
              <div>
                <p>{hasFilters ? "No products match your filters." : "No products found."}</p>
                {hasFilters && (
                  <button type="button" onClick={clearAll} style={{ padding: "8px 16px" }}>
                    Clear all filters
                  </button>
                )}
              </div>
            )}

            <div
              style={{
                display: "grid",
                gridTemplateColumns: "repeat(auto-fill, minmax(200px, 1fr))",
                gap: 16,
              }}
            >
              {items.map((p) => (
                <Link
                  key={p.productId}
                  to={`/products/${encodeURIComponent(p.productId)}`}
                  style={{
                    position: "relative",
                    background: tokens.color.surface,
                    border: `1px solid ${tokens.color.line}`,
                    borderRadius: tokens.radius.md,
                    padding: 12,
                    textDecoration: "none",
                    color: "inherit",
                    display: "block",
                  }}
                >
                  <div style={{ position: "relative" }}>
                    <img
                      src={p.imageUrl}
                      alt={p.name}
                      style={{ width: "100%", aspectRatio: "1 / 1", objectFit: "cover", borderRadius: 8, background: "#eef0f3" }}
                    />
                    {/* Category stamp — top-left over the image */}
                    <span
                      style={{
                        position: "absolute",
                        top: 8,
                        left: 8,
                        background: tokens.color.badge,
                        color: "#fff",
                        fontSize: 11,
                        fontWeight: 700,
                        textTransform: "uppercase",
                        letterSpacing: "0.03em",
                        padding: "3px 8px",
                        borderRadius: tokens.radius.pill,
                        maxWidth: "calc(100% - 16px)",
                        whiteSpace: "nowrap",
                        overflow: "hidden",
                        textOverflow: "ellipsis",
                      }}
                    >
                      {p.category}
                    </span>
                  </div>
                  <div style={{ marginTop: 10, fontWeight: 600, fontSize: 14, lineHeight: 1.35, minHeight: 38 }}>
                    {p.name}
                  </div>
                  <div style={{ color: tokens.color.price, fontWeight: 800, fontSize: 18 }}>{formatPrice(p.price)}</div>
                  <div
                    style={{
                      marginTop: 4,
                      fontSize: 12.5,
                      fontWeight: 600,
                      color: p.available ? tokens.color.stockIn : tokens.color.stockOut,
                    }}
                  >
                    {p.available ? "In stock" : "Out of stock"}
                  </div>
                </Link>
              ))}
            </div>

            {cursor && (
              <div style={{ textAlign: "center", marginTop: 24 }}>
                <button
                  onClick={() => cursor && void fetchPage({ cursor, search: activeSearch, categories: selected, sort })}
                  disabled={loading}
                  style={{
                    padding: "10px 22px",
                    border: "none",
                    background: tokens.color.green,
                    color: "#fff",
                    fontWeight: 700,
                    borderRadius: tokens.radius.sm,
                    cursor: "pointer",
                  }}
                >
                  {loading ? "Loading…" : "Load more"}
                </button>
              </div>
            )}
          </section>
        </div>
      </div>
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
        borderRadius: tokens.radius.pill,
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
