from typing import Dict, List, Optional, Any, Tuple, Union
from datetime import datetime
import logfire
from psycopg2.extras import execute_values, DictCursor

class BaseCRUD:
    """Base CRUD operations for database interactions."""
    
    def __init__(self, conn, queries):
        """Initialize with database connection and queries"""
        self.conn = conn
        # Access to the queries loaded in DatabaseManager
        self.queries = queries

    def execute_query(
        self,
        query: str,
        params: dict = None,
        fetch: bool = False,
        fetch_one: bool = False,
        as_dict: bool = True
    ) -> Optional[Union[List[Dict], Dict, List, Any]]:
        try:
            cursor_factory = DictCursor if as_dict else None
            with self.conn.cursor(cursor_factory=cursor_factory) as cur:
                cur.execute(query, params)
                if fetch:
                    if fetch_one:
                        result = cur.fetchone()
                        return dict(result) if result and as_dict else result
                    else:
                        results = cur.fetchall()
                        return [dict(row) for row in results] if as_dict else results
                # No need to call self.conn.commit() since autocommit is enabled
                return None
        except Exception as e:
            # No need to call self.conn.rollback() since autocommit is enabled
            logfire.error(
                "Database query execution failed",
                query=query,
                params=params,
                error=str(e)
            )
            raise

    def insert_one(
        self, 
        table: str, 
        data: Dict[str, Any], 
        return_id: bool = True,
        exclude_none: bool = True
    ) -> Optional[int]:
        """
        Insert a single record with improved parameter handling.
        
        Args:
            table: Table name
            data: Column-value pairs
            return_id: Whether to return inserted ID
            exclude_none: Whether to exclude None values
            
        Returns:
            Optional ID of inserted record
        """
        try:
            # Filter out None values if requested
            filtered_data = {
                k: v for k, v in data.items() 
                if not exclude_none or v is not None
            }
            
            columns = list(filtered_data.keys())
            placeholders = [f'%({col})s' for col in columns]
            
            query = f"""
                INSERT INTO {table} 
                ({', '.join(columns)}) 
                VALUES ({', '.join(placeholders)})
                {' RETURNING id' if return_id else ''}
            """
            
            result = self.execute_query(
                query, 
                filtered_data,
                fetch=return_id,
                fetch_one=True
            )
            
            return result['id'] if return_id and result else None
            
        except Exception as e:
            logfire.error(
                "Error inserting record",
                table=table,
                data=str(data),
                error=str(e)
            )
            raise

    def insert_many(
        self,
        table: str,
        records: List[Dict[str, Any]],
        page_size: int = 1000,
        return_ids: bool = False
    ) -> Optional[List[int]]:
        """
        Batch insert multiple records with improved handling.
        
        Args:
            table: Table name
            records: List of records to insert
            page_size: Batch size
            return_ids: Whether to return inserted IDs
            
        Returns:
            Optional list of inserted record IDs
        """
        if not records:
            return []
            
        try:
            # Get columns from first record
            columns = list(records[0].keys())
            
            placeholders = ', '.join([f'%({col})s' for col in columns])
            base_query = f"""
                INSERT INTO {table} 
                ({', '.join(columns)})
                VALUES ({placeholders})
                {' RETURNING id' if return_ids else ''}
            """
            
            inserted_ids = []
            
            # Process in batches
            for i in range(0, len(records), page_size):
                batch = records[i:i + page_size]
                
                with self.conn.cursor() as cur:
                    execute_values(
                        cur,
                        base_query,
                        batch,
                        template=None,
                        page_size=page_size
                    )
                    if return_ids:
                        result = cur.fetchall()
                        inserted_ids.extend([row['id'] for row in result])
                    
                logfire.debug(
                    "Batch insert completed",
                    table=table,
                    batch_size=len(batch)
                )
                
            return inserted_ids if return_ids else None
            
        except Exception as e:
            logfire.error(
                "Error in batch insert",
                table=table,
                error=str(e)
            )
            raise

    def update(
        self,
        table: str,
        where: Dict[str, Any],
        values: Dict[str, Any],
        return_updated: bool = False
    ) -> Optional[List[Dict]]:
        """
        Update records with improved condition handling.
        
        Args:
            table: Table name
            where: Where conditions
            values: Values to update
            return_updated: Whether to return updated records
            
        Returns:
            Optional list of updated records
        """
        try:
            set_items = [f"{k} = %({k})s" for k in values.keys()]
            where_items = [f"{k} = %({k})s" for k in where.keys()]
            
            query = f"""
                UPDATE {table} 
                SET {', '.join(set_items)}
                WHERE {' AND '.join(where_items)}
                {' RETURNING *' if return_updated else ''}
            """
            
            params = {**values, **where}
            
            result = self.execute_query(
                query,
                params,
                fetch=return_updated
            )
            
            return result if return_updated else None
            
        except Exception as e:
            logfire.error(
                "Error updating records",
                table=table,
                where=where,
                values=values,
                error=str(e)
            )
            raise

    def select(
        self,
        table: str,
        columns: Optional[List[str]] = None,
        where: Optional[Dict[str, Any]] = None,
        order_by: Optional[str] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        group_by: Optional[List[str]] = None
    ) -> List[Dict]:
        """
        Select records with enhanced query building.
        
        Args:
            table: Table name
            columns: Columns to select
            where: Where conditions
            order_by: Order by clause
            limit: Result limit
            offset: Result offset
            group_by: Group by columns
            
        Returns:
            List of matching records
        """
        try:
            # Build query parts
            select_cols = ', '.join(columns) if columns else '*'
            query_parts = [f"SELECT {select_cols}", f"FROM {table}"]
            params = {}
            
            # Add WHERE clause
            if where:
                conditions = []
                for i, (key, value) in enumerate(where.items()):
                    param_name = f"where_{i}"
                    if isinstance(value, (list, tuple)):
                        conditions.append(f"{key} = ANY(%({param_name})s)")
                    elif value is None:
                        conditions.append(f"{key} IS NULL")
                    else:
                        conditions.append(f"{key} = %({param_name})s")
                    params[param_name] = value
                    
                if conditions:
                    query_parts.append("WHERE " + " AND ".join(conditions))
            
            # Add GROUP BY
            if group_by:
                query_parts.append(f"GROUP BY {', '.join(group_by)}")
            
            # Add ORDER BY
            if order_by:
                query_parts.append(f"ORDER BY {order_by}")
            
            # Add LIMIT and OFFSET
            if limit is not None:
                query_parts.append(f"LIMIT {limit}")
            if offset is not None:
                query_parts.append(f"OFFSET {offset}")
            
            # Execute query
            query = " ".join(query_parts)
            result = self.execute_query(query, params, fetch=True)
            
            logfire.debug(
                "Select query executed",
                table=table,
                rows=len(result) if result else 0
            )
            
            return result if result else []
            
        except Exception as e:
            logfire.error(
                "Error selecting records",
                table=table,
                error=str(e)
            )
            raise

    def delete(
        self,
        table: str,
        where: Dict[str, Any],
        return_deleted: bool = False
    ) -> Optional[List[Dict]]:
        """
        Delete records with improved condition handling.
        
        Args:
            table: Table name
            where: Where conditions
            return_deleted: Whether to return deleted records
            
        Returns:
            Optional list of deleted records
        """
        try:
            where_items = [f"{k} = %({k})s" for k in where.keys()]
            
            query = f"""
                DELETE FROM {table}
                WHERE {' AND '.join(where_items)}
                {' RETURNING *' if return_deleted else ''}
            """
            
            result = self.execute_query(
                query,
                where,
                fetch=return_deleted
            )
            
            count = len(result) if return_deleted and result else 0
            logfire.info(
                "Delete completed",
                table=table,
                records_deleted=count
            )
            
            return result if return_deleted else None
            
        except Exception as e:
            logfire.error(
                "Error deleting records",
                table=table,
                where=where,
                error=str(e)
            )
            raise

    def exists(
        self,
        table: str,
        where: Dict[str, Any]
    ) -> bool:
        """
        Check existence with improved condition handling.
        
        Args:
            table: Table name
            where: Where conditions
            
        Returns:
            Whether matching records exist
        """
        try:
            where_items = [f"{k} = %({k})s" for k in where.keys()]
            
            query = f"""
                SELECT EXISTS (
                    SELECT 1 FROM {table}
                    WHERE {' AND '.join(where_items)}
                ) AS exists
            """
            
            result = self.execute_query(
                query,
                where,
                fetch=True,
                fetch_one=True
            )
            
            return result['exists'] if result else False
            
        except Exception as e:
            logfire.error(
                "Error checking existence",
                table=table,
                where=where,
                error=str(e)
            )
            return False
