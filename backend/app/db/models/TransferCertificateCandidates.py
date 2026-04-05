from sqlalchemy import (
    JSON,
    Column,
    Integer,
    DateTime,
    ForeignKey,
    Index,
    Numeric,
    Text
)
from sqlalchemy.sql import func
from App.Db.Base import Base


class TransferCertificateCandidate(Base):
    __tablename__ = "transfer_certificate_candidates"

    # PRIMARY KEY
    id = Column(Integer, primary_key=True)

    # FKs
    doc_id = Column(
        Integer,
        ForeignKey(
            "transfer_certificates.doc_id",
            ondelete="CASCADE"
        ),
        nullable=False
    )

    sr = Column(
        Text,
        ForeignKey(
            "admission_forms.sr",
            ondelete="CASCADE",
            onupdate="CASCADE"
        ),
        nullable=False
    )

    # SCORING
    total_score = Column(
        Numeric(5, 3),
        nullable=False
    )

    signals = Column(JSON, nullable=False)

    # METADATA
    created_at = Column(
        DateTime,
        server_default=func.now()
    )

    __table_args__ = (
        Index(
            "transfer_certificate_candidates_doc_id_sr_key",
            "doc_id",
            "sr",
            unique=True
        ),
    )
