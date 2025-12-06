from datetime import datetime, timezone
from typing import Literal

from pydantic import EmailStr
from sqlmodel import Column, DateTime, Field, Integer, Relationship, SQLModel, func


# Shared properties
class UserBase(SQLModel):
    email: EmailStr = Field(unique=True, index=True, max_length=255)
    is_active: bool = True
    is_superuser: bool = False
    full_name: str | None = Field(default=None, max_length=255)


# Properties to receive via API on creation
class UserCreate(UserBase):
    password: str = Field(min_length=8, max_length=128)


class UserRegister(SQLModel):
    email: EmailStr = Field(max_length=255)
    password: str = Field(min_length=8, max_length=128)
    full_name: str | None = Field(default=None, max_length=255)


# Properties to receive via API on update, all are optional
class UserUpdate(UserBase):
    email: EmailStr | None = Field(default=None, max_length=255)  # type: ignore
    password: str | None = Field(default=None, min_length=8, max_length=128)


class UserUpdateMe(SQLModel):
    full_name: str | None = Field(default=None, max_length=255)
    email: EmailStr | None = Field(default=None, max_length=255)


class UpdatePassword(SQLModel):
    current_password: str = Field(min_length=8, max_length=128)
    new_password: str = Field(min_length=8, max_length=128)


# Database model, database table inferred from class name
class User(UserBase, table=True):
    id: int | None = Field(
        default=None, sa_column=Column(Integer, primary_key=True, autoincrement=True)
    )
    hashed_password: str
    chat_members: list["ChatMember"] = Relationship(
        back_populates="user", cascade_delete=True
    )


# Properties to return via API, id is always required
class UserPublic(UserBase):
    id: int


class UsersPublic(SQLModel):
    data: list[UserPublic]
    count: int


# Generic message
class Message(SQLModel):
    message: str


# JSON payload containing access token
class Token(SQLModel):
    access_token: str
    token_type: str = "bearer"


# Contents of JWT token
class TokenPayload(SQLModel):
    sub: str | None = None


class NewPassword(SQLModel):
    token: str
    new_password: str = Field(min_length=8, max_length=128)


# ========== МОДЕЛИ МЕССЕНДЖЕРА FUSION ==========


# Модель чата (личный или групповой)
class Chat(SQLModel, table=True):
    id: int | None = Field(
        default=None, sa_column=Column(Integer, primary_key=True, autoincrement=True)
    )
    chat_type: str = Field(default="private", max_length=20)  # "private" или "group"
    name: str | None = Field(
        default=None, max_length=255
    )  # Название для групповых чатов
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime, default=func.now()),
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime, default=func.now(), onupdate=func.now()),
    )

    # Связи
    members: list["ChatMember"] = Relationship(
        back_populates="chat", cascade_delete=True
    )
    messages: list["ChatMessage"] = Relationship(
        back_populates="chat", cascade_delete=True
    )


# Участники чата
class ChatMember(SQLModel, table=True):
    id: int | None = Field(
        default=None, sa_column=Column(Integer, primary_key=True, autoincrement=True)
    )
    chat_id: int = Field(foreign_key="chat.id", nullable=False, ondelete="CASCADE")
    user_id: int = Field(foreign_key="user.id", nullable=False, ondelete="CASCADE")
    joined_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime, default=func.now()),
    )
    last_read_at: datetime | None = Field(
        default=None, sa_column=Column(DateTime, nullable=True)
    )

    # Связи
    chat: Chat = Relationship(back_populates="members")
    user: User = Relationship(back_populates="chat_members")


# Сообщения в чате
class ChatMessage(SQLModel, table=True):
    id: int | None = Field(
        default=None, sa_column=Column(Integer, primary_key=True, autoincrement=True)
    )
    chat_id: int = Field(foreign_key="chat.id", nullable=False, ondelete="CASCADE")
    sender_id: int = Field(foreign_key="user.id", nullable=False, ondelete="CASCADE")
    content: str = Field(max_length=4096)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime, default=func.now()),
    )
    edited_at: datetime | None = Field(
        default=None, sa_column=Column(DateTime, nullable=True)
    )

    # Связи
    chat: Chat = Relationship(back_populates="messages")
    sender: User = Relationship()


# API модели для чатов
class ChatCreate(SQLModel):
    chat_type: str = "private"  # "private" или "group"
    name: str | None = None
    member_ids: list[int] = Field(default_factory=list)


class ChatPublic(SQLModel):
    id: int
    chat_type: str
    name: str | None
    created_at: datetime
    updated_at: datetime
    members: list["ChatMemberPublic"] = Field(default_factory=list)
    last_message: "ChatMessagePublic | None" = None


class ChatMemberPublic(SQLModel):
    id: int
    user_id: int
    user: UserPublic
    joined_at: datetime
    last_read_at: datetime | None


class ChatAddMembers(SQLModel):
    member_ids: list[int] = Field(min_length=1)


class ChatMessageCreate(SQLModel):
    content: str = Field(min_length=1, max_length=4096)


class ChatMessagePublic(SQLModel):
    id: int
    chat_id: int
    sender_id: int
    sender: UserPublic | None = None
    content: str
    created_at: datetime
    edited_at: datetime | None = None


class ChatMessageUpdate(SQLModel):
    content: str = Field(min_length=1, max_length=4096)


class ChatsPublic(SQLModel):
    data: list[ChatPublic]
    count: int


class ChatMessagesPublic(SQLModel):
    data: list[ChatMessagePublic]
    count: int


class UserSearch(SQLModel):
    query: str = Field(min_length=1, max_length=100)
