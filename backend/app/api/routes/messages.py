import asyncio
import logging
from typing import Any

from fastapi import APIRouter, HTTPException

from app import crud
from app.api.deps import CurrentUser, SessionDep
from app.api.routes.websocket import manager
from app.models import (
    ChatMessage,
    ChatMessageCreate,
    ChatMessagePublic,
    ChatMessageUpdate,
    Message,
    User,
    UserPublic,
)

router = APIRouter(prefix="/messages", tags=["messages"])
logger = logging.getLogger(__name__)


async def broadcast_message_to_chat(message_public: ChatMessagePublic, chat_id: int):
    """Транслировать сообщение всем участникам чата через WebSocket"""
    # Используем mode='json' для правильной сериализации datetime
    message_dict = message_public.model_dump(mode='json')
    logger.info(f"Broadcasting message {message_dict.get('id')} to chat {chat_id}")
    try:
        await manager.broadcast_to_chat(
            {
                "type": "new_message",
                "message": message_dict,
            },
            chat_id,
        )
        logger.info(f"Message broadcasted successfully")
    except Exception as e:
        logger.error(f"Error broadcasting message: {e}")


@router.post("/{chat_id}", response_model=ChatMessagePublic)
async def create_message(
    chat_id: int,
    message_in: ChatMessageCreate,
    session: SessionDep,
    current_user: CurrentUser,
) -> Any:
    """Создать сообщение в чате"""
    # Проверяем, что пользователь является участником чата
    chat = crud.get_chat(session=session, chat_id=chat_id, user_id=current_user.id)
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    
    try:
        message = crud.create_message(
            session=session,
            chat_id=chat_id,
            sender_id=current_user.id,
            content=message_in.content,
        )
        
        sender = session.get(User, message.sender_id)
        message_public = ChatMessagePublic(
            id=message.id,
            chat_id=message.chat_id,
            sender_id=message.sender_id,
            sender=UserPublic.model_validate(sender) if sender else None,
            content=message.content,
            created_at=message.created_at,
            edited_at=message.edited_at,
        )
        
        # Транслируем сообщение всем участникам чата через WebSocket (не ждем завершения)
        asyncio.create_task(broadcast_message_to_chat(message_public, chat_id))
        
        return message_public
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/{message_id}", response_model=ChatMessagePublic)
def update_message(
    message_id: int,
    message_in: ChatMessageUpdate,
    session: SessionDep,
    current_user: CurrentUser,
) -> Any:
    """Обновить сообщение"""
    message = crud.update_message(
        session=session,
        message_id=message_id,
        sender_id=current_user.id,
        content=message_in.content,
    )
    
    if not message:
        raise HTTPException(status_code=404, detail="Message not found or you don't have permission")
    
    sender = session.get(User, message.sender_id)
    return ChatMessagePublic(
        id=message.id,
        chat_id=message.chat_id,
        sender_id=message.sender_id,
        sender=UserPublic.model_validate(sender) if sender else None,
        content=message.content,
        created_at=message.created_at,
        edited_at=message.edited_at,
    )


@router.delete("/{message_id}", response_model=Message)
def delete_message(
    message_id: int, session: SessionDep, current_user: CurrentUser
) -> Any:
    """Удалить сообщение"""
    success = crud.delete_message(
        session=session, message_id=message_id, user_id=current_user.id
    )
    
    if not success:
        raise HTTPException(status_code=404, detail="Message not found or you don't have permission")
    
    return Message(message="Message deleted successfully")

