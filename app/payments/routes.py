from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from fastapi_utils.cbv import cbv
from sqlalchemy.orm import Session

from app.core.dependency_injection import service_locator
from app.payments.schemas import (
    PaymentCreate,
    PaymentResponse,
    PaymentUpdate,
    PayoutCreate,
    PayoutResponse,
)
from app.dependencies import get_db
from app.authentication.utils import get_current_active_user
from app.accounts.models import User

router = APIRouter(prefix="/payments", tags=["payments"])
payouts_router = APIRouter(prefix="/payouts", tags=["payments"])


@cbv(router)
class PaymentsView:
    db: Session = Depends(get_db)
    current_user: User = Depends(get_current_active_user)

    @router.post("/", response_model=PaymentResponse, status_code=201)
    def create_payment(self, payload: PaymentCreate):
        data = payload.model_dump()
        return service_locator.payment_service.create_payment(
            db=self.db, user_id=self.current_user.id, data=data
        )

    @router.put("/{payment_id}", response_model=PaymentResponse)
    def update_payment(self, payment_id: UUID, payload: PaymentUpdate):
        payment = service_locator.payment_service.update_payment(
            db=self.db,
            payment_id=payment_id,
            data=payload.model_dump(exclude_unset=True),
        )
        if not payment:
            raise HTTPException(status_code=404, detail="Payment not found")
        return payment


@cbv(payouts_router)
class PayoutsView:
    db: Session = Depends(get_db)
    current_user: User = Depends(get_current_active_user)

    @payouts_router.post("/", response_model=PayoutResponse, status_code=201)
    def request_payout(self, payload: PayoutCreate):
        if self.current_user.role not in ("creator", "instructor", "admin"):
            raise HTTPException(
                status_code=403, detail="Only creators can request payouts")
        data = payload.model_dump()
        return service_locator.payment_service.request_payout(
            db=self.db, creator_id=self.current_user.id, data=data
        )
