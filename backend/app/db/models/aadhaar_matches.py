from sqlalchemy import (
    Column,
    Integer,
    Text,
    String,
    Boolean,
    DateTime,
    ForeignKey,
    Index
)
from sqlalchemy.sql import func
from backend.app.db.base import Base


class AadhaarMatch(Base):
    __tablename__ = "aadhaar_matches"

    # PRIMARY KEY
    match_id = Column(Integer, primary_key=True)

    # REFERENCES
    sr_number = Column(
        Text,
        ForeignKey(
            "admission_forms.sr",
            onupdate="CASCADE",
            ondelete="CASCADE"
        ),
        nullable=False
    )

    aadhaar_doc_id = Column(
        Integer,
        ForeignKey(
            "aadhaar_documents.doc_id",
            ondelete="CASCADE"
        ),
        nullable=False
    )

    # MATCH DETAILS
    match_role = Column(String, nullable=False)
    match_score = Column(Integer, nullable=False)
    match_method = Column(String, nullable=False)

    role_confidence = Column(Integer)

    # CONFIRMATION WORKFLOW
    is_confirmed = Column(
        Boolean,
        server_default="false"
    )

    confirmed_by = Column(String)
    confirmed_on = Column(DateTime)

    notes = Column(Text)

    # METADATA
    matched_on = Column(
        DateTime,
        server_default=func.now()
    )

    __table_args__ = (
        Index(
            "aadhaar_matches_sr_number_aadhaar_doc_id_key",
            "sr_number",
            "aadhaar_doc_id",
            unique=True
        ),
    )
