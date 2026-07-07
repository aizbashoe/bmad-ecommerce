import { BrowserRouter, Route, Routes } from "react-router-dom";
import StoreHeader from "./components/StoreHeader";
import { CartProvider } from "./state/cart";
import ProductListPage from "./pages/ProductListPage";
import ProductDetailPage from "./pages/ProductDetailPage";
import CartPage from "./pages/CartPage";

// Storefront root. A shared shell (StoreHeader) + cart state (CartProvider) wrap every route.
// "/" -> PLP (Epic 1), "/products/:id" -> PDP (Epic 2), "/cart" -> Cart (Epic 3).
export default function App() {
  return (
    <BrowserRouter>
      <CartProvider>
        <StoreHeader />
        <Routes>
          <Route path="/" element={<ProductListPage />} />
          <Route path="/products/:id" element={<ProductDetailPage />} />
          <Route path="/cart" element={<CartPage />} />
        </Routes>
      </CartProvider>
    </BrowserRouter>
  );
}
