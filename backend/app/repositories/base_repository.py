from typing import Any, Generic, List, Optional, Sequence, Type, TypeVar
import uuid
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.base import Base

ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    """Generic asynchronous repository providing fundamental CRUD operations."""

    def __init__(self, model: Type[ModelType], session: AsyncSession) -> None:
        self.model = model
        self.session = session

    async def get_by_id(self, id_: uuid.UUID) -> Optional[ModelType]:
        return await self.session.get(self.model, id_)

    async def list_all(self, skip: int = 0, limit: int = 100) -> Sequence[ModelType]:
        stmt = select(self.model).offset(skip).limit(limit)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def count(self) -> int:
        stmt = select(func.count()).select_from(self.model)
        result = await self.session.execute(stmt)
        return result.scalar_one()

    def add(self, entity: ModelType) -> ModelType:
        self.session.add(entity)
        return entity

    async def delete(self, entity: ModelType) -> None:
        await self.session.delete(entity)

    async def commit(self) -> None:
        await self.session.commit()

    async def rollback(self) -> None:
        await self.session.rollback()

    async def refresh(self, entity: ModelType) -> None:
        await self.session.refresh(entity)
