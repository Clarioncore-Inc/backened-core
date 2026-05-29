from decimal import Decimal, ROUND_HALF_UP

import httpx
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.accounts.models import User
from app.general.models import AppSettings
from app.payments.models import Payment, Payout
from app.settings import FRONTEND_URL, STRIPE_SECRET_KEY
from app.enrollments.services import EnrollmentService

PLATFORM_FEE_RATE = 0.20
DEFAULT_IQ_TEST_PRICE = Decimal("299.0")
STRIPE_API_BASE_URL = "https://api.stripe.com/v1"


class PaymentService:
    def _get_iq_test_price(self, db: Session) -> Decimal:
        settings = db.query(AppSettings).order_by(AppSettings.created_at.asc()).first()
        if settings and settings.iq_test_price is not None:
            return Decimal(str(settings.iq_test_price))
        return DEFAULT_IQ_TEST_PRICE

    def _get_checkout_urls(self) -> tuple[str, str]:
        frontend_url = FRONTEND_URL.rstrip("/")
        success_url = (
            f"{frontend_url}/iq-test-payment-success"
            "?session_id={CHECKOUT_SESSION_ID}"
        )
        cancel_url = f"{frontend_url}/iq-test-overview"
        return success_url, cancel_url

    def _stripe_request(self, method: str, path: str, **kwargs) -> dict:
        if not STRIPE_SECRET_KEY:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Stripe is not configured.",
            )

        headers = kwargs.pop("headers", {})
        headers["Authorization"] = f"Bearer {STRIPE_SECRET_KEY}"

        try:
            response = httpx.request(
                method=method,
                url=f"{STRIPE_API_BASE_URL}{path}",
                headers=headers,
                timeout=30.0,
                **kwargs,
            )
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            detail = "Stripe request failed."
            try:
                stripe_error = exc.response.json().get("error", {})
                detail = stripe_error.get("message") or detail
            except ValueError:
                pass
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=detail,
            ) from exc
        except httpx.HTTPError as exc:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Unable to reach Stripe.",
            ) from exc

        return response.json()

    def create_payment(self, db: Session, user_id, data: dict) -> Payment:
        data["user_id"] = user_id
        payment = Payment(**data)
        db.add(payment)
        db.commit()
        db.refresh(payment)
        return payment

    def create_iq_test_checkout_session(self, db: Session, user_id) -> dict:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

        success_url, cancel_url = self._get_checkout_urls()
        amount = self._get_iq_test_price(db=db)
        amount_cents = int(
            (amount * Decimal("100")).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
        )

        payload = {
            "mode": "payment",
            "success_url": success_url,
            "cancel_url": cancel_url,
            "customer_email": user.email,
            "client_reference_id": str(user.id),
            "metadata[user_id]": str(user.id),
            "metadata[product_type]": "iq_test",
            "line_items[0][price_data][currency]": "usd",
            "line_items[0][price_data][unit_amount]": str(amount_cents),
            "line_items[0][price_data][product_data][name]": "Proctored Psychologist IQ Test",
            "line_items[0][price_data][product_data][description]": (
                "Official psychologist-proctored IQ assessment with certified results."
            ),
            "line_items[0][quantity]": "1",
        }

        session = self._stripe_request("POST", "/checkout/sessions", data=payload)
        return {
            "checkout_url": session["url"],
            "session_id": session["id"],
        }

    def confirm_iq_test_checkout_session(self, db: Session, user_id, session_id: str) -> Payment:
        existing_payment = (
            db.query(Payment)
            .filter(Payment.user_id == user_id, Payment.provider_txn_id == session_id)
            .first()
        )
        if existing_payment:
            return existing_payment

        session = self._stripe_request(
            "GET",
            f"/checkout/sessions/{session_id}",
            params={"expand[]": "payment_intent"},
        )

        metadata = session.get("metadata") or {}
        stripe_user_id = metadata.get("user_id") or session.get("client_reference_id")
        if str(stripe_user_id) != str(user_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="This checkout session does not belong to the current user.",
            )

        if metadata.get("product_type") != "iq_test":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="This checkout session is not for the IQ test flow.",
            )

        if session.get("payment_status") != "paid":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Payment has not been completed yet.",
            )

        amount_total = Decimal(str(session.get("amount_total", 0))) / Decimal("100")
        payment = Payment(
            user_id=user_id,
            amount=amount_total,
            currency=str(session.get("currency") or "USD").upper(),
            provider="stripe",
            provider_txn_id=session_id,
            status="completed",
        )
        db.add(payment)
        db.commit()
        db.refresh(payment)
        return payment

    def update_payment(self, db: Session, payment_id, data: dict) -> Payment:
        payment = db.query(Payment).filter(Payment.id == payment_id).first()
        if not payment:
            return None
        for field, value in data.items():
            setattr(payment, field, value)
        db.commit()

        # Auto-enroll on payment completion
        if data.get("status") == "completed" and payment.course_id:
            EnrollmentService().enroll(
                db=db, user_id=payment.user_id, course_id=payment.course_id
            )

        db.refresh(payment)
        return payment

    def get_creator_earnings(self, db: Session, creator_id):
        """Aggregate completed payments for courses owned by creator, minus 20% fee."""
        from app.courses.models import Course
        courses = db.query(Course).filter(Course.created_by == creator_id).all()
        course_ids = [c.id for c in courses]
        payments = (
            db.query(Payment)
            .filter(
                Payment.course_id.in_(course_ids),
                Payment.status == "completed",
            )
            .all()
        )
        gross = sum(float(p.amount) for p in payments)
        net = gross * (1 - PLATFORM_FEE_RATE)
        return {
            "gross": gross,
            "net": net,
            "platform_fee": gross * PLATFORM_FEE_RATE,
            "currency": "USD",
        }

    def request_payout(self, db: Session, creator_id, data: dict) -> Payout:
        data["creator_id"] = creator_id
        payout = Payout(**data)
        db.add(payout)
        db.commit()
        db.refresh(payout)
        return payout

