from sqlalchemy import Column, Integer, Numeric, String

from app.core.models import BaseModel


class AppSettings(BaseModel):
    __tablename__ = "app_settings"

    app_name = Column(String, nullable=False, default="CerebroLearn")
    logo = Column(String, nullable=True)
    contacts = Column(String, nullable=True)
    email = Column(String, nullable=True)
    iq_test_price = Column(Numeric(10, 2), nullable=False, default=299.0)
    refresh_booking_in_minute = Column(Integer, nullable=False, default=5)
    psychologist_booking_reminder_in_minutes = Column(
        Integer, nullable=False, default=30
    )