"""Idempotent synthetic-catalog seed (FR-16).

Generates a deterministic catalog (fixed, index-derived ids) so re-running overwrites
existing items rather than duplicating. Provisions the table via the repository, then
batch-writes the products. Run with:  python -m scripts.seed
(inside the api container:  docker compose exec api python -m scripts.seed)
"""

from app.models.product import Product
from app.repositories.products import ProductsRepository

# ≥4 categories to exercise the category facet.
CATEGORIES = ["apparel", "electronics", "home", "books", "toys", "sports"]

# A handful of adjective/noun parts per category → varied, searchable names.
_ADJECTIVES = ["Classic", "Deluxe", "Compact", "Premium", "Eco", "Rugged", "Sleek", "Vintage"]
_NOUNS = {
    "apparel": ["Tee", "Hoodie", "Jacket", "Cap", "Socks"],
    "electronics": ["Headphones", "Charger", "Speaker", "Webcam", "Mouse"],
    "home": ["Mug", "Lamp", "Blanket", "Planter", "Cutting Board"],
    "books": ["Notebook", "Novel", "Cookbook", "Journal", "Atlas"],
    "toys": ["Puzzle", "Blocks", "Drone", "Figurine", "Board Game"],
    "sports": ["Water Bottle", "Yoga Mat", "Dumbbell", "Jump Rope", "Backpack"],
}

PRODUCTS_PER_CATEGORY = 40  # 6 categories * 40 = 240 products (within ~100–500)


def generate_products() -> list[Product]:
    """Deterministic catalog — no randomness, so ids/content are stable across runs."""
    products: list[Product] = []
    index = 0
    for category in CATEGORIES:
        nouns = _NOUNS.get(category)
        if not nouns:
            raise ValueError(f"seed: category {category!r} has no entry in _NOUNS")
        for i in range(PRODUCTS_PER_CATEGORY):
            index += 1
            adj = _ADJECTIVES[i % len(_ADJECTIVES)]
            noun = nouns[i % len(nouns)]
            product_id = f"p-{index:04d}"
            # Price 500–19,999 cents, spread deterministically for sort/facet testing.
            price = 500 + (index * 137) % 19_500
            products.append(
                Product(
                    product_id=product_id,
                    name=f"{adj} {noun} {index}",
                    description=f"A {adj.lower()} {noun.lower()} in our {category} range. Item #{index}.",
                    price=price,
                    category=category,
                    image_url=f"https://picsum.photos/seed/{product_id}/400/400",
                    available=(index % 11 != 0),  # ~1 in 11 out of stock
                )
            )
    return products


def main() -> None:
    repo = ProductsRepository()
    repo.ensure_table()
    products = generate_products()
    repo.batch_put(products)
    categories = sorted({p.category for p in products})
    print(f"Seeded {len(products)} products across {len(categories)} categories: {', '.join(categories)}")
    print(f"Table '{repo.table_name}' now reports {repo.count()} items.")


if __name__ == "__main__":
    main()
