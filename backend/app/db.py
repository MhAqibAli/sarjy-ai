"""SQLAlchemy models + tiny data-access helpers. SQLite in dev, Postgres in prod."""
from datetime import datetime

from sqlalchemy import DateTime, String, Text, UniqueConstraint, create_engine, delete, select
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column

from .config import DATABASE_URL

_connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, connect_args=_connect_args, pool_pre_ping=True)


class Base(DeclarativeBase):
    pass


class Memory(Base):
    __tablename__ = "memories"
    __table_args__ = (UniqueConstraint("user_id", "key", name="uq_user_key"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[str] = mapped_column(String(64), index=True)
    key: Mapped[str] = mapped_column(String(64))
    value: Mapped[str] = mapped_column(Text)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )


class Message(Base):
    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[str] = mapped_column(String(64), index=True)
    role: Mapped[str] = mapped_column(String(16))
    content: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


def init_db() -> None:
    Base.metadata.create_all(engine)


def get_memories(user_id: str) -> dict[str, str]:
    with Session(engine) as s:
        rows = s.scalars(select(Memory).where(Memory.user_id == user_id)).all()
        return {r.key: r.value for r in rows}


def upsert_memories(user_id: str, facts: dict[str, str]) -> None:
    if not facts:
        return
    with Session(engine) as s:
        for key, value in facts.items():
            row = s.scalar(
                select(Memory).where(Memory.user_id == user_id, Memory.key == key)
            )
            if row:
                row.value = value
            else:
                s.add(Memory(user_id=user_id, key=key, value=value))
        s.commit()


def delete_memories(user_id: str) -> None:
    with Session(engine) as s:
        s.execute(delete(Memory).where(Memory.user_id == user_id))
        s.execute(delete(Message).where(Message.user_id == user_id))
        s.commit()


def add_message(user_id: str, role: str, content: str) -> None:
    with Session(engine) as s:
        s.add(Message(user_id=user_id, role=role, content=content))
        s.commit()


def get_recent_messages(user_id: str, limit: int = 8) -> list[dict[str, str]]:
    with Session(engine) as s:
        rows = s.scalars(
            select(Message)
            .where(Message.user_id == user_id)
            .order_by(Message.id.desc())
            .limit(limit)
        ).all()
        return [{"role": r.role, "content": r.content} for r in reversed(rows)]
