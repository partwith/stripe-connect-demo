# Railway Deployment Setup

## Prerequisites
- Railway account at https://railway.app
- Stripe test account at https://dashboard.stripe.com

## Steps

### 1. Deploy to Railway

1. Go to https://railway.app → New Project → Deploy from GitHub repo
2. Select `partwith/stripe-connect-demo`
3. Railway detects `railway.toml` and creates three services: `api`, `worker`, `web`

### 2. Add Database and Cache

In Railway dashboard:
1. Click **+ New** → Database → **PostgreSQL** → Add to project
2. Click **+ New** → Database → **Redis** → Add to project

Railway automatically sets `DATABASE_URL` and `REDIS_URL` on all services.

### 3. Set Environment Variables

**On `api` and `worker` services:**
```
STRIPE_SECRET_KEY=sk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...   (set after step 5)
ADMIN_API_KEY=<your-secure-key>
FRONTEND_URL=https://<web-railway-domain>.railway.app
```

**On `web` service — IMPORTANT: set these as build variables, not just runtime vars.**
Next.js embeds `NEXT_PUBLIC_*` values at build time (`npm run build`). They must be
present when Railway builds the Docker image, not only when the container starts.

In Railway dashboard → `web` service → **Variables** → add:
```
NEXT_PUBLIC_API_URL=https://<api-railway-domain>.railway.app
NEXT_PUBLIC_ADMIN_KEY=<same-as-ADMIN_API_KEY>
```

Then in **Settings → Build** for the `web` service, confirm that environment variables
are passed through to the Docker build (Railway does this automatically when you set
them as service variables before the first deploy).

### 4. Run Database Migration

```bash
npm i -g @railway/cli
railway login
railway link   # select your project
railway run --service api alembic upgrade head
```

### 5. Configure Stripe Webhook

1. Go to https://dashboard.stripe.com/test/webhooks → Add endpoint
2. URL: `https://<api-domain>.railway.app/api/webhooks/stripe`
3. Events: select `account.updated`
4. Copy signing secret → set as `STRIPE_WEBHOOK_SECRET` on `api` and `worker` services

### 6. Verify

```bash
curl https://<api-domain>.railway.app/health
# → {"status":"ok"}
```

Open `https://<web-domain>.railway.app` to see the demo.
