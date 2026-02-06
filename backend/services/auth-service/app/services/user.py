"""
User Service
"""
from datetime import datetime
from typing import Optional, List
from uuid import UUID

from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate
from app.services.jwt import jwt_service


class UserService:
    """User management service"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, user_id: UUID) -> Optional[User]:
        """Get user by ID"""
        result = await self.db.execute(
            select(User).where(User.id == user_id)
        )
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email"""
        result = await self.db.execute(
            select(User).where(User.email == email.lower())
        )
        return result.scalar_one_or_none()

    async def create(self, user_data: UserCreate) -> User:
        """Create a new user"""
        hashed_password = jwt_service.hash_password(user_data.password)

        user = User(
            email=user_data.email.lower(),
            hashed_password=hashed_password,
            full_name=user_data.full_name,
        )

        self.db.add(user)
        await self.db.flush()
        await self.db.refresh(user)
        return user

    async def update(self, user_id: UUID, user_data: UserUpdate) -> Optional[User]:
        """Update user profile"""
        user = await self.get_by_id(user_id)
        if not user:
            return None

        update_data = user_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(user, field, value)

        user.updated_at = datetime.utcnow()
        await self.db.flush()
        await self.db.refresh(user)
        return user

    async def update_password(self, user_id: UUID, new_password: str) -> bool:
        """Update user password"""
        hashed_password = jwt_service.hash_password(new_password)
        result = await self.db.execute(
            update(User)
            .where(User.id == user_id)
            .values(hashed_password=hashed_password, updated_at=datetime.utcnow())
        )
        return result.rowcount > 0

    async def update_last_login(self, user_id: UUID) -> None:
        """Update last login timestamp"""
        await self.db.execute(
            update(User)
            .where(User.id == user_id)
            .values(last_login_at=datetime.utcnow())
        )

    async def deactivate(self, user_id: UUID) -> bool:
        """Deactivate user account"""
        result = await self.db.execute(
            update(User)
            .where(User.id == user_id)
            .values(is_active=False, updated_at=datetime.utcnow())
        )
        return result.rowcount > 0

    async def delete(self, user_id: UUID) -> bool:
        """Delete user account"""
        result = await self.db.execute(
            delete(User).where(User.id == user_id)
        )
        return result.rowcount > 0

    async def list_users(
        self,
        skip: int = 0,
        limit: int = 20,
        is_active: Optional[bool] = None
    ) -> tuple[List[User], int]:
        """List users with pagination"""
        query = select(User)

        if is_active is not None:
            query = query.where(User.is_active == is_active)

        # Get total count
        count_query = select(User.id)
        if is_active is not None:
            count_query = count_query.where(User.is_active == is_active)
        count_result = await self.db.execute(count_query)
        total = len(count_result.all())

        # Get paginated results
        query = query.order_by(User.created_at.desc()).offset(skip).limit(limit)
        result = await self.db.execute(query)
        users = result.scalars().all()

        return list(users), total

    async def search_users(self, query: str, limit: int = 10) -> List[User]:
        """Search users by email or name"""
        search_query = select(User).where(
            (User.email.ilike(f"%{query}%")) |
            (User.full_name.ilike(f"%{query}%"))
        ).limit(limit)

        result = await self.db.execute(search_query)
        return list(result.scalars().all())
