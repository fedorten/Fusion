import logging
import sentry_sdk
from fastapi import FastAPI
from fastapi.routing import APIRoute
from starlette.middleware.cors import CORSMiddleware
from sqlmodel import Session, SQLModel, select

from app import crud
from app.api.main import api_router
from app.core.config import settings
from app.core.db import engine
from app.models import User, UserCreate

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def custom_generate_unique_id(route: APIRoute) -> str:
    return f"{route.tags[0]}-{route.name}"


if settings.SENTRY_DSN and settings.ENVIRONMENT != "local":
    sentry_sdk.init(dsn=str(settings.SENTRY_DSN), enable_tracing=True)

# Создаем таблицы при старте, если их нет
def create_tables():
    """Создает таблицы в БД, если их еще нет"""
    try:
        logger.info("Checking and creating database tables if needed...")
        # SQLModel.create_all безопасно создает только отсутствующие таблицы
        SQLModel.metadata.create_all(engine)
        logger.info("Database tables ready")
    except Exception as e:
        logger.error(f"Error creating tables: {e}")
        # Не падаем, если таблицы уже существуют
        pass

def create_initial_user():
    """Создает начального пользователя, если его нет"""
    try:
        with Session(engine) as session:
            user = session.exec(
                select(User).where(User.email == settings.FIRST_SUPERUSER)
            ).first()
            if not user:
                logger.info("Creating initial superuser...")
                user_in = UserCreate(
                    email=settings.FIRST_SUPERUSER,
                    password=settings.FIRST_SUPERUSER_PASSWORD,
                    is_superuser=True,
                )
                crud.create_user(session=session, user_create=user_in)
                logger.info("Initial superuser created successfully")
            else:
                logger.info("Initial superuser already exists")
    except Exception as e:
        logger.error(f"Error creating initial user: {e}")

# Создаем таблицы и начального пользователя при импорте модуля
create_tables()
create_initial_user()

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    generate_unique_id_function=custom_generate_unique_id,
)

# Set all CORS enabled origins
if settings.all_cors_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.all_cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

app.include_router(api_router, prefix=settings.API_V1_STR)
