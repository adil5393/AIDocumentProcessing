from sqlalchemy import (
    Column,
    Integer,
    Text,
    Date,
    DateTime,
    ForeignKey,
    Index
)
from sqlalchemy.sql import func
from backend.app.db.base import Base


class BirthCertificate(Base):
    __tablename__ = "birth_certificates"

    # PRIMARY KEY
    doc_id = Column(Integer, primary_key=True)

    # STUDENT INFO
    student_name = Column(Text)
    father_name = Column(Text)
    mother_name = Column(Text)
    date_of_birth = Column(Date)
    place_of_birth = Column(Text)

    # LOOKUP / MATCHING
    lookup_status = Column(
        Text,
        server_default="no_match"
    )

    last_checked_at = Column(
        DateTime,
        server_default=func.now()
    )

    content_hash = Column(Text)

    # FK → uploaded_files (NOT NULL)
    file_id = Column(
        Integer,
        ForeignKey("uploaded_files.file_id", ondelete="CASCADE"),
        nullable=False
    )

    __table_args__ = (
        Index("idx_birth_certificates_file_id", "file_id"),
        Index("idx_birth_certificates_lookup_status", "lookup_status"),
        Index("idx_birthcert_name_dob", "student_name", "date_of_birth"),
        Index("idx_birthcert_parents", "father_name", "mother_name"),
        Index(
            "uniq_birth_certificate_content",
            "content_hash",
            unique=True
        ),
    )
