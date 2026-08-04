# Model Mapping And Rewrite Notes

## Proposed Firestore migration order

1. `MobileSalesBill`
2. `CustomerLedger`
3. `FarmerLedger`
4. `ArrivalEntry` and `ArrivalGoods`
5. `PattiEntry` and `PattiEntryList`
6. `SalesBillEntry`, `SalesBillItem`, `CreditBillEntry`, `CreditBillHistory`
7. Reporting read models

## Model-by-model notes

### `Shop`

- Keep in SQL initially.
- It currently anchors ownership through Django `User`.
- Firebase documents should reference `shop_id` as a scalar field, not a Django relation.

### `Index`

- Keep in SQL until a Firestore transaction strategy is implemented.
- Replace each mutable counter with either a dedicated counter document or a namespaced counter collection.

### `MobileSalesBill`

- Good first Firebase candidate.
- Suggested document fields: `shop_id`, `name`, `lot_no`, `total_bags`, `net_weight`, `created_at`, `updated_at`.
- Current queries are simple enough to port with equality filtering.

### `CustomerLedger` and `FarmerLedger`

- Migrate as independent top-level collections.
- Add normalized search fields such as `name_lower`, `contact_normalized`, and maybe `search_prefixes`.
- Replace `icontains` with a defined search capability instead of pretending Firestore supports it.
- Current `CustomerLedger` migration will start with normalized fields plus app-layer substring filtering on shop-scoped results.
- `FarmerLedger` should mirror the same approach, using normalized `place` search plus app-layer filtering first.

### `ArrivalEntry` and `ArrivalGoods`

- Decide whether goods should be embedded inside the arrival document or stored as a subcollection.
- Stock decrements must become transactional.
- Avoid depending on SQL-style reverse relations.
- Current migration starts with embedded goods rows inside the arrival document so Firestore validation can proceed before live stock consumers are switched.

### `PattiEntry` and `PattiEntryList`

- Treat as parent document plus embedded lines if line counts stay small.
- If line counts can grow significantly, use a subcollection and a summary snapshot on the parent.

### `SalesBillEntry` and `SalesBillItem`

- Consider embedding item rows directly inside the bill document.
- Persist derived totals explicitly to avoid runtime aggregation.
- Capture `shop_id`, customer name, payment mode, and balance fields directly on the document.
- Current migration starts with embedded items that store `arrival_entry_id` and `arrival_goods_local_id` so stock can be mutated without SQL foreign keys.

### `CreditBillEntry` and `CreditBillHistory`

- Likely better as a credit parent document with a payment-history subcollection.
- Store running totals or current balance on the parent to avoid repeated scans.

## Query rewrite rules

- Replace joins with explicit document references or duplicated display fields.
- Replace aggregates with denormalized totals updated on write.
- Replace `order_by('-id')` with timestamp-based ordering.
- Replace auto-increment assumptions with generated IDs plus business-friendly display counters.