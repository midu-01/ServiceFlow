#!/usr/bin/env python3
"""Seed default demonstration users idempotently into ServiceFlow database."""

import asyncio
import os
import sys

# Ensure backend root is on python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.core.logging import logger, setup_logging
from app.core.security import hash_password
from app.db.models.user import User, UserRole
from app.db.session import get_worker_session
from app.repositories.user_repository import UserRepository

DEFAULT_USERS = [
    {
        "username": os.getenv("ADMIN_USERNAME", "admin"),
        "email": os.getenv("ADMIN_EMAIL", "admin@serviceflow.internal"),
        "password": os.getenv("ADMIN_PASSWORD", "AdminSecret123!"),
        "role": UserRole.ADMIN,
    },
    {
        "username": os.getenv("SUPERVISOR_USERNAME", "supervisor"),
        "email": os.getenv("SUPERVISOR_EMAIL", "supervisor@serviceflow.internal"),
        "password": os.getenv("SUPERVISOR_PASSWORD", "SupervisorSecret123!"),
        "role": UserRole.SUPERVISOR,
    },
    {
        "username": os.getenv("OPERATOR_USERNAME", "operator"),
        "email": os.getenv("OPERATOR_EMAIL", "operator@serviceflow.internal"),
        "password": os.getenv("OPERATOR_PASSWORD", "OperatorSecret123!"),
        "role": UserRole.OPERATOR,
    },
]


async def seed_users() -> None:
    setup_logging()
    logger.info("Initializing user seed process...")

    async with get_worker_session() as session:
        user_repo = UserRepository(session)
        created_count = 0
        existing_count = 0

        for user_data in DEFAULT_USERS:
            existing = await user_repo.get_by_username(user_data["username"])
            if existing:
                logger.info(f"User '{user_data['username']}' already exists (role={existing.role.value}). Skipping.")
                existing_count += 1
                continue

            user = User(
                username=user_data["username"],
                email=user_data["email"],
                hashed_password=hash_password(user_data["password"]),
                role=user_data["role"],
                is_active=True,
            )
            user_repo.add(user)
            await user_repo.commit()
            created_count += 1
            logger.info(f"Created seed user: username='{user.username}', role='{user.role.value}'")

        logger.info(f"Seeding completed: {created_count} created, {existing_count} already existed.")


if __name__ == "__main__":
    asyncio.run(seed_users())
