
from sqlalchemy import (
    Column, Integer, String, ForeignKey, Date)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.models import BaseModel
from app.lessons.models import section_attachments


class Attachment(BaseModel):
    __tablename__ = "attachments"

    url = Column(String, nullable=False)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    filename = Column(String)
    file_size = Column(Integer)
    mime_type = Column(String)
    s3_key = Column(String)
    thumbnail = Column(String)
    upload_finished_at = Column(Date)
    sections = relationship(
        "Section", secondary=section_attachments, back_populates="attachments")

    user = relationship("User", back_populates="attachments")
