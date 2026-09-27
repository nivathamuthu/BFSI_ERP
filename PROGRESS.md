# Progress

Built from the insurance ERP spec in this repo. Phases 0–6 are in the codebase and covered by pytest.

| Phase | What landed | Status |
|---|---|---|
| 0 | Django project, DRF, SQLite by default and Postgres via Docker Compose, JWT register/login/refresh, Swagger at `/api/docs/`, `TimeStampedModel`, role permission | Done |
| 1 | Customers and policies, including date and premium validation | Done |
| 2 | Claims and underwriting with status transitions | Done |
| 3 | Invoices, transactions, and outstanding balance per customer | Done |
| 4 | Compliance rules/reports and document upload/download | Done |
| 5 | Mock identity verification and rules-based claim fraud flags | Done |
| 6 | Admin / underwriter / claims-adjuster permissions, filtering and pagination, Postman collection, `seed_demo`, tests, this file, README | Done |

How to pick it up: read the business flow in `README.md`, run `python manage.py seed_demo`, then open `/api/docs/`.
