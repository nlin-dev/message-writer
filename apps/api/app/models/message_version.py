import json
from datetime import datetime, timezone

from sqlalchemy import ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class MessageVersion(Base):
    __tablename__ = "message_versions"
    __table_args__ = (UniqueConstraint("message_id", "version_number"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    message_id: Mapped[int] = mapped_column(ForeignKey("messages.id", ondelete="CASCADE"))
    version_number: Mapped[int] = mapped_column()
    prompt_or_instruction: Mapped[str] = mapped_column(Text)
    message_text: Mapped[str] = mapped_column(Text)
    claims_json: Mapped[str] = mapped_column(Text)
    dropped_claims_json: Mapped[str] = mapped_column(Text)
    source: Mapped[str] = mapped_column(String)
    created_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc))

    @property
    def claims(self) -> list[dict]:
        return json.loads(self.claims_json) if self.claims_json else []

    @property
    def dropped_claims(self) -> list[dict]:
        return json.loads(self.dropped_claims_json) if self.dropped_claims_json else []
