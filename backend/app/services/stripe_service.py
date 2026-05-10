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


def create_destination_charge(
    amount: int,
    application_fee_amount: int,
    destination_account: str,
    idempotency_key: str,
) -> stripe.PaymentIntent:
    return stripe.PaymentIntent.create(
        amount=amount,
        currency="usd",
        payment_method_types=["card"],
        application_fee_amount=application_fee_amount,
        transfer_data={"destination": destination_account},
        confirm=True,
        payment_method="pm_card_visa",
        idempotency_key=idempotency_key,
    )


def create_stripe_customer(email: str) -> stripe.Customer:
    return stripe.Customer.create(email=email)


def charge_subscription(
    stripe_customer_id: str,
    amount_cents: int,
    idempotency_key: str,
) -> stripe.PaymentIntent:
    return stripe.PaymentIntent.create(
        amount=amount_cents,
        currency="usd",
        customer=stripe_customer_id,
        payment_method="pm_card_visa",
        payment_method_types=["card"],
        confirm=True,
        setup_future_usage="off_session",
        idempotency_key=idempotency_key,
    )
