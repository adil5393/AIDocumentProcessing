from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    CheckConstraint,
    Index
)
from sqlalchemy.sql import func, text
from backend.app.db.base import Base


class SRRegistry(Base):
    __tablename__ = "sr_registry"

    # PRIMARY KEY
    id = Column(Integer, primary_key=True)

    # BUSINESS KEY
    sr_number = Column(String(50), nullable=False)

    # CONTEXT
    branch_id = Column(Integer, nullable=False)
    reserved_by = Column(Integer, nullable=False)

    # STATE
    status = Column(String(12), nullable=False)

    # TIMESTAMPS
    reserved_at = Column(
        DateTime,
        server_default=func.now(),
        nullable=False
    )

    expires_at = Column(
        DateTime,
        server_default=text("now() + interval '1 hour'"),
        nullable=False
    )

    confirmed_at = Column(DateTime)

    __table_args__ = (
        # UNIQUE CONSTRAINT (Postgres shows it twice, but one is enough)
        Index("sr_registry_sr_unique", "sr_number", unique=True),

        # STATUS CHECK
        CheckConstraint(
            "status IN ('reserved', 'confirmed')",
            name="sr_registry_status_check"
        ),
    )
