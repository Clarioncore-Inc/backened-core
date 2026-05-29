from sqlalchemy import Column, Numeric, String

from app.core.models import BaseModel


class AppSettings(BaseModel):
    __tablename__ = "app_settings"

    app_name = Column(String, nullable=False, default="CerebroLearn")
    logo = Column(String, nullable=True)
    contacts = Column(String, nullable=True)
    email = Column(String, nullable=True)
    iq_test_price = Column(Numeric(10, 2), nullable=False, default=299.0)