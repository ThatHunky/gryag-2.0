"""Database models for Gryag bot."""

from datetime import datetime
from typing import Optional

from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, Index, String, Text, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """Base class for all models."""
    pass


class Chat(Base):
    """Telegram chat metadata and settings."""
    
    __tablename__ = "chats"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)  # Telegram chat ID
    title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    chat_type: Mapped[str] = mapped_column(String(20))  # private, group, supergroup, channel
    member_count: Mapped[int | None] = mapped_column(nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    messages: Mapped[list["Message"]] = relationship(back_populates="chat", cascade="all, delete-orphan")
    summaries: Mapped[list["Summary"]] = relationship(back_populates="chat", cascade="all, delete-orphan")


class User(Base):
    """Telegram user info and settings."""
    
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)  # Telegram user ID
    username: Mapped[str | None] = mapped_column(String(255), nullable=True)
    full_name: Mapped[str] = mapped_column(String(255))
    pronouns: Mapped[str | None] = mapped_column(String(50), nullable=True)
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    messages: Mapped[list["Message"]] = relationship(back_populates="user")
    memories: Mapped[list["UserMemory"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    restrictions: Mapped[list["UserRestriction"]] = relationship(back_populates="user", cascade="all, delete-orphan")


class Message(Base):
    """Stored messages for context."""
    
    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    telegram_message_id: Mapped[int] = mapped_column(BigInteger)
    chat_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("chats.id", ondelete="CASCADE"))
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    content: Mapped[str] = mapped_column(Text)
    content_type: Mapped[str] = mapped_column(String(50), default="text")  # text, photo, voice, etc.
    reply_to_message_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    is_bot_message: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    # Relationships
    chat: Mapped["Chat"] = relationship(back_populates="messages")
    user: Mapped[Optional["User"]] = relationship(back_populates="messages")

    __table_args__ = (
        Index("ix_messages_chat_created", "chat_id", "created_at"),
        Index("ix_messages_chat_telegram_id", "chat_id", "telegram_message_id"),
    )


class Summary(Base):
    """Generated context summaries."""
    
    __tablename__ = "summaries"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    chat_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("chats.id", ondelete="CASCADE"))
    summary_type: Mapped[str] = mapped_column(String(20))  # 7day, 30day
    content: Mapped[str] = mapped_column(Text)
    token_count: Mapped[int] = mapped_column()
    period_start: Mapped[datetime] = mapped_column(DateTime)
    period_end: Mapped[datetime] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    # Relationships
    chat: Mapped["Chat"] = relationship(back_populates="summaries")

    __table_args__ = (
        Index("ix_summaries_chat_type", "chat_id", "summary_type"),
    )


class AccessList(Base):
    """Whitelist/blacklist entries."""
    
    __tablename__ = "access_list"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    entity_id: Mapped[int] = mapped_column(BigInteger)  # User or chat ID
    entity_type: Mapped[str] = mapped_column(String(20))  # user, chat
    list_type: Mapped[str] = mapped_column(String(20))  # whitelist, blacklist
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by: Mapped[int | None] = mapped_column(BigInteger, nullable=True)  # Admin who added
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    __table_args__ = (
        Index("ix_access_entity_type", "entity_id", "entity_type", "list_type", unique=True),
    )


class UserMemory(Base):
    """Persistent facts about users (global, max 50 per user)."""
    
    __tablename__ = "user_memories"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"))
    fact: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    # Relationships
    user: Mapped["User"] = relationship(back_populates="memories")

    __table_args__ = (
        Index("ix_memories_user", "user_id"),
    )


class UserRestriction(Base):
    """Bot-level bans/restrictions (admin controlled)."""
    
    __tablename__ = "user_restrictions"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"))
    restriction_type: Mapped[str] = mapped_column(String(20))  # ban, restrict
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)  # None = permanent
    created_by: Mapped[int] = mapped_column(BigInteger)  # Admin who created
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Relationships
    user: Mapped["User"] = relationship(back_populates="restrictions")

    __table_args__ = (
        Index("ix_restrictions_user_active", "user_id", "is_active"),
    )


class RateLimit(Base):
    """Rate limiting tracking for non-admins."""
    
    __tablename__ = "rate_limits"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, index=True)
    window_start: Mapped[datetime] = mapped_column(DateTime)
    request_count: Mapped[int] = mapped_column(default=0)

    __table_args__ = (
        Index("ix_rate_limits_user_window", "user_id", "window_start"),
    )
