import ProductListPage from "./pages/ProductListPage";

// Storefront root. The PLP is the home page (Story 1.3). A router arrives with the
// PDP route in Epic 2; for now the app renders the product listing directly.
export default function App() {
  return <ProductListPage />;
}
