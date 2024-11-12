# src/crawler/database.py
import os
import asyncio
import asyncpg
import aiosql
from datetime import datetime
from typing import Optional, List, Dict, Any
import logfire
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class DatabaseManager:
    def __init__(self):
        self.pool: Optional[asyncpg.Pool] = None
        self._connection_params = {
            'host': os.getenv('POSTGRES_HOST', 'localhost'),
            'port': int(os.getenv('POSTGRES_PORT', 5432)),
            'user': os.getenv('POSTGRES_USER', 'postgres'),
            'password': os.getenv('POSTGRES_PASSWORD', ''),
            'database': os.getenv('POSTGRES_DATABASE', 'postgres')
        }
        
        # Load SQL queries using aiosql
        queries_path = os.path.join(os.path.dirname(__file__), 'sql')
        self.queries = aiosql.from_path(queries_path, "asyncpg")
        logfire.info("SQL queries loaded successfully")

    async def initialize(self) -> None:
        """Initialize database pool and create tables if they don't exist"""
        if not self.pool:
            try:
                self.pool = await asyncpg.create_pool(**self._connection_params)
                logfire.info("Database pool created successfully")
                
                # Execute schema creation
                async with self.pool.acquire() as conn:
                    await self.queries.create_schema(conn)
                logfire.info("Database schema initialized successfully")
                
            except Exception as e:
                logfire.error(f"Failed to initialize database: {e}")
                raise

    async def store_frontier_url(self, url: str, category: str, type_: int, 
                               depth: int = 0, is_target: bool = False) -> str:
        """Store a new URL in the frontier"""
        if not self.pool:
            raise RuntimeError("Database not initialized")
        
        try:
            async with self.pool.acquire() as conn:
                url_id = await self.queries.insert_frontier_url(
                    conn,
                    url=url,
                    category=category,
                    type_=type_,
                    depth=depth,
                    is_target=is_target
                )
                if url_id:
                    logfire.info(f"Stored new frontier URL: {url}")
                else:
                    logfire.info(f"URL already exists in frontier: {url}")
                return url_id
        except Exception as e:
            logfire.error(f"Failed to store frontier URL {url}: {e}")
            raise

    async def update_config_url_log(self, url: str, category: str, type_: int, 
                                  success: bool = True, status: str = "completed") -> None:
        """Update or create config URL log entry"""
        if not self.pool:
            raise RuntimeError("Database not initialized")
        
        try:
            async with self.pool.acquire() as conn:
                await self.queries.update_config_url_log(
                    conn,
                    url=url,
                    category=category,
                    type_=type_,
                    success=success,
                    status=status
                )
                logfire.info(f"Updated config URL log: {url}")
        except Exception as e:
            logfire.error(f"Failed to update config URL log {url}: {e}")
            raise

    async def get_unprocessed_frontier_urls(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get unprocessed URLs from frontier"""
        if not self.pool:
            raise RuntimeError("Database not initialized")
        
        try:
            async with self.pool.acquire() as conn:
                rows = await self.queries.get_unprocessed_urls(conn, limit=limit)
                return [dict(row) for row in rows]
        except Exception as e:
            logfire.error(f"Failed to get unprocessed URLs: {e}")
            raise

    async def mark_url_processed(self, url_id: str, success: bool = True, 
                               error_message: str = None) -> None:
        """Mark a URL as processed in the frontier"""
        if not self.pool:
            raise RuntimeError("Database not initialized")
            
        try:
            async with self.pool.acquire() as conn:
                await self.queries.mark_url_processed(
                    conn,
                    url_id=url_id,
                    success=success,
                    error_message=error_message
                )
                logfire.info(f"Marked URL {url_id} as processed")
        except Exception as e:
            logfire.error(f"Failed to mark URL {url_id} as processed: {e}")
            raise
    async def close(self) -> None:
        """Close the database pool"""
        if self.pool:
            await self.pool.close()
            logfire.info("Database pool closed")
# Singleton instance
db_manager = DatabaseManager()
