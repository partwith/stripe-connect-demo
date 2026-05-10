import stripe
from app.config import settings

stripe.api_key = settings.stripe_secret_key


def create_express_account(email: str, business_name: str) -> stripe.Account:
    return stripe.Account.create(
        type="express",
        email=email,
        business_profile={"name": business_name},
        capabilities={
            "card_payments": {"requested": True},
            "transfers": {"requested": True},
        },
    )


def create_account_link(account_id: str, return_url: str, refresh_url: str) -> str:
    link = stripe.AccountLink.create(
        account=account_id,
        refresh_url=refresh_url,
        return_url=return_url,
        type="account_onboarding",
    )
    return link.url


def get_account(account_id: str) -> stripe.Account:
    return stripe.Account.retrieve(account_id)


def construct_webhook_event(payload: bytes, sig_header: str) -> stripe.Event:
    return stripe.Webhook.construct_event(
        payload, sig_header, settings.stripe_webhook_secret
    )
