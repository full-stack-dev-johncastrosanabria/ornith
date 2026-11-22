# Products API

`PUT /products/{id}` replaces a product's editable fields. Body: `{ "name", "price", "stock", "version" }`.

1. 404 Not Found when no product has this id.
2. 400 (validation problem) when the body breaks the same rules as POST (name not blank and at most 80
   characters after trimming, price >= 0, stock from 0 to 10000) or when `version` is missing.
3. 409 Conflict when `version` differs from the stored version (another client updated the product first);
   nothing changes.
4. Otherwise the product is updated in place: same id, name trimmed, new price and stock, version + 1.
   Respond 200 with the updated product.
