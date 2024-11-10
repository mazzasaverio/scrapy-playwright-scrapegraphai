# src/crawler/database.py
import os
import asyncio
import asyncpg
import logfire

from typing import Optional

logger = logfire.getLogger(__name__)

async def get_db_pool() -> Optional[asyncpg.Pool]:
    """Create and return database connection pool"""
    try:
        pool = await asyncpg.create_pool(
            host=os.getenv('POSTGRES_HOST', 'localhost'),
            port=int(os.getenv('POSTGRES_PORT', 5432)),
            database=os.getenv('POSTGRES_DB', 'crawler_db'),
            user=os.getenv('POSTGRES_USER', 'crawler'),
            password=os.getenv('POSTGRES_PASSWORD', 'crawler123')
        )
        return pool
    except Exception as e:
        logger.error(f"Failed to create database pool: {e}")
        return None

async def init_db():
    """Initialize database tables"""
    pool = await get_db_pool()
    if not pool:
        return
    
    async with pool.acquire() as conn:
        # Create FrontierUrl table
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS frontier_url (
                id SERIAL PRIMARY KEY,
                url TEXT NOT NULL,
                category TEXT NOT NULL,
                type INTEGER NOT NULL,
                depth INTEGER NOT NULL,
                is_target BOOLEAN NOT NULL,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                processed_at TIMESTAMP WITH TIME ZONE,
                UNIQUE(url, category)
            )
        ''')
        
        # Create ConfigUrlLog table
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS config_url_log (
                id SERIAL PRIMARY KEY,
                url TEXT NOT NULL,
                category TEXT NOT NULL,
                type INTEGER NOT NULL,
                last_checked_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(url, category)
            )
        ''')
    
    await pool.close()

async def test_connection() -> bool:
    """Test database connection"""
    pool = await get_db_pool()
    if not pool:
        return False
    
    try:
        async with pool.acquire() as conn:
            version = await conn.fetchval('SELECT version()')
            logger.info(f"Connected to PostgreSQL. Version: {version}")
            return True
    except Exception as e:
        logger.error(f"Database connection test failed: {e}")
        return False
    finally:
        await pool.close()

if __name__ == "__main__":
    # Script per testare la connessione
    async def main():
        await init_db()
        success = await test_connection()
        print("Connection test:", "SUCCESS" if success else "FAILED")

    asyncio.run(main())