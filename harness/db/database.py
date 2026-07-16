"""Database connection and session management."""
import os
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase

DATABASE_URL = os.environ.get("DATABASE_URL", "")

_engine = None
_session_factory = None


class Base(DeclarativeBase):
    pass


def _get_engine():
    global _engine
    if _engine is None and DATABASE_URL:
        _engine = create_async_engine(DATABASE_URL, echo=False, pool_size=20)
    return _engine


async def get_db():
    """FastAPI dependency: yields an async database session."""
    global _session_factory
    engine = _get_engine()
    if engine is None:
        raise RuntimeError("DATABASE_URL not configured")
    if _session_factory is None:
        _session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with _session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def init_db():
    """Create all tables (called at startup)."""
    engine = _get_engine()
    if engine is None:
        return
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
