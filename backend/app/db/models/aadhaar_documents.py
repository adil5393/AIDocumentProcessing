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


class AadhaarDocument(Base):
    __tablename__ = "aadhaar_documents"

    # PRIMARY KEY
    doc_id = Column(Integer, primary_key=True)

    # CORE DATA
    aadhaar_number = Column(String(12), nullable=False)
    name = Column(Text)
    date_of_birth = Column(Date)

    raw_text = Column(Text)

    # RELATION INFO
    relation_type = Column(String(10))
    related_name = Column(Text)

    # LOOKUP STATE
    lookup_status = Column(
        String(20),
        server_default="pending"
    )
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
        Index("idx_aadhaar_number", "aadhaar_number"),
        Index("idx_aadhaar_name_dob", "name", "date_of_birth"),
        Index("uniq_aadhaar_number", "aadhaar_number", unique=True),
    )
