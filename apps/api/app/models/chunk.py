from datetime import datetime, timezone

from sqlalchemy import ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Chunk(Base):
    __tablename__ = "chunks"

    id: Mapped[int] = mapped_column(primary_key=True)
    reference_id: Mapped[int] = mapped_column(ForeignKey("references.id", ondelete="CASCADE"))
    content: Mapped[str] = mapped_column(Text)
    chunk_index: Mapped[int] = mapped_column()
    created_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc))
