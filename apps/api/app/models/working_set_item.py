from datetime import datetime, timezone

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class WorkingSetItem(Base):
    __tablename__ = "working_set_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    reference_id: Mapped[int] = mapped_column(ForeignKey("references.id", ondelete="CASCADE"))
    added_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc))
