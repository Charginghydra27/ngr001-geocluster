from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, Any

class EventIn(BaseModel):
    occurred_at: datetime
    lat: float
    lon: float
    type: Optional[str] = None
    severity: Optional[int] = None
    properties: dict[str, Any] = Field(default_factory=dict)

class EventOut(EventIn):
    id: int
    class Config:
        from_attributes = True
