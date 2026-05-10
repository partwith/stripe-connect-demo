# Stripe Connect Demo

A demo application showing Stripe Connect vendor onboarding, destination charges, and annual subscription plans — built with FastAPI + Next.js and deployable to Railway.

![Landing page](docs/screenshot-landing.png)

## What it does

- **Vendor onboarding** — vendors register with their business name and email, then complete Stripe's hosted Express account onboarding (identity, bank account, etc.)
- **Webhook sync** — Stripe sends `account.updated` events that automatically update each vendor's onboarding status
- **Destination charges** — admin portal can create charges routed to a vendor's Stripe account, with a 10% platform application fee
- **Subscription plans** — customers purchase annual plans ($10 / $40 / $100) with AI prompt usage quotas; Stripe stores the `cus_` token for future billing, charges use idempotency keys, and the next renewal is due 3 days before expiry
- **Admin portal** — two sections: Stripe Connect vendor management and subscription customer overview (plan, usage left, expiry, next charge date)

## Tech stack

| Layer | Technology |
|---|---|
| Backend API | Python 3.12, FastAPI, SQLAlchemy 2, Alembic |
| Async worker | Celery 5, Redis |
| Database | PostgreSQL |
| Frontend | Next.js 14 (App Router), TypeScript, Tailwind CSS |
| Payments | Stripe Connect (Express accounts), Stripe Customers + PaymentIntents |
| Deployment | Railway (multi-service) |

---

## Screenshots

### Homepage — Subscription Plans

![Landing page](docs/screenshot-landing.png)

### Subscribe Checkout

![Subscribe checkout](docs/screenshot-subscribe.png)

### Admin Portal

![Admin portal](docs/screenshot-admin.png)

---

## Local Development

### Prerequisites

- Python 3.12
- Node.js 20+
- PostgreSQL (running locally)
- Redis (running locally)
- [Stripe CLI](https://stripe.com/docs/stripe-cli) — for webhook forwarding
- A [Stripe test account](https://dashboard.stripe.com)

### 1. Clone and configure

```bash
git clone git@github.com:partwith/stripe-connect-demo.git
cd stripe-connect-demo
```

### 2. Backend setup

```bash
cd backend
cp .env.example .env
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Edit `backend/.env` with your values:

```env
# From https://dashboard.stripe.com/test/apikeys
STRIPE_SECRET_KEY=sk_test_...

# From `stripe listen` output in step 3
STRIPE_WEBHOOK_SECRET=whsec_...

# From https://dashboard.stripe.com/test/apikeys (used by frontend)
STRIPE_PUBLISHABLE_KEY=pk_test_...

# Create the DB first: createdb stripe_demo
DATABASE_URL=postgresql://youruser@localhost:5432/stripe_demo

# Redis connection (default works if Redis is running locally)
REDIS_URL=redis://localhost:6379/0

# URL the backend uses for CORS — leave as-is for local dev
FRONTEND_URL=http://localhost:3000

# Secret header value required by all /api/admin/* endpoints
ADMIN_API_KEY=demo-admin-key-change-me
```

Create the database and run migrations:

```bash
createdb stripe_demo   # or via psql
alembic upgrade head
```

### 3. Start the Stripe webhook listener

In a dedicated terminal (keep it running):

```bash
stripe listen \
  --api-key sk_test_... \
  --forward-to localhost:8000/api/webhooks/stripe
```

Copy the `whsec_...` signing secret it prints and paste it into `.env` as `STRIPE_WEBHOOK_SECRET`.

### 4. Start the backend

```bash
cd backend
source .venv/bin/activate
uvicorn app.main:app --reload --port 8000
```

Verify: `curl http://localhost:8000/health` → `{"status":"ok"}`

### 5. Start the frontend

```bash
cd frontend
npm install
NEXT_PUBLIC_API_URL=http://localhost:8000 \
NEXT_PUBLIC_ADMIN_KEY=demo-admin-key-change-me \
npm run dev
```

Open **http://localhost:3000**.

### 6. (Optional) Start the Celery worker

The worker periodically syncs all non-complete vendor statuses from Stripe (every 5 minutes). Not required for basic testing — the webhook listener handles real-time updates.

```bash
cd backend
source .venv/bin/activate
celery -A celery_worker.celery_app worker --loglevel=info
```

---

## Usage

### Subscription flow

1. Go to **http://localhost:3000** and scroll to **Subscription Plans**
2. Choose a plan — Basic ($10 / 100 prompts), Standard ($40 / 500 prompts), or Premium ($100 / 2 000 prompts)
3. Enter your email and click **Subscribe** — the backend creates a Stripe Customer (`cus_…`), charges the test card with an idempotency key, and stores the subscription
4. You're redirected to a confirmation page with your subscription ID
5. In the **Admin Portal** → **Subscription Customers** section you can see the plan, prompts remaining, expiry date (1 year), and next charge due date (3 days before expiry)

> **Billing logic:** `expires_at = starts_at + 365 days`, `next_charge_due_at = expires_at − 3 days`. The Stripe Customer token is persisted so future renewals can be charged off-session.

### Vendor onboarding flow

1. Go to **http://localhost:3000/vendor/register**
2. Enter a business name and email
3. Click **Continue to Stripe Onboarding** — you're redirected to Stripe's hosted flow
4. Complete onboarding using [Stripe test data](https://stripe.com/docs/connect/testing) (no real info needed)
5. After completing, you're returned to the app with your status

For Stripe test onboarding, use:
- Routing number: `110000000`
- Account number: `000123456`
- Any future date for DOB
- ABN (Australian Business Number): `51824753556` (or `83914571673`)

### Admin portal

Go to **http://localhost:3000/admin**

**Section 1 — Stripe Connect Vendors:**
- See all vendors with their onboarding status
- Click any vendor to view full Stripe account details and create destination charges
- Click **Sync Stripe Status** to pull the latest data from Stripe on demand

**Section 2 — Subscription Customers:**
- See all subscribers with their plan tier, AI prompts remaining, expiry date, next charge due date, and status badge

Admin API key defaults to `demo-admin-key-change-me` (set via `ADMIN_API_KEY` env var).

---

## API reference

All endpoints are served from the FastAPI backend (`http://localhost:8000`).

### Vendor endpoints

| Method | Path | Description |
|---|---|---|
| `POST` | `/api/vendors/` | Register a new vendor + create Stripe Express account |
| `POST` | `/api/vendors/{id}/onboard` | Generate a Stripe account link URL |
| `GET` | `/api/vendors/{id}` | Get vendor status |

### Subscription endpoints

| Method | Path | Description |
|---|---|---|
| `POST` | `/api/subscriptions/` | Purchase a subscription plan (creates Stripe Customer + charges) |

### Admin endpoints (requires `X-Admin-Key` header)

| Method | Path | Description |
|---|---|---|
| `GET` | `/api/admin/vendors` | List all vendors |
| `GET` | `/api/admin/vendors/{id}` | Get vendor detail |
| `POST` | `/api/admin/vendors/{id}/sync` | Pull latest status from Stripe |
| `POST` | `/api/admin/vendors/{id}/charge` | Create a destination charge to a vendor |
| `GET` | `/api/admin/vendors/{id}/orders` | List orders for a vendor |
| `GET` | `/api/admin/subscriptions` | List all subscription customers |

### Webhooks

| Method | Path | Description |
|---|---|---|
| `POST` | `/api/webhooks/stripe` | Stripe webhook receiver (`account.updated`, `payment_intent.succeeded/failed`) |

---

## Running tests

```bash
cd backend
source .venv/bin/activate
pytest tests/ -v
```

41 tests covering vendor registration, onboarding, admin API, webhook handling, destination charges, subscription creation (all tiers), billing date logic, idempotency, Stripe failure rollback, and the Stripe service layer.

---

## Deployment (Railway)

See [RAILWAY_SETUP.md](RAILWAY_SETUP.md) for the full step-by-step guide.

**TL;DR:**

1. Push this repo to GitHub
2. Create a Railway project → deploy from GitHub
3. Add PostgreSQL and Redis plugins
4. Set environment variables on each service
5. Run `railway run --service api alembic upgrade head`
6. Register the webhook endpoint in the Stripe dashboard

---

## Project structure

```
stripe-connect-demo/
├── backend/
│   ├── app/
│   │   ├── main.py           # FastAPI app
│   │   ├── config.py         # Environment config
│   │   ├── database.py       # SQLAlchemy setup
│   │   ├── models/           # Vendor, Order, Subscription models
│   │   ├── schemas/          # Pydantic schemas
│   │   ├── routers/          # vendor, admin, webhook, subscription
│   │   ├── services/         # Stripe SDK wrapper
│   │   └── tasks/            # Celery tasks
│   ├── celery_worker.py
│   ├── alembic/              # Database migrations
│   └── requirements.txt
├── frontend/
│   └── src/
│       ├── app/              # Next.js pages
│       │   ├── page.tsx              # Landing + subscription plans
│       │   ├── vendor/register/      # Vendor registration
│       │   ├── return/               # Post-Stripe return
│       │   ├── subscribe/[tier]/     # Subscription checkout
│       │   ├── subscribe/confirm/    # Subscription confirmation
│       │   └── admin/                # Admin portal (vendors + subscriptions)
│       ├── components/       # Nav, StatusBadge, VendorCard
│       └── lib/              # API client, TypeScript types
├── docs/                     # Screenshots
├── railway.toml              # Railway deployment config
└── RAILWAY_SETUP.md          # Deployment guide
```
