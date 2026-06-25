from typing import Optional

from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text
from sqlalchemy.sql import func

from app.database import Base


def _iq_label(iq: Optional[int], profile_type: str) -> str:
    if not iq:
        return "No verified IQ score"
    return "Estimated historical IQ" if profile_type == "historical" else "Reported/estimated IQ"


def _iq_note(iq: Optional[int]) -> str:
    if not iq:
        return "No verified IQ score is shown. This profile uses expertise, influence, and documented achievements instead."
    return "IQ values shown here are estimates or widely circulated public figures, not verified clinical records."


class GeniusProfile(Base):
    __tablename__ = "genius_profiles"

    id = Column(String, primary_key=True)
    slug = Column(String, unique=True, nullable=False, index=True)
    full_name = Column(String, nullable=False)
    iq_score = Column(Integer, nullable=True)
    iq_score_label = Column(String, nullable=False)
    iq_score_note = Column(Text, nullable=False)
    birth_date = Column(String, nullable=True)
    death_date = Column(String, nullable=True)
    birth_place = Column(String, nullable=False)
    zodiac_sign = Column(String, nullable=True)
    profile_image_url = Column(String, nullable=True)
    biography = Column(Text, nullable=False)
    short_description = Column(Text, nullable=False)
    era = Column(String, nullable=False)
    profile_type = Column(String, nullable=False, default="historical")
    is_historical = Column(Boolean, nullable=False, default=True)
    is_fictional = Column(Boolean, nullable=False, default=False)
    source_url = Column(String, nullable=True)
    editorial_note = Column(Text, nullable=False, default="")
    publication_status = Column(String, nullable=False, default="draft")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
