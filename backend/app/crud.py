from typing import Any

from sqlmodel import Session, func, or_, select

from app.core.security import get_password_hash, verify_password
from app.models import (
    Chat,
    ChatCreate,
    ChatMember,
    ChatMessage,
    ChatMessageCreate,
    User,
    UserCreate,
    UserUpdate,
)


def create_user(*, session: Session, user_create: UserCreate) -> User:
    db_obj = User.model_validate(
        user_create, update={"hashed_password": get_password_hash(user_create.password)}
    )
    session.add(db_obj)
    session.commit()
    session.refresh(db_obj)
    return db_obj


def update_user(*, session: Session, db_user: User, user_in: UserUpdate) -> Any:
    user_data = user_in.model_dump(exclude_unset=True)
    extra_data = {}
    if "password" in user_data:
        password = user_data["password"]
        hashed_password = get_password_hash(password)
        extra_data["hashed_password"] = hashed_password
    db_user.sqlmodel_update(user_data, update=extra_data)
    session.add(db_user)
    session.commit()
    session.refresh(db_user)
    return db_user


def get_user_by_email(*, session: Session, email: str) -> User | None:
    statement = select(User).where(User.email == email)
    session_user = session.exec(statement).first()
    return session_user


def authenticate(*, session: Session, email: str, password: str) -> User | None:
    db_user = get_user_by_email(session=session, email=email)
    if not db_user:
        return None
    if not verify_password(password, db_user.hashed_password):
        return None
    return db_user


# ========== CRUD ОПЕРАЦИИ ДЛЯ МЕССЕНДЖЕРА ==========

def search_users(*, session: Session, query: str, current_user_id: int, limit: int = 20) -> list[User]:
    """Поиск пользователей по email или имени"""
    search_term = f"%{query.lower()}%"
    statement = (
        select(User)
        .where(
            or_(
                User.email.ilike(search_term),
                User.full_name.ilike(search_term)
            )
        )
        .where(User.id != current_user_id)
        .where(User.is_active == True)
        .limit(limit)
    )
    return list(session.exec(statement).all())


def get_or_create_private_chat(*, session: Session, user1_id: int, user2_id: int) -> Chat:
    """Получить или создать приватный чат между двумя пользователями"""
    # Проверяем, существует ли уже приватный чат между этими пользователями
    statement = (
        select(Chat)
        .join(ChatMember, Chat.id == ChatMember.chat_id)
        .where(Chat.chat_type == "private")
        .where(ChatMember.user_id.in_([user1_id, user2_id]))
        .group_by(Chat.id)
        .having(func.count(ChatMember.user_id) == 2)
    )
    existing_chat = session.exec(statement).first()
    
    if existing_chat:
        return existing_chat
    
    # Создаем новый приватный чат
    new_chat = Chat(chat_type="private")
    session.add(new_chat)
    session.flush()
    
    # Добавляем обоих пользователей в чат
    member1 = ChatMember(chat_id=new_chat.id, user_id=user1_id)
    member2 = ChatMember(chat_id=new_chat.id, user_id=user2_id)
    session.add(member1)
    session.add(member2)
    session.commit()
    session.refresh(new_chat)
    return new_chat


def create_group_chat(*, session: Session, creator_id: int, name: str, member_ids: list[int]) -> Chat:
    """Создать групповой чат"""
    # Добавляем создателя в список участников
    all_member_ids = [creator_id] + [mid for mid in member_ids if mid != creator_id]
    
    new_chat = Chat(chat_type="group", name=name)
    session.add(new_chat)
    session.flush()
    
    # Добавляем всех участников
    for user_id in all_member_ids:
        member = ChatMember(chat_id=new_chat.id, user_id=user_id)
        session.add(member)
    
    session.commit()
    session.refresh(new_chat)
    return new_chat


def get_user_chats(*, session: Session, user_id: int) -> list[Chat]:
    """Получить все чаты пользователя"""
    statement = (
        select(Chat)
        .join(ChatMember, Chat.id == ChatMember.chat_id)
        .where(ChatMember.user_id == user_id)
        .order_by(Chat.updated_at.desc())
    )
    return list(session.exec(statement).all())


def get_chat(*, session: Session, chat_id: int, user_id: int) -> Chat | None:
    """Получить чат, если пользователь является его участником"""
    statement = (
        select(Chat)
        .join(ChatMember, Chat.id == ChatMember.chat_id)
        .where(Chat.id == chat_id)
        .where(ChatMember.user_id == user_id)
    )
    return session.exec(statement).first()


def create_message(*, session: Session, chat_id: int, sender_id: int, content: str) -> ChatMessage:
    """Создать сообщение в чате"""
    # Проверяем, что отправитель является участником чата
    member = session.exec(
        select(ChatMember).where(
            ChatMember.chat_id == chat_id,
            ChatMember.user_id == sender_id
        )
    ).first()
    
    if not member:
        raise ValueError("User is not a member of this chat")
    
    message = ChatMessage(chat_id=chat_id, sender_id=sender_id, content=content)
    session.add(message)
    
    # Обновляем время последнего обновления чата
    chat = session.get(Chat, chat_id)
    if chat:
        from datetime import datetime, timezone
        chat.updated_at = datetime.now(timezone.utc)
    
    session.commit()
    session.refresh(message)
    return message


def get_chat_messages(*, session: Session, chat_id: int, user_id: int, skip: int = 0, limit: int = 50) -> list[ChatMessage]:
    """Получить сообщения чата"""
    # Проверяем, что пользователь является участником
    member = session.exec(
        select(ChatMember).where(
            ChatMember.chat_id == chat_id,
            ChatMember.user_id == user_id
        )
    ).first()
    
    if not member:
        return []
    
    statement = (
        select(ChatMessage)
        .where(ChatMessage.chat_id == chat_id)
        .order_by(ChatMessage.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    messages = list(session.exec(statement).all())
    return list(reversed(messages))  # Возвращаем в хронологическом порядке


def update_message(*, session: Session, message_id: int, sender_id: int, content: str) -> ChatMessage | None:
    """Обновить сообщение"""
    message = session.get(ChatMessage, message_id)
    if not message or message.sender_id != sender_id:
        return None
    
    message.content = content
    from datetime import datetime, timezone
    message.edited_at = datetime.now(timezone.utc)
    session.add(message)
    session.commit()
    session.refresh(message)
    return message


def delete_message(*, session: Session, message_id: int, user_id: int) -> bool:
    """Удалить сообщение"""
    message = session.get(ChatMessage, message_id)
    if not message or message.sender_id != user_id:
        return False
    
    session.delete(message)
    session.commit()
    return True


def add_members_to_group_chat(*, session: Session, chat_id: int, member_ids: list[int], current_user_id: int) -> Chat | None:
    """Добавить участников в групповой чат"""
    # Проверяем, что чат существует и является групповым
    chat = session.get(Chat, chat_id)
    if not chat or chat.chat_type != "group":
        return None
    
    # Проверяем, что текущий пользователь является участником чата
    current_member = session.exec(
        select(ChatMember).where(
            ChatMember.chat_id == chat_id,
            ChatMember.user_id == current_user_id
        )
    ).first()
    
    if not current_member:
        return None
    
    # Получаем существующих участников
    existing_members = session.exec(
        select(ChatMember).where(ChatMember.chat_id == chat_id)
    ).all()
    existing_user_ids = {m.user_id for m in existing_members}
    
    # Добавляем новых участников
    added_count = 0
    for user_id in member_ids:
        if user_id not in existing_user_ids:
            # Проверяем, что пользователь существует
            user = session.get(User, user_id)
            if user:
                member = ChatMember(chat_id=chat_id, user_id=user_id)
                session.add(member)
                added_count += 1
    
    if added_count > 0:
        session.commit()
        session.refresh(chat)
    
    return chat


def mark_chat_as_read(*, session: Session, chat_id: int, user_id: int) -> None:
    """Отметить чат как прочитанный"""
    from datetime import datetime, timezone
    member = session.exec(
        select(ChatMember).where(
            ChatMember.chat_id == chat_id,
            ChatMember.user_id == user_id
        )
    ).first()
    
    if member:
        member.last_read_at = datetime.now(timezone.utc)
        session.add(member)
        session.commit()
