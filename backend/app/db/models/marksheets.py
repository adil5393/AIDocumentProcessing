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


class Marksheet(Base):
    __tablename__ = "marksheets"

    # PRIMARY KEY
    doc_id = Column(Integer, primary_key=True)

    # STUDENT INFO
    student_name = Column(Text)
    father_name = Column(Text)
    mother_name = Column(Text)
    date_of_birth = Column(Date)

    result_status = Column(String(10))

    # LOOKUP / MATCHING
    lookup_status = Column(
        Text,
        server_default="no_match"
    )

    lookup_checked_at = Column(
        DateTime,
        server_default=func.now()
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
        Index("idx_marksheet_name_dob", "student_name", "date_of_birth"),
        Index("idx_marksheet_parents", "father_name", "mother_name"),
        Index("idx_marksheets_file_id", "file_id"),
        Index("idx_marksheets_lookup_checked_at", "lookup_checked_at"),
        Index(
            "uniq_marksheet_content",
            "content_hash",
            unique=True
        ),
    )
