# src/crawler/database.py

import os
import asyncio
import asyncpg
import aiosql
from datetime import datetime
from typing import Optional, List, Dict, Any
import logfire
from dotenv import load_dotenv
from twisted.internet import defer, threads, reactor
from twisted.python.threadpool import ThreadPool
from functools import partial

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
        
        # Load SQL queries
        queries_path = os.path.join(os.path.dirname(__file__), 'sql')
        self.queries = aiosql.from_path(queries_path, "asyncpg")
        logfire.info("SQL queries loaded successfully")
        
        # Create a thread pool for database operations
        self.threadpool = ThreadPool(minthreads=1, maxthreads=10)
        self.threadpool.start()
        reactor.addSystemEventTrigger('before', 'shutdown', self.threadpool.stop)

    async def _init_pool(self):
        """Initialize the connection pool"""
        try:
            self.pool = await asyncpg.create_pool(**self._connection_params)
            return self.pool
        except Exception as e:
            logfire.error(f"Failed to create connection pool: {e}")
            raise

    @defer.inlineCallbacks
    def initialize(self):
        """Initialize database connection"""
        if not self.pool:
            try:
                # Create a new event loop for this thread
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                # Initialize pool
                self.pool = yield threads.deferToThread(
                    lambda: loop.run_until_complete(self._init_pool())
                )
                
                logfire.info("Database pool created successfully")
                
                # Initialize schema
                yield threads.deferToThread(
                    lambda: loop.run_until_complete(self._execute_schema_creation())
                )
                
                logfire.info("Database schema initialized successfully")
                
            except Exception as e:
                logfire.error(f"Failed to initialize database: {e}")
                raise
            finally:
                loop.close()

    async def _execute_schema_creation(self):
        """Execute schema creation"""
        if not self.pool:
            raise RuntimeError("Database pool not initialized")
            
        async with self.pool.acquire() as conn:
            await self.queries.create_schema(conn)

    @defer.inlineCallbacks
    def store_frontier_url(self, url: str, category: str, type_: int,
                          depth: int = 0, is_target: bool = False):
        """Store a new URL in the frontier"""
        if not self.pool:
            raise RuntimeError("Database not initialized")
            
        try:
            # Create a new event loop for this operation
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            result = yield threads.deferToThread(
                lambda: loop.run_until_complete(
                    self._store_frontier_url_async(url, category, type_, depth, is_target)
                )
            )
            return result
            
        except Exception as e:
            logfire.error(f"Failed to store frontier URL {url}: {e}")
            raise
        finally:
            loop.close()

    async def _store_frontier_url_async(self, url: str, category: str, type_: int,
                                      depth: int = 0, is_target: bool = False):
        """Async implementation of URL storage"""
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

    @defer.inlineCallbacks
    def close(self):
        """Close database pool"""
        if self.pool:
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                yield threads.deferToThread(
                    lambda: loop.run_until_complete(self.pool.close())
                )
                
                logfire.info("Database pool closed")
                
            except Exception as e:
                logfire.error(f"Error closing database pool: {e}")
                raise
            finally:
                loop.close()
                self.threadpool.stop()

# Singleton instance
db_manager = DatabaseManager()