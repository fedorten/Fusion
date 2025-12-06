from sqlmodel import Session, create_engine, select
from sqlalchemy import event
from sqlalchemy.dialects.sqlite import BLOB

from app import crud
from app.core.config import settings
from app.models import (
    Chat,
    ChatMember,
    ChatMessage,
    User,
    UserCreate,
)  # Импортируем все модели для регистрации в метаданных

# SQLite требует connect_args для работы в многопоточном режиме
connect_args = {}
if settings.SQLALCHEMY_DATABASE_URI.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_engine(
    str(settings.SQLALCHEMY_DATABASE_URI),
    connect_args=connect_args,
    echo=False,
)

# Настройка для работы с UUID в SQLite
if settings.SQLALCHEMY_DATABASE_URI.startswith("sqlite"):

    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_conn, connection_record):
        cursor = dbapi_conn.cursor()
        # Включаем поддержку внешних ключей
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


# make sure all SQLModel models are imported (app.models) before initializing DB
# otherwise, SQLModel might fail to initialize relationships properly
# for more details: https://github.com/fastapi/full-stack-fastapi-template/issues/28


def init_db(session: Session) -> None:
    # Tables should be created with Alembic migrations
    # But if you don't want to use migrations, create
    # the tables un-commenting the next lines
    from sqlmodel import SQLModel

    # This works because the models are already imported and registered from app.models
    # Создаем таблицы для тестов (в продакшене используются миграции Alembic)
    SQLModel.metadata.create_all(engine)

    user = session.exec(
        select(User).where(User.email == settings.FIRST_SUPERUSER)
    ).first()
    if not user:
        user_in = UserCreate(
            email=settings.FIRST_SUPERUSER,
            password=settings.FIRST_SUPERUSER_PASSWORD,
            is_superuser=True,
        )
        user = crud.create_user(session=session, user_create=user_in)
