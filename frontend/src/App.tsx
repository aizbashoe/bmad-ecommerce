import { useEffect, useState } from "react";
import { getHealth } from "./api/client";

// Walking-skeleton page: proves the frontend can reach the API through the typed
// client (AC-6). Real pages (PLP/PDP/Cart/Checkout/OrderSummary) land in later stories.
export default function App() {
  const [apiStatus, setApiStatus] = useState<string>("checking…");

  useEffect(() => {
    getHealth()
      .then((h) => setApiStatus(h.status))
      .catch(() => setApiStatus("unreachable"));
  }, []);

  return (
    <main style={{ fontFamily: "system-ui, sans-serif", padding: "2rem" }}>
      <h1>BMAD E-Commerce Storefront</h1>
      <p>Walking skeleton — Story 1.1.</p>
      <p>
        API: <strong data-testid="api-status">{apiStatus}</strong>
      </p>
    </main>
  );
}
