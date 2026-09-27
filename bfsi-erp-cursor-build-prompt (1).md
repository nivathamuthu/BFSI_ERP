# ERP for BFSI (Insurance) — Cursor Build Spec & Prompt

This file is meant to be dropped into a new repo and used with **Cursor's Agent/Composer mode**
to build a portfolio-ready version of the BFSI Insurance ERP from your resume — policy
administration, claims, underwriting, financial accounting, compliance, and document management,
built on Django REST Framework to match your actual work experience.

The full spec covers 8 modules end-to-end; that's a multi-quarter enterprise build. This file scopes
it into phases so Cursor builds a working slice at a time instead of stalling on scope.

---

## 1. What you're building

A Django REST Framework backend where an insurer can manage customers, issue and administer
policies, process claims, run underwriting, post financial transactions, track compliance, store
documents, and verify identity — all through clean, testable REST APIs with proper auth and
validation. This is the same domain as your Winsser/Blueberry work, built as a standalone repo you
can show and talk through in an interview.

---

## 2. Tech stack

| Layer | Choice |
|---|---|
| Framework | Django + Django REST Framework |
| Database | PostgreSQL (primary), SQLite fine for local dev if you want zero setup first |
| Auth | JWT (`djangorestframework-simplejwt`) |
| Docs | drf-spectacular or drf-yasg (Swagger/OpenAPI) |
| File storage | Local media storage first; swap in S3-compatible (MinIO) if you want the extra credit |
| Validation | DRF serializers + Django validators |
| Testing | pytest + pytest-django, or Django's built-in test framework |
| Containerization | Docker Compose (Postgres + web) |
| Tooling | Git, Postman collection, GitHub Actions for CI (optional, phase 6) |

---

## 3. Suggested repo structure (Django apps per domain)

```
bfsi_erp/
├── docker-compose.yml
├── requirements.txt
├── manage.py
├── config/                 # Django project settings
│   ├── settings.py
│   ├── urls.py
├── core/                   # shared abstract models (TimeStampedModel), permissions, utils
├── customers/              # CRM: Customer Management API
├── policies/               # Policy Administration API
├── claims/                 # Claims Processing API
├── underwriting/           # Underwriting API
├── finance/                # Financial Accounting API (transactions, invoices)
├── compliance/             # Compliance Management API
├── documents/              # Document Management API
├── identity/               # Identity Verification API
└── tests/
```

Each domain app gets its own `models.py`, `serializers.py`, `views.py` (ViewSets), `urls.py`.

---

## 4. Data model (from your spec, with relationships made explicit)

| Model | Key fields | Relations |
|---|---|---|
| **Customer** | name, email, phone, address, created_at, updated_at | — |
| **Policy** | policy_number, type, start_date, end_date, premium_amount, status | `customer` FK → Customer |
| **Claim** | claim_number, claimant_name, claim_date, description, amount, status | `policy` FK → Policy |
| **UnderwritingRequest** | policy_type, details, status | `customer` FK → Customer |
| **Transaction** | transaction_number, type, amount, date, description | — |
| **Invoice** | invoice_number, amount, due_date, status | `customer` FK → Customer |
| **ComplianceRule** | name, description, status | — |
| **ComplianceReport** | report_number, date, status, details | optionally FK → ComplianceRule |
| **Document** | name, type, size, url | generic FK or explicit FKs to Policy/Claim/Underwriting for "attached to" |
| **IdentityVerificationRequest** | document_type, document_number, status | `customer` FK → Customer |

Use a shared abstract `TimeStampedModel` (created_at, updated_at) in `core/models.py` and inherit
it everywhere instead of repeating those two fields per model.

---

## 5. API surface (from your spec)

| Module | Base path | Endpoints |
|---|---|---|
| Customer Management | `/api/customers/` | GET/POST list+create; GET/PUT/DELETE `/api/customers/{id}/` |
| Policy Administration | `/api/policies/` | GET/POST list+create; GET/PUT/DELETE `/api/policies/{id}/` |
| Claims Processing | `/api/claims/` | GET/POST list+create; GET/PUT/DELETE `/api/claims/{id}/` |
| Underwriting | `/api/underwriting/` | GET/POST list+create; GET/PUT/DELETE `/api/underwriting/{id}/` |
| Financial Accounting | `/api/finance/transactions/`, `/api/finance/invoices/` | GET/POST on each |
| Compliance | `/api/compliance/rules/`, `/api/compliance/reports/` | GET/POST on each |
| Document Management | `/api/documents/` | GET/POST list+create; GET (download)/PUT/DELETE `/api/documents/{id}/` |
| Identity Verification | `/api/identity/verify/` | POST only |

Add pagination, filtering (`django-filter`), and ordering on every list endpoint — small addition,
big interview talking point.

---

## 6. Build phases (do these in order)

**Phase 0 — Scaffolding**
Django project + DRF installed, Postgres via Docker Compose, JWT auth wired up (register/login/
refresh), Swagger docs live at `/api/docs/`, `core` app with the shared abstract model and a
custom `IsAuthenticated`-based permission class. Confirm `/api/docs/` loads before continuing.

**Phase 1 — Customer + Policy**
Build `customers` and `policies` apps fully: models, migrations, serializers with validation
(e.g. `end_date` > `start_date`, `premium_amount` > 0), ViewSets, URLs, and tests for each CRUD
path. This is your core reference pattern — every later app copies this structure.

**Phase 2 — Claims + Underwriting**
Same pattern as Phase 1. Add status-transition logic (e.g. a claim can't go from `settled` back to
`intake`) using a small state machine or just validated choices — this is a natural place to show
business-logic thinking, not just CRUD.

**Phase 3 — Financial Accounting**
`Transaction` and `Invoice` models/APIs. Link invoices to customers and, where relevant, to
policies. Add a simple computed field or endpoint (e.g. outstanding balance per customer) so it's
not pure CRUD.

**Phase 4 — Compliance + Document Management**
Compliance rules/reports APIs. Document upload/download using Django's file storage (local first),
with file type/size validation on upload. Link documents to policies/claims/underwriting via FK or
a generic relation.

**Phase 5 — Identity Verification + validation/fraud checks**
Build `/api/identity/verify/` as a stub that accepts documents and returns a mocked verification
result (don't fake a real third-party integration — note in the README that this stands in for a
service like Onfido/Jumio). Add basic fraud-check logic as a rules-based function (flag claims over
a threshold, mismatched claimant/policyholder names, etc.) — enough to demonstrate the idea.

**Phase 6 — Polish (portfolio-critical)**
Role-based permissions (e.g. underwriter vs claims-adjuster vs admin), pagination/filtering on all
list endpoints, a Postman collection exported to the repo, pytest coverage on the core flows, a
seed script with realistic sample data, and a README with setup steps + a short architecture note.

Don't let Cursor jump to Phase 4+ before 0–3 are working end-to-end with passing tests.

---

## 7. The prompt — paste this into Cursor's Agent/Composer

```
You are helping me build a Django REST Framework backend: an ERP system for a BFSI
(insurance) company. I'm an experienced backend developer (3+ years Python/Django/DRF,
BFSI domain) building this as a portfolio project, so write production-quality code — proper
serializer validation, sensible model relationships, permission classes, and tests, not toy CRUD.

Stack: Django + Django REST Framework, PostgreSQL, JWT auth via djangorestframework-simplejwt,
drf-spectacular for OpenAPI/Swagger docs, pytest-django for tests, Docker Compose for local dev.

Data model:
- Customer(name, email, phone, address, timestamps)
- Policy(policy_number, customer FK, type, start_date, end_date, premium_amount, status, timestamps)
- Claim(claim_number, policy FK, claimant_name, claim_date, description, amount, status, timestamps)
- UnderwritingRequest(policy_type, customer FK, details, status, timestamps)
- Transaction(transaction_number, type, amount, date, description, timestamps)
- Invoice(invoice_number, customer FK, amount, due_date, status, timestamps)
- ComplianceRule(name, description, status, timestamps)
- ComplianceReport(report_number, date, status, details, timestamps)
- Document(name, type, size, url, timestamps, linked to Policy/Claim/UnderwritingRequest)
- IdentityVerificationRequest(customer FK, document_type, document_number, status, timestamps)

Build this in phases, and do NOT skip ahead:

Phase 0: Django project scaffold, DRF, Postgres via docker-compose, JWT auth (register/login/
refresh), Swagger docs at /api/docs/, a `core` app with a shared TimeStampedModel abstract
base and a base permission class. Confirm docs load before moving on.

Phase 1: Full `customers` and `policies` apps — models, migrations, serializers with real
validation (e.g. end_date after start_date, premium_amount positive), ViewSets, URLs, and
tests for every CRUD path. This is the reference pattern every later app follows.

Phase 2: `claims` and `underwriting` apps, same pattern, plus status-transition validation so
records can't move to invalid states.

Phase 3: `finance` app — Transaction and Invoice APIs, linked to customers/policies, plus one
computed endpoint (e.g. outstanding balance per customer).

Phase 4: `compliance` app (rules + reports) and `documents` app with file upload/download,
type/size validation, and linkage to policies/claims/underwriting.

Phase 5: `identity` app with a stubbed verification endpoint (clearly noted as mocking a
real provider) and a simple rules-based fraud-check function on claims.

Phase 6: role-based permissions (admin/underwriter/claims-adjuster), pagination and filtering
on all list endpoints, a Postman collection, a seed data script, pytest coverage on core
flows, and a README with setup instructions.

Start with Phase 0 only. Ask me before moving to the next phase. After each phase, tell me
exactly how to test it (curl or Postman examples) and make sure migrations and tests actually
pass before we move on. Keep commits scoped to one phase at a time.
```

---

## 8. Notes for using Cursor well here

- Use **Agent mode** — this has enough interlinked models that inline autocomplete alone will
  drift from the schema.
- After each phase, actually run `python manage.py test` yourself before saying "continue."
- If Cursor suggests a real third-party ID-verification integration, redirect it to the mocked
  version — don't ship fake credentials or a half-working external call.
- Ask Cursor to maintain a `PROGRESS.md` so you can pick this back up across sessions without
  re-explaining the schema every time.
- Once Phases 0–3 work, you already have a demo-able project — Phases 4–6 are what push it from
  "CRUD demo" to "shows real engineering judgment" in an interview.
