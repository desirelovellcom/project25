"""
Database connection and utilities
"""

import asyncpg
import os
from contextlib import asynccontextmanager
from typing import AsyncGenerator
import logging

logger = logging.getLogger(__name__)

class Database:
    def __init__(self, connection: asyncpg.Connection):
        self.connection = connection
    
    async def execute(self, query: str, *args):
        """Execute a query without returning results"""
        return await self.connection.execute(query, *args)
    
    async def fetch_one(self, query: str, *args):
        """Fetch a single row"""
        return await self.connection.fetchrow(query, *args)
    
    async def fetch_all(self, query: str, *args):
        """Fetch all rows"""
        return await self.connection.fetch(query, *args)

@asynccontextmanager
async def get_db() -> AsyncGenerator[Database, None]:
    """Database dependency for FastAPI"""
    database_url = os.getenv("DATABASE_URL", "postgresql://postgres:dev_password@localhost:5432/energy_cost")
    
    connection = None
    try:
        connection = await asyncpg.connect(database_url)
        yield Database(connection)
    except Exception as e:
        logger.error(f"Database connection error: {e}")
        raise
    finally:
        if connection:
            await connection.close()
