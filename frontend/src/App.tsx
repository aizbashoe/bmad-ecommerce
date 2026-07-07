import { BrowserRouter, Route, Routes } from "react-router-dom";
import StoreHeader from "./components/StoreHeader";
import ProductListPage from "./pages/ProductListPage";
import ProductDetailPage from "./pages/ProductDetailPage";

// Storefront root. A shared shell (StoreHeader) wraps every route (Story 2.1).
// "/" -> PLP (Epic 1), "/products/:id" -> PDP (Epic 2).
export default function App() {
  return (
    <BrowserRouter>
      <StoreHeader />
      <Routes>
        <Route path="/" element={<ProductListPage />} />
        <Route path="/products/:id" element={<ProductDetailPage />} />
      </Routes>
    </BrowserRouter>
  );
}
