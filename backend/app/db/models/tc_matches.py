from sqlalchemy import (
    Column,
    Integer,
    Text,
    Boolean,
    DateTime,
    ForeignKey,
    Index
)
from sqlalchemy.sql import func
from backend.app.db.base import Base


class TCMatch(Base):
    __tablename__ = "tc_matches"

    # PRIMARY KEY
    id = Column(Integer, primary_key=True)

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

    tc_doc_id = Column(
        Integer,
        ForeignKey(
            "transfer_certificates.doc_id",
            ondelete="CASCADE"
        ),
        nullable=False
    )

    # NOTE: file_id intentionally has NO FK in DB
    file_id = Column(Integer, nullable=False)

    # MATCH DETAILS
    match_score = Column(Integer)
    match_method = Column(Text)

    # CONFIRMATION
    is_confirmed = Column(
        Boolean,
        server_default="true"
    )

    confirmed_on = Column(
        DateTime,
        server_default=func.now()
    )

    __table_args__ = (
        Index(
            "uniq_tc_match",
            "tc_doc_id",
            unique=True
        ),
    )
