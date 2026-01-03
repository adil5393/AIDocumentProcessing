from sqlalchemy import (
    Column,
    Integer,
    Text,
    String,
    Date,
    DateTime,
    ForeignKey,
    Index
)
from sqlalchemy.sql import func
from backend.app.db.base import Base


class TransferCertificate(Base):
    __tablename__ = "transfer_certificates"

    # PRIMARY KEY
    doc_id = Column(Integer, primary_key=True)

    # STUDENT INFO
    student_name = Column(Text)
    father_name = Column(Text)
    mother_name = Column(Text)
    date_of_birth = Column(Date)

    last_class_studied = Column(String(10))
    last_school_name = Column(Text)

    # LOOKUP / DEDUP
    content_hash = Column(Text)

    lookup_status = Column(Text)
    lookup_checked_at = Column(DateTime)

    # METADATA
    created_at = Column(
        DateTime,
        server_default=func.now()
    )

    # FK → uploaded_files
    file_id = Column(
        Integer,
        ForeignKey("uploaded_files.file_id", ondelete="CASCADE")
    )

    __table_args__ = (
        Index(
            "transfer_certificates_content_hash_unique",
            "content_hash",
            unique=True
        ),
    )
