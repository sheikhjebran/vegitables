# Current Backend State

## Runtime baseline

- Django version target is `>=4.0,<5.0`.
- The project currently runs from `vegitable/manage.py`.
- Local development defaults to SQLite.
- Production deployment supports MySQL through environment variables.
- Session storage is configured as `django.contrib.sessions.backends.db`.

## Current backend characteristics

- The app is a server-rendered Django project with DRF endpoints mixed into the same codebase.
- Business logic is concentrated in `vegitable/shops/views.py` and `vegitable/shops/shop_views/`.
- The data model is relational and centered around `Shop`, `Index`, arrival flows, sales flows, patti flows, ledgers, credit bills, and mobile sales cache rows.

## Code patterns that matter for migration

- Most requests resolve the active `Shop` from `request.user`.
- Multiple flows use `ForeignKey` relations as if joins are cheap and always available.
- Reports depend on `values`, `values_list`, `annotate`, `aggregate`, `F`, and `Q` expressions.
- Several forms use `request.session` form tokens.
- Incrementing counters in `Index` assumes transactional relational updates.

## High-risk migration surfaces

- `SalesBillEntry` plus `SalesBillItem`: parent-child writes and summary reads.
- `ArrivalEntry` plus `ArrivalGoods`: inventory-style updates and decrement logic.
- `CreditBillEntry` plus `CreditBillHistory`: dependent records and balance tracking.
- `PattiEntry` plus `PattiEntryList`: grouped write patterns.
- `Shop` plus `User`: hard dependency on Django auth.

## Conclusion

This backend is not currently shaped for a direct backend swap. The safest path is to introduce Firebase behind a bounded domain boundary first, keep SQL for framework-owned concerns, and only cut over data slices after query rewrites and validation.