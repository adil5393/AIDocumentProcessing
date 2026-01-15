# app/db/models/uploaded_files.py
from sqlalchemy import (
    Column,
    Integer,
    Text,
    Boolean,
    DateTime,
    CheckConstraint,
    Index,
    text
)
from sqlalchemy.sql import func
from backend.app.db.base import Base

class UploadedFile(Base):
    __tablename__ = "uploaded_files"

    file_id = Column(Integer, primary_key=True)
    file_path = Column(Text, nullable=False)
    doc_type = Column(Text, nullable=False)

    ocr_done = Column(Boolean, server_default=text("false"), nullable=False)
    extraction_done = Column(Boolean, server_default=text("false"), nullable=False)

    created_at = Column(DateTime, server_default=func.now())
    ocr_at = Column(DateTime)
    extracted_at = Column(DateTime)

    ocr_text = Column(Text)
    extracted_raw = Column(Text)  # jsonb later if needed
    display_name = Column(Text)
    extraction_error = Column(Text)
    layover_status = Column(Text)
    unlock = Column(
    Boolean,
    nullable=False,
    server_default=text("false")
)

    __table_args__ = (
        CheckConstraint(
            "extraction_done = false OR ocr_done = true",
            name="extraction_requires_ocr"
        ),
        Index("idx_uploaded_files_display_name", "display_name"),
    )