from sqlalchemy import (
    Column,
    Integer,
    DateTime,
    ForeignKey,
    Index,
    Numeric,
    Text
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func
from backend.app.db.base import Base


class BirthCertificateCandidate(Base):
    __tablename__ = "birth_certificate_candidates"

    # PRIMARY KEY
    id = Column(Integer, primary_key=True)

    # FKs
    doc_id = Column(
        Integer,
        ForeignKey(
            "birth_certificates.doc_id",
            ondelete="CASCADE"
        ),
        nullable=False
    )

    sr = Column(
        Text,
        ForeignKey(
            "admission_forms.sr",
            ondelete="CASCADE"
        ),
        nullable=False
    )

    # SCORING
    total_score = Column(
        Numeric(5, 3),
        nullable=False
    )

    signals = Column(JSONB, nullable=False)

    # METADATA
    created_at = Column(
        DateTime,
        server_default=func.now()
    )

    __table_args__ = (
        Index(
            "birth_certificate_candidates_doc_id_sr_key",
            "doc_id",
            "sr",
            unique=True
        ),
    )
