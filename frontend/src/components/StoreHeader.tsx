import { Link } from "react-router-dom";
import { tokens } from "../theme/tokens";

// Shared storefront shell header (Story 2.1). Wraps every page; the wordmark links home.
// Search stays in the PLP body for now; the header search + live cart count arrive with the
// PLP restyle and Epic 3 respectively.
export default function StoreHeader() {
  return (
    <header style={{ background: tokens.color.header, color: "#fff", fontFamily: tokens.font }}>
      <div
        style={{
          display: "flex",
          alignItems: "center",
          gap: 16,
          maxWidth: 1240,
          margin: "0 auto",
          padding: "12px 20px",
        }}
      >
        <Link
          to="/"
          aria-label="BMAD POC Store — home"
          style={{
            fontWeight: 800,
            fontSize: 20,
            color: "#fff",
            textDecoration: "none",
            letterSpacing: "-0.02em",
          }}
        >
          BMAD <span style={{ color: tokens.color.green }}>POC</span> Store
        </Link>
        <span style={{ marginLeft: "auto", fontSize: 13, opacity: 0.85 }}>🛒 Cart</span>
      </div>
    </header>
  );
}
