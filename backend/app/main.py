from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.routers import vendor as vendor_router
from app.routers import admin as admin_router
from app.routers import webhook as webhook_router
from app.routers import subscription as subscription_router

app = FastAPI(title="Stripe Connect Demo", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_url, "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(vendor_router.router, prefix="/api/vendors", tags=["vendors"])
app.include_router(admin_router.router, prefix="/api/admin", tags=["admin"])
app.include_router(webhook_router.router, prefix="/api/webhooks", tags=["webhooks"])
app.include_router(subscription_router.router, prefix="/api/subscriptions", tags=["subscriptions"])


@app.get("/health")
def health():
    return {"status": "ok"}
