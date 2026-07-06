---
title: 'PLP category badge on product tiles'
type: 'feature'
created: '2026-07-07'
status: 'done'
route: 'one-shot'
---

# PLP category badge on product tiles

## Intent

**Problem:** Product tiles on the PLP showed no category, making it hard to tell which category a product belongs to (and hard to visually confirm that category filtering is working).

**Approach:** Add a small category "stamp" — an absolute-positioned pill over the top-left of each tile's image — rendering `product.category`. Truncates with an ellipsis for long names; purely cosmetic, no data/API change.

## Suggested Review Order

1. [ProductListPage.tsx — product card + badge](../../frontend/src/pages/ProductListPage.tsx) — the `position: relative` anchor and the absolute category `<span>` (uppercase pill, width-guarded with ellipsis).

*One-shot change. Blind Hunter review: materially clean; one Low finding (long-name overflow) auto-patched with `maxWidth`/`nowrap`/`ellipsis`.*
