from sqlalchemy.orm import Session
from app.payments.models import Payment, Payout
from app.enrollments.services import EnrollmentService

PLATFORM_FEE_RATE = 0.20


class PaymentService:
    def create_payment(self, db: Session, user_id, data: dict) -> Payment:
        data["user_id"] = user_id
        payment = Payment(**data)
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

