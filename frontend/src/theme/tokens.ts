// Design tokens mirrored from the UX DESIGN.md spine
// (_bmad-output/planning-artifacts/ux-designs/ux-bmad-ecommerce-2026-07-07/DESIGN.md).
// Single source for the shared shell + PDP styling; the PLP restyle and cart/checkout reuse these.

export const tokens = {
  color: {
    green: "#159f4a",
    greenDark: "#0f7d3a",
    ink: "#17181a",
    muted: "#6b7280",
    line: "#e5e7eb",
    bg: "#f4f5f7",
    surface: "#ffffff",
    header: "#1f1f1f",
    price: "#d81e2c", // brand price accent — NOT a discount signal (we have no discounts)
    badge: "rgba(17,24,39,0.82)",
    stockIn: "#0f7d3a",
    stockOut: "#9ca3af",
    error: "#b91c1c",
  },
  radius: { sm: 8, md: 10, pill: 999 },
  font: 'system-ui, -apple-system, "Segoe UI", Roboto, sans-serif',
} as const;
