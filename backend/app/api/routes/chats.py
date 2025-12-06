from typing import Any

from fastapi import APIRouter, HTTPException
from sqlmodel import select

from app import crud
from app.api.deps import CurrentUser, SessionDep
from app.models import (
    Chat,
    ChatAddMembers,
    ChatCreate,
    ChatMember,
    ChatMemberPublic,
    ChatMessage,
    ChatMessagePublic,
    ChatMessagesPublic,
    ChatPublic,
    ChatsPublic,
    Message,
    User,
    UserPublic,
)

router = APIRouter(prefix="/chats", tags=["chats"])


def _format_chat_public(chat: Chat, current_user_id: int, session: SessionDep) -> ChatPublic:
    """Форматирует чат для API ответа"""
    # Получаем участников
    members_stmt = select(ChatMember).where(ChatMember.chat_id == chat.id)
    members = list(session.exec(members_stmt).all())
    
    # Для приватного чата определяем собеседника
    chat_name = chat.name
    if chat.chat_type == "private" and not chat_name:
        for member in members:
            if member.user_id != current_user_id:
                user = session.get(User, member.user_id)
                if user:
                    chat_name = user.full_name or user.email
    
    # Получаем последнее сообщение
    last_msg_stmt = (
        select(ChatMessage)
        .where(ChatMessage.chat_id == chat.id)
        .order_by(ChatMessage.created_at.desc())
        .limit(1)
    )
    last_message = session.exec(last_msg_stmt).first()
    
    # Форматируем участников
    members_public = []
    for member in members:
        user = session.get(User, member.user_id)
        if user:
            members_public.append(
                ChatMemberPublic(
                    id=member.id,
                    user_id=member.user_id,
                    user=UserPublic.model_validate(user),
                    joined_at=member.joined_at,
                    last_read_at=member.last_read_at,
                )
            )
    
    return ChatPublic(
        id=chat.id,
        chat_type=chat.chat_type,
        name=chat_name,
        created_at=chat.created_at,
        updated_at=chat.updated_at,
        members=members_public,
        last_message=(
            ChatMessagePublic(
                id=last_message.id,
                chat_id=last_message.chat_id,
                sender_id=last_message.sender_id,
                sender=UserPublic.model_validate(session.get(User, last_message.sender_id)) if session.get(User, last_message.sender_id) else None,
                content=last_message.content,
                created_at=last_message.created_at,
                edited_at=last_message.edited_at,
            )
            if last_message
            else None
        ),
    )


@router.get("/", response_model=ChatsPublic)
def get_chats(session: SessionDep, current_user: CurrentUser) -> Any:
    """Получить все чаты текущего пользователя"""
    chats = crud.get_user_chats(session=session, user_id=current_user.id)
    
    chats_public = []
    for chat in chats:
        chats_public.append(_format_chat_public(chat, current_user.id, session))
    
    return ChatsPublic(data=chats_public, count=len(chats_public))


@router.get("/{chat_id}", response_model=ChatPublic)
def get_chat(chat_id: int, session: SessionDep, current_user: CurrentUser) -> Any:
    """Получить конкретный чат"""
    chat = crud.get_chat(session=session, chat_id=chat_id, user_id=current_user.id)
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    
    return _format_chat_public(chat, current_user.id, session)


@router.post("/private/{user_id}", response_model=ChatPublic)
def create_or_get_private_chat(user_id: int, session: SessionDep, current_user: CurrentUser) -> Any:
    """Создать или получить приватный чат с пользователем"""
    if user_id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot create chat with yourself")
    
    # Проверяем, что пользователь существует
    target_user = session.get(User, user_id)
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    chat = crud.get_or_create_private_chat(
        session=session,
        user1_id=current_user.id,
        user2_id=user_id,
    )
    
    return _format_chat_public(chat, current_user.id, session)


@router.post("/group", response_model=ChatPublic)
def create_group_chat(
    chat_in: ChatCreate, session: SessionDep, current_user: CurrentUser
) -> Any:
    """Создать групповой чат"""
    if chat_in.chat_type != "group":
        raise HTTPException(status_code=400, detail="Use /private/{user_id} for private chats")
    
    if not chat_in.name:
        raise HTTPException(status_code=400, detail="Group chat name is required")
    
    if not chat_in.member_ids:
        raise HTTPException(status_code=400, detail="At least one member is required")
    
    # Проверяем, что все пользователи существуют
    for user_id in chat_in.member_ids:
        user = session.get(User, user_id)
        if not user:
            raise HTTPException(status_code=404, detail=f"User {user_id} not found")
    
    chat = crud.create_group_chat(
        session=session,
        creator_id=current_user.id,
        name=chat_in.name,
        member_ids=chat_in.member_ids,
    )
    
    return _format_chat_public(chat, current_user.id, session)


@router.post("/{chat_id}/members", response_model=ChatPublic)
def add_members_to_group(
    chat_id: int,
    members_in: ChatAddMembers,
    session: SessionDep,
    current_user: CurrentUser,
) -> Any:
    """Добавить участников в групповой чат"""
    chat = crud.get_chat(session=session, chat_id=chat_id, user_id=current_user.id)
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    
    if chat.chat_type != "group":
        raise HTTPException(status_code=400, detail="Can only add members to group chats")
    
    # Проверяем, что все пользователи существуют
    for user_id in members_in.member_ids:
        user = session.get(User, user_id)
        if not user:
            raise HTTPException(status_code=404, detail=f"User {user_id} not found")
    
    updated_chat = crud.add_members_to_group_chat(
        session=session,
        chat_id=chat_id,
        member_ids=members_in.member_ids,
        current_user_id=current_user.id,
    )
    
    if not updated_chat:
        raise HTTPException(status_code=403, detail="You don't have permission to add members to this chat")
    
    return _format_chat_public(updated_chat, current_user.id, session)


@router.post("/{chat_id}/read", response_model=Message)
def mark_chat_read(chat_id: int, session: SessionDep, current_user: CurrentUser) -> Any:
    """Отметить чат как прочитанный"""
    chat = crud.get_chat(session=session, chat_id=chat_id, user_id=current_user.id)
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    
    crud.mark_chat_as_read(session=session, chat_id=chat_id, user_id=current_user.id)
    return Message(message="Chat marked as read")


@router.get("/{chat_id}/messages", response_model=ChatMessagesPublic)
def get_messages(
    chat_id: int,
    session: SessionDep,
    current_user: CurrentUser,
    skip: int = 0,
    limit: int = 50,
) -> Any:
    """Получить сообщения чата"""
    chat = crud.get_chat(session=session, chat_id=chat_id, user_id=current_user.id)
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    
    messages = crud.get_chat_messages(
        session=session,
        chat_id=chat_id,
        user_id=current_user.id,
        skip=skip,
        limit=limit,
    )
    
    messages_public = []
    for msg in messages:
        sender = session.get(User, msg.sender_id)
        messages_public.append(
            ChatMessagePublic(
                id=msg.id,
                chat_id=msg.chat_id,
                sender_id=msg.sender_id,
                sender=UserPublic.model_validate(sender) if sender else None,
                content=msg.content,
                created_at=msg.created_at,
                edited_at=msg.edited_at,
            )
        )
    
    return ChatMessagesPublic(data=messages_public, count=len(messages_public))

