import json
from typing import Dict, Set

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from sqlmodel import Session

from app import crud
from app.core.security import decode_access_token
from app.core.db import engine
from app.models import ChatMessage, ChatMessagePublic, User, UserPublic

router = APIRouter()


# Хранилище активных WebSocket соединений
class ConnectionManager:
    def __init__(self):
        # chat_id -> set of websockets
        self.active_connections: Dict[int, Set[WebSocket]] = {}
        # user_id -> set of websockets
        self.user_connections: Dict[int, Set[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, chat_id: int, user_id: int):
        await websocket.accept()
        
        if chat_id not in self.active_connections:
            self.active_connections[chat_id] = set()
        self.active_connections[chat_id].add(websocket)
        
        if user_id not in self.user_connections:
            self.user_connections[user_id] = set()
        self.user_connections[user_id].add(websocket)

    def disconnect(self, websocket: WebSocket, chat_id: int, user_id: int):
        if chat_id in self.active_connections:
            self.active_connections[chat_id].discard(websocket)
            if not self.active_connections[chat_id]:
                del self.active_connections[chat_id]
        
        if user_id in self.user_connections:
            self.user_connections[user_id].discard(websocket)
            if not self.user_connections[user_id]:
                del self.user_connections[user_id]

    async def send_personal_message(self, message: dict, websocket: WebSocket):
        await websocket.send_json(message)

    async def broadcast_to_chat(self, message: dict, chat_id: int):
        import logging
        logger = logging.getLogger(__name__)
        if chat_id in self.active_connections:
            logger.info(f"Broadcasting to {len(self.active_connections[chat_id])} connections in chat {chat_id}")
            disconnected = set()
            for connection in self.active_connections[chat_id]:
                try:
                    await connection.send_json(message)
                    logger.info(f"Message sent to connection in chat {chat_id}")
                except Exception as e:
                    logger.error(f"Error sending message to connection: {e}")
                    disconnected.add(connection)
            
            # Удаляем отключенные соединения
            for conn in disconnected:
                self.active_connections[chat_id].discard(conn)
        else:
            logger.warning(f"No active connections for chat {chat_id}")


manager = ConnectionManager()


async def get_user_from_websocket(websocket: WebSocket, token: str) -> User | None:
    """Получить пользователя из токена WebSocket"""
    try:
        payload = decode_access_token(token)
        user_id: int = int(payload.get("sub"))
        if user_id is None:
            return None
        
        with Session(engine) as session:
            user = session.get(User, user_id)
            return user
    except Exception:
        return None


@router.websocket("/ws/{chat_id}")
async def websocket_endpoint(websocket: WebSocket, chat_id: int):
    """WebSocket endpoint для чата"""
    # Получаем токен из query параметров
    token = websocket.query_params.get("token")
    if not token:
        await websocket.close(code=1008, reason="Token required")
        return
    
    user = await get_user_from_websocket(websocket, token)
    if not user:
        await websocket.close(code=1008, reason="Invalid token")
        return
    
    # Проверяем, что пользователь является участником чата
    with Session(engine) as session:
        chat = crud.get_chat(session=session, chat_id=chat_id, user_id=user.id)
        if not chat:
            await websocket.close(code=1008, reason="Chat not found or access denied")
            return
    
    await manager.connect(websocket, chat_id, user.id)
    
    try:
        while True:
            data = await websocket.receive_text()
            message_data = json.loads(data)
            
            if message_data.get("type") == "message":
                # Создаем сообщение
                with Session(engine) as session:
                    try:
                        message = crud.create_message(
                            session=session,
                            chat_id=chat_id,
                            sender_id=user.id,
                            content=message_data.get("content", ""),
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
                        
                        # Отправляем сообщение всем участникам чата
                        # Используем mode='json' для правильной сериализации datetime
                        await manager.broadcast_to_chat(
                            {
                                "type": "new_message",
                                "message": message_public.model_dump(mode='json'),
                            },
                            chat_id,
                        )
                    except Exception as e:
                        await websocket.send_json({
                            "type": "error",
                            "message": str(e),
                        })
            
            elif message_data.get("type") == "typing":
                # Уведомление о печати
                await manager.broadcast_to_chat(
                    {
                        "type": "typing",
                        "user_id": user.id,
                        "user_name": user.full_name or user.email,
                    },
                    chat_id,
                )
    
    except WebSocketDisconnect:
        manager.disconnect(websocket, chat_id, user.id)

