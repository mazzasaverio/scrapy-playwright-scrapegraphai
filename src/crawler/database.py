import os
import psycopg2
from psycopg2 import pool, Error as PsycopgError
from psycopg2.extras import execute_values
import aiosql
import logfire
from pathlib import Path
from typing import Optional, Dict, Any, List, Union
from dotenv import load_dotenv

class DatabaseManager:
    def __init__(self):
        self.pool = None
        load_dotenv()
        
        self._connection_params = {
            'host': os.getenv('POSTGRES_HOST', 'localhost'),
            'port': int(os.getenv('POSTGRES_PORT', 5432)),
            'user': os.getenv('POSTGRES_USER', 'postgres'),
            'password': os.getenv('POSTGRES_PASSWORD', ''),
            'database': os.getenv('POSTGRES_DATABASE', 'postgres'),
            'sslmode': os.getenv('POSTGRES_SSLMODE', 'prefer')
        }
        
        # Load SQL files
        self._load_sql_files()

    def _load_sql_files(self):
        """Load SQL schema and queries from files"""
        try:
            sql_dir = Path(__file__).parent / 'sql'
            
            # Load schema
            schema_file = sql_dir / 'schema.sql'
            if not schema_file.exists():
                raise FileNotFoundError(f"Schema file not found at: {schema_file}")
            
            with open(schema_file) as f:
                self.schema_sql = f.read()
            
            # Load queries
            queries_file = sql_dir / 'queries.sql'
            if not queries_file.exists():
                raise FileNotFoundError(f"Queries file not found at: {queries_file}")
                
            with open(queries_file) as f:
                self.queries = aiosql.from_str(f.read(), "psycopg2")
           
            
        except Exception as e:
            logfire.error(f"Failed to load SQL files: {e}")
            raise

    def initialize(self):
        """Initialize database connection pool and schema"""
        try:
            # Create connection pool
            self.pool = psycopg2.pool.SimpleConnectionPool(
                minconn=1,
                maxconn=10,
                **self._connection_params
            )

            # **Set autocommit mode on all connections in the pool**
            for conn in self.pool._pool:
                conn.autocommit = True

            # Create schema
            self._execute_schema_creation()
         
        except PsycopgError as e:
            logfire.error(
                "Database connection error",
                error=str(e),
                connection_params={
                    k:v for k,v in self._connection_params.items() 
                    if k != 'password'
                }
            )
            raise
        except Exception as e:
            logfire.error(f"Failed to initialize database: {e}")
            raise
        
    def _execute_schema_creation(self):
        """Execute schema creation SQL with proper error handling"""
        if not self.pool:
            raise RuntimeError("Database pool not initialized")
            
        conn = self.pool.getconn()
        try:
            with conn.cursor() as cur:
                # First drop existing types if they exist
                cur.execute("""
                    DROP TYPE IF EXISTS url_state_type CASCADE;
                    DROP TYPE IF EXISTS config_state_type CASCADE;
                """)
                
                # Create ENUMs and tables
                cur.execute(self.schema_sql)
                conn.commit()
            
        except PsycopgError as e:
            conn.rollback()
            logfire.error(
                "Schema creation failed",
                error=str(e),
                error_type=type(e).__name__
            )
            raise
        finally:
            self.pool.putconn(conn)
            
    # Rest of the code remains the same
            
    def execute_query(
        self, 
        query: str, 
        params: Optional[Union[tuple, dict]] = None, 
        fetch: bool = False,
        fetch_one: bool = False
    ) -> Optional[List[tuple]]:
        """Execute a SQL query with enhanced error handling"""
        if not self.pool:
            raise RuntimeError("Database pool not initialized")
            
        conn = self.pool.getconn()
        try:
            with conn.cursor() as cur:
                cur.execute(query, params)
                
                result = None
                if fetch:
                    if fetch_one:
                        result = cur.fetchone()
                    else:
                        result = cur.fetchall()
                    
                conn.commit()
                return result
                
        except PsycopgError as e:
            conn.rollback()
            logfire.error(
                "Query execution failed",
                query=query,
                params=params,
                error=str(e)
            )
            raise
        finally:
            self.pool.putconn(conn)
            
    def execute_batch(
        self, 
        query: str, 
        params_list: List[Union[tuple, dict]], 
        page_size: int = 1000
    ) -> None:
        """Execute batch operations with proper error handling"""
        if not self.pool:
            raise RuntimeError("Database pool not initialized")
            
        conn = self.pool.getconn()
        try:
            with conn.cursor() as cur:
                execute_values(cur, query, params_list, page_size=page_size)
                conn.commit()
      
                
        except PsycopgError as e:
            conn.rollback()
            logfire.error(
                "Batch execution failed",
                query=query,
                batch_size=len(params_list),
                error=str(e)
            )
            raise
        finally:
            self.pool.putconn(conn)
    
    def check_connection(self) -> bool:
        """Test database connection"""
        try:
            conn = self.pool.getconn()
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
                return True
        except Exception as e:
            logfire.error("Connection test failed", error=str(e))
            return False
        finally:
            if conn:
                self.pool.putconn(conn)
            
    def close(self):
        """Close database connections"""
        if self.pool:
            try:
                self.pool.closeall()
          
            except Exception as e:
                logfire.error(f"Error closing database connections: {e}")

# Singleton instance
db_manager = DatabaseManager()