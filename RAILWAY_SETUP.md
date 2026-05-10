# Railway Deployment Guide

This repo deploys as **three services** on Railway: `api`, `worker`, and `web`.
Each service has its own `railway.toml` in its subdirectory (`backend/` and `frontend/`).

---

## Prerequisites

- Railway account at https://railway.app
- Railway CLI: `npm i -g @railway/cli`
- Stripe test account at https://dashboard.stripe.com with **Connect enabled**
  (enable at https://dashboard.stripe.com/test/connect/accounts/overview)

---

## Step 1 — Create the Railway project

1. Go to https://railway.app → **New Project** → **Deploy from GitHub repo**
2. Select `partwith/stripe-connect-demo`
3. Railway creates **one** service by default — rename it `api` and set its **Root Directory** to `backend`

---

## Step 2 — Add the worker and web services

In your Railway project dashboard:

**Add worker service:**
1. Click **+ New** → **GitHub Repo** → select `partwith/stripe-connect-demo`
2. Set Root Directory to `backend`
3. Rename the service to `worker`
4. Under **Settings → Deploy**, set Start Command to:
   ```
   celery -A celery_worker.celery_app worker --loglevel=info -c 2
   ```

**Add web service:**
1. Click **+ New** → **GitHub Repo** → select `partwith/stripe-connect-demo`
2. Set Root Directory to `frontend`
3. Rename the service to `web`

---

## Step 3 — Add PostgreSQL and Redis

In the Railway project dashboard:
1. Click **+ New** → **Database** → **PostgreSQL** → Add to project
2. Click **+ New** → **Database** → **Redis** → Add to project

Railway automatically injects `DATABASE_URL` and `REDIS_URL` into all services.

---

## Step 4 — Deploy once to get your domains

Click **Deploy** on all three services. Wait for them to build (the first build takes ~3–5 minutes).

Once deployed, note the public domains Railway assigns:
- `api` service → e.g. `api-production-xxxx.up.railway.app`
- `web` service → e.g. `web-production-xxxx.up.railway.app`

---

## Step 5 — Set environment variables

**On `api` service** → Variables:
```
STRIPE_SECRET_KEY=sk_test_...
STRIPE_WEBHOOK_SECRET=whsec_placeholder   ← update in Step 7
ADMIN_API_KEY=<pick a secure random string>
FRONTEND_URL=https://<web-domain>.up.railway.app
```

**On `worker` service** → Variables:
```
STRIPE_SECRET_KEY=sk_test_...
STRIPE_WEBHOOK_SECRET=whsec_placeholder   ← update in Step 7
ADMIN_API_KEY=<same as api>
```

**On `web` service** → Variables (must be set BEFORE next deploy — baked in at build time):
```
NEXT_PUBLIC_API_URL=https://<api-domain>.up.railway.app
NEXT_PUBLIC_ADMIN_KEY=<same as ADMIN_API_KEY>
```

After setting variables, **redeploy all three services**.

---

## Step 6 — Run the database migration

```bash
railway login
railway link        # select your project when prompted
railway run --service api -- alembic upgrade head
```

Expected output ends with: `Running upgrade -> 52cb6af41ff2, initial_schema`

---

## Step 7 — Register the Stripe webhook

1. Go to https://dashboard.stripe.com/test/webhooks → **Add endpoint**
2. Endpoint URL: `https://<api-domain>.up.railway.app/api/webhooks/stripe`
3. Select event: `account.updated`
4. Click **Add endpoint**
5. Copy the **Signing secret** (starts with `whsec_`)

Update `STRIPE_WEBHOOK_SECRET` on both `api` and `worker` services with this value, then redeploy both.

---

## Step 8 — Verify

```bash
curl https://<api-domain>.up.railway.app/health
# → {"status":"ok"}
```

Open `https://<web-domain>.up.railway.app` — you should see the Stripe Connect Demo landing page.

---

## Environment variable reference

| Variable | Services | Description |
|---|---|---|
| `DATABASE_URL` | api, worker | Auto-set by Railway PostgreSQL plugin |
| `REDIS_URL` | api, worker | Auto-set by Railway Redis plugin |
| `STRIPE_SECRET_KEY` | api, worker | From Stripe dashboard → API keys |
| `STRIPE_WEBHOOK_SECRET` | api, worker | From Stripe dashboard → Webhooks (Step 7) |
| `ADMIN_API_KEY` | api, worker, web | Your choice — used for admin portal auth |
| `FRONTEND_URL` | api | Public URL of the `web` service |
| `NEXT_PUBLIC_API_URL` | web (build-time) | Public URL of the `api` service |
| `NEXT_PUBLIC_ADMIN_KEY` | web (build-time) | Same value as `ADMIN_API_KEY` |
