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


class BirthCertificateMatch(Base):
    __tablename__ = "birth_certificate_matches"

    # PRIMARY KEY
    id = Column(Integer, primary_key=True)

    # REFERENCES
    sr_number = Column(Text, nullable=False)

    bc_doc_id = Column(
        Integer,
        ForeignKey(
            "birth_certificates.doc_id",
            ondelete="CASCADE"
        ),
        nullable=False
    )

    # NOTE: intentionally no FK (matches DB)
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
            "uniq_bc_match",
            "bc_doc_id",
            unique=True
        ),
    )
