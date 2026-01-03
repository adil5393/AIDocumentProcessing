from sqlalchemy import (
    Column,
    Integer,
    Text,
    DateTime,
    Float,
    ForeignKey,
    Index,
    CheckConstraint
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func
from backend.app.db.base import Base


class AadhaarLookupCandidate(Base):
    __tablename__ = "aadhaar_lookup_candidates"

    # PRIMARY KEY
    id = Column(Integer, primary_key=True)

    # FKs
    doc_id = Column(
        Integer,
        ForeignKey(
            "aadhaar_documents.doc_id",
            ondelete="CASCADE"
        ),
        nullable=False
    )

    sr = Column(
        Text,
        ForeignKey(
            "admission_forms.sr",
            onupdate="CASCADE",
            ondelete="CASCADE"
        ),
        nullable=False
    )

    # ROLE & SCORE
    role = Column(Text, nullable=False)
    total_score = Column(Float, nullable=False)

    # MATCH DETAILS
    signals = Column(JSONB, nullable=False)
    student_name = Column(Text)

    # METADATA
    created_at = Column(
        DateTime,
        server_default=func.now()
    )

    __table_args__ = (
        # COMPOSITE UNIQUE
        Index(
            "aadhaar_lookup_candidates_doc_id_sr_role_key",
            "doc_id",
            "sr",
            "role",
            unique=True
        ),

        # SEARCH / SORT
        Index("idx_aadhaar_lookup_doc", "doc_id"),
        Index(
            "idx_aadhaar_lookup_score",
            "doc_id",
            Column("total_score").desc()
        ),

        # ROLE CHECK
        CheckConstraint(
            "role IN ('student', 'father', 'mother')",
            name="aadhaar_lookup_candidates_role_check"
        ),
    )
