from sqlalchemy import (
    Column,
    Integer,
    Text,
    Date,
    DateTime,
    String,
    ForeignKey,
    Index
)
from sqlalchemy.sql import func
from backend.app.db.base import Base


class AdmissionForm(Base):
    __tablename__ = "admission_forms"

    # PRIMARY KEY
    sr = Column(String(20), primary_key=True)

    # STUDENT INFO
    student_name = Column(Text, nullable=False)
    gender = Column(String(10))
    date_of_birth = Column(Date)

    # PARENTS
    father_name = Column(Text)
    mother_name = Column(Text)
    father_occupation = Column(Text)
    mother_occupation = Column(Text)

    father_aadhaar = Column(String(12))
    mother_aadhaar = Column(String(12))
    student_aadhaar_number = Column(String(12))

    # CONTACT
    phone1 = Column(String(20))
    phone2 = Column(String(20))
    address = Column(Text)

    # ACADEMIC
    class_name = Column("class", String(10))  # class is reserved in Python
    last_school_attended = Column(Text)

    spen = Column(String(11))

    # METADATA
    created_at = Column(DateTime, server_default=func.now())

    # FK → uploaded_files
    file_id = Column(
        Integer,
        ForeignKey("uploaded_files.file_id", ondelete="CASCADE"),
        nullable=False
    )

    __table_args__ = (
        Index("admission_forms_sr_unique", "sr", unique=True),
        Index("idx_admission_name_dob", "student_name", "date_of_birth"),
        Index("idx_admission_parents", "father_name", "mother_name"),
        Index("idx_adm_student_aadhaar", "student_aadhaar_number"),
        Index("idx_adm_father_aadhaar", "father_aadhaar"),
        Index("idx_adm_mother_aadhaar", "mother_aadhaar"),
    )
