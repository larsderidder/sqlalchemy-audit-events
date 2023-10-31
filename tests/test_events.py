import pytest
from sqlalchemy import Column, DateTime, Integer
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from sqlalchemy_audit_events import AccountabilityMixin, CreatedAndUpdatedMixin, register_session_events


class Base(DeclarativeBase):
    pass


class Item(AccountabilityMixin, CreatedAndUpdatedMixin, Base):
    __tablename__ = "items"

    id = Column(Integer, primary_key=True)
    updated_by_user_id = Column(Integer, nullable=True)
    updated_by_service_id = Column(Integer, nullable=True)
    was_last_updated_on = Column(DateTime, nullable=True)


@pytest.mark.asyncio
async def test_register_session_events_updates_fields():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async_session = async_sessionmaker(engine, expire_on_commit=False)
    async with async_session() as session:
        register_session_events(session)
        session.info["session_info"].user_id = 42
        session.info["session_info"].service_user_id = 99

        item = Item()
        session.add(item)
        await session.flush()

        assert item.updated_by_user_id == 42
        assert item.updated_by_service_id == 99
        assert item.was_last_updated_on is not None
