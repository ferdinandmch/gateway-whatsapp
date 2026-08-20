import os

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.models import Base


def get_test_database_url() -> str | None:
    return os.environ.get("TEST_DATABASE_URL")


@pytest_asyncio.fixture
async def db_session() -> AsyncSession:
    url = get_test_database_url()
    if not url:
        pytest.skip("TEST_DATABASE_URL not set — skipping integration tests")

    engine = create_async_engine(url, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all, checkfirst=True)

    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with factory() as session:
        yield session
        await session.rollback()

    await engine.dispose()
