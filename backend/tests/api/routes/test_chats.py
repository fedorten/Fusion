from fastapi.testclient import TestClient

from app.core.config import settings
from tests.utils.utils import get_superuser_token_headers


def test_create_private_chat(
    client: TestClient, superuser_token_headers: dict[str, str], db
) -> None:
    """Тест создания приватного чата"""
    from app import crud
    from app.models import UserCreate
    from sqlmodel import Session
    
    # Создаем второго пользователя через CRUD
    session: Session = db
    user_create = UserCreate(
        email="testuser@example.com",
        password="testpassword123",
        full_name="Test User",
    )
    user = crud.create_user(session=session, user_create=user_create)
    user_id = user.id

    # Создаем приватный чат
    response = client.post(
        f"{settings.API_V1_STR}/chats/private/{user_id}",
        headers=superuser_token_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["chat_type"] == "private"
    assert data["id"] is not None


def test_get_chats(
    client: TestClient, superuser_token_headers: dict[str, str], db
) -> None:
    """Тест получения списка чатов"""
    response = client.get(
        f"{settings.API_V1_STR}/chats/",
        headers=superuser_token_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert "data" in data
    assert "count" in data
    assert isinstance(data["data"], list)


def test_search_users(
    client: TestClient, superuser_token_headers: dict[str, str], db
) -> None:
    """Тест поиска пользователей"""
    from app import crud
    from app.models import UserCreate
    from sqlmodel import Session
    
    # Создаем тестового пользователя через CRUD
    session: Session = db
    user_create = UserCreate(
        email="searchtest@example.com",
        password="testpassword123",
        full_name="Search Test User",
    )
    crud.create_user(session=session, user_create=user_create)

    # Ищем пользователя
    response = client.get(
        f"{settings.API_V1_STR}/users/search?query=searchtest",
        headers=superuser_token_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert "data" in data
    assert len(data["data"]) > 0
    assert any(user["email"] == "searchtest@example.com" for user in data["data"])


def test_create_and_send_message(
    client: TestClient, superuser_token_headers: dict[str, str], db
) -> None:
    """Тест создания чата и отправки сообщения"""
    from app import crud
    from app.models import UserCreate
    from sqlmodel import Session
    
    # Создаем второго пользователя через CRUD
    session: Session = db
    user_create = UserCreate(
        email="messagetest@example.com",
        password="testpassword123",
        full_name="Message Test User",
    )
    user = crud.create_user(session=session, user_create=user_create)
    user_id = user.id

    # Создаем приватный чат
    response = client.post(
        f"{settings.API_V1_STR}/chats/private/{user_id}",
        headers=superuser_token_headers,
    )
    chat_id = response.json()["id"]

    # Отправляем сообщение
    message_data = {"content": "Hello, this is a test message!"}
    response = client.post(
        f"{settings.API_V1_STR}/messages/{chat_id}",
        headers=superuser_token_headers,
        json=message_data,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["content"] == message_data["content"]
    assert data["chat_id"] == chat_id

    # Получаем сообщения чата
    response = client.get(
        f"{settings.API_V1_STR}/chats/{chat_id}/messages",
        headers=superuser_token_headers,
    )
    assert response.status_code == 200
    messages_data = response.json()
    assert "data" in messages_data
    assert len(messages_data["data"]) > 0
    assert messages_data["data"][0]["content"] == message_data["content"]

