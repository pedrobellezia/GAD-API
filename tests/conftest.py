from os import getenv

import pytest
import pytest_asyncio
from alembic import command
from alembic.config import Config
from dotenv import load_dotenv
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession

from app.app import app
from app.core import get_db as original_get_db

load_dotenv()

TEST_DATABASE_URL = getenv("TEST_DATABASE_URL")

if not TEST_DATABASE_URL:
    raise ValueError("TEST_DATABASE_URL não encontrado nas variáveis de ambiente")


@pytest_asyncio.fixture
async def engine():
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    try:
        yield engine
    finally:
        await engine.dispose()


@pytest.fixture(scope="session", autouse=True)
def apply_migrations():
    """Aplica migrations usando conexão síncrona (Alembic é síncrono)"""

    alembic_cfg = Config("alembic.ini")
    alembic_cfg.set_main_option("sqlalchemy.url", TEST_DATABASE_URL)

    command.downgrade(alembic_cfg, "base")
    command.upgrade(alembic_cfg, "head")

    yield

    # Cleanup após todos os testes
    command.downgrade(alembic_cfg, "base")


@pytest_asyncio.fixture
async def db(engine):
    async with engine.connect() as conn:
        trans = await conn.begin()

        session = AsyncSession(bind=conn)

        try:
            yield session
        finally:
            await session.close()
            await trans.rollback()


@pytest_asyncio.fixture
async def client(db):
    async def override():
        yield db

    """Create a test client with overridden database dependency."""
    app.dependency_overrides[original_get_db] = override

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
        headers={"X-API-KEY": getenv("API_KEY")},
    ) as ac:
        yield ac

    app.dependency_overrides.clear()
