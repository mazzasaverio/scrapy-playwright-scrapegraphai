# src/tools/clean_db.py

import psycopg2
import os
from dotenv import load_dotenv
import logfire

def clean_database():
    """Clean all records from frontier_url and config_url_log tables"""
    # Load environment variables
    load_dotenv()
    
    # Get database connection parameters from environment
    db_params = {
        'dbname': os.getenv('POSTGRES_DATABASE'),
        'user': os.getenv('POSTGRES_USER'),
        'password': os.getenv('POSTGRES_PASSWORD'),
        'host': os.getenv('POSTGRES_HOST'),
        'port': os.getenv('POSTGRES_PORT')
    }
    
    try:
        # Connect to database
        logfire.info("Connecting to database...")
        conn = psycopg2.connect(**db_params)
        cur = conn.cursor()
        
        # Delete records from tables
        tables = ['frontier_url', 'config_url_log']
        
        for table in tables:
            try:
                # Get count before deletion
                cur.execute(f"SELECT COUNT(*) FROM {table}")
                count_before = cur.fetchone()[0]
                logfire.info(f"Records in {table} before deletion: {count_before}")
                
                # Delete records
                cur.execute(f"DELETE FROM {table}")
                conn.commit()
                
                # Get count after deletion
                cur.execute(f"SELECT COUNT(*) FROM {table}")
                count_after = cur.fetchone()[0]
                logfire.info(f"Records in {table} after deletion: {count_after}")
                logfire.info(f"Successfully deleted {count_before - count_after} records from {table}")
                
            except Exception as e:
                logfire.error(f"Error cleaning table {table}: {str(e)}")
                conn.rollback()
                raise
                
    except Exception as e:
        logfire.error(f"Database connection error: {str(e)}")
        raise
        
    finally:
        # Close database connection
        if 'cur' in locals():
            cur.close()
        if 'conn' in locals():
            conn.close()
            logfire.info("Database connection closed")

if __name__ == "__main__":
    try:
        clean_database()
        logfire.info("Database cleanup completed successfully")
    except Exception as e:
        logfire.error(f"Database cleanup failed: {str(e)}")
        exit(1)