// Shared cart state (Epic 3). Holds the header's live item count. `refresh()` fetches the cart
// (and establishes the anonymous guest session on mount, AD-2); `applyCart(cart)` updates the
// count from a cart the caller already has in hand (after a mutation) — no extra round-trip.

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useState,
  type ReactNode,
} from "react";
import { getCart, type Cart } from "../api/client";

interface CartContextValue {
  count: number; // Σ line-item quantities
  refresh: () => Promise<void>;
  applyCart: (cart: Cart) => void;
}

const countOf = (cart: Cart): number => cart.items.reduce((n, i) => n + i.quantity, 0);

const CartContext = createContext<CartContextValue>({
  count: 0,
  refresh: async () => {},
  applyCart: () => {},
});

export function CartProvider({ children }: { children: ReactNode }) {
  const [count, setCount] = useState(0);

  const applyCart = useCallback((cart: Cart) => setCount(countOf(cart)), []);

  const refresh = useCallback(async () => {
    try {
      applyCart(await getCart());
    } catch {
      // ignore — the header count simply stays as-is if the cart can't be loaded
    }
  }, [applyCart]);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  return (
    <CartContext.Provider value={{ count, refresh, applyCart }}>{children}</CartContext.Provider>
  );
}

export function useCart(): CartContextValue {
  return useContext(CartContext);
}
