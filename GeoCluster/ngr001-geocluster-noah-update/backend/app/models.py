from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Integer, String, DateTime, JSON, Float
from datetime import datetime  # Python type (IMPORTANT)

class Base(DeclarativeBase):
    pass

class Event(Base):
    __tablename__ = "events"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    occurred_at: Mapped[datetime] = mapped_column(DateTime)  # use Python datetime here
    lat: Mapped[float] = mapped_column(Float)
    lon: Mapped[float] = mapped_column(Float)
    type: Mapped[str | None] = mapped_column(String, nullable=True)
    severity: Mapped[int | None] = mapped_column(Integer, nullable=True)
    properties: Mapped[dict] = mapped_column(JSON, default=dict)
