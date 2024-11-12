# src/crawler/utils/query_loader.py
import os
from typing import Dict
from logfire import logger

class QueryLoader:
    def __init__(self, sql_dir: str = None):
        if sql_dir is None:
            # Get the directory where the SQL files are stored
            sql_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'sql')
        self.sql_dir = sql_dir
        self.queries: Dict[str, str] = {}
        self._load_queries()

    def _load_queries(self) -> None:
        """Load all SQL queries from files"""
        try:
            # Load schema files
            schema_dir = os.path.join(self.sql_dir, 'schema')
            self.queries['schema'] = self._load_directory(schema_dir)

            # Load query files
            queries_dir = os.path.join(self.sql_dir, 'queries')
            self.queries['queries'] = self._load_directory(queries_dir)
            
            logger.info("SQL queries loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load SQL queries: {e}")
            raise

    def _load_directory(self, directory: str) -> Dict[str, str]:
        """Load all SQL files from a directory"""
        queries = {}
        if not os.path.exists(directory):
            logger.warning(f"Directory not found: {directory}")
            return queries

        for filename in os.listdir(directory):
            if filename.endswith('.sql'):
                file_path = os.path.join(directory, filename)
                queries.update(self._parse_sql_file(file_path))
        return queries

    def _parse_sql_file(self, file_path: str) -> Dict[str, str]:
        """Parse SQL file and extract named queries"""
        queries = {}
        current_query = []
        current_name = None

        with open(file_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line.startswith('-- name:'):
                    # Save previous query if exists
                    if current_name and current_query:
                        queries[current_name] = '\n'.join(current_query).strip()
                    # Start new query
                    current_name = line.split(':', 1)[1].strip()
                    current_query = []
                elif line and not line.startswith('--'):
                    current_query.append(line)

            # Save last query
            if current_name and current_query:
                queries[current_name] = '\n'.join(current_query).strip()

        return queries

    def get_query(self, query_name: str) -> str:
        """Get a query by name"""
        for section in self.queries.values():
            if query_name in section:
                return section[query_name]
        raise KeyError(f"Query '{query_name}' not found")

    def get_schema(self) -> str:
        """Get complete schema creation SQL"""
        return '\n'.join(self.queries['schema'].values())

query_loader = QueryLoader()