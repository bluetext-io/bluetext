from typing import Type, TypeVar, List, Optional, Dict, Any, Sequence
from sqlmodel import SQLModel
from psycopg.rows import dict_row
from psycopg import sql

from .connection import get_connection
from ..utils import log

logger = log.get_logger(__name__)

T = TypeVar("T", bound=SQLModel)

async def create_item(item: SQLModel) -> SQLModel:
    """Create a new item in the database.

    Args:
        item: SQLModel instance to create

    Returns:
        The created item with its ID populated
    """
    async with get_connection() as conn:
        table_name = item.__class__.__tablename__
        columns = []
        values = []
        placeholders = []

        for field_name, field_value in item.model_dump(exclude_unset=True).items():
            if field_name != "id":  # Skip auto-increment ID
                columns.append(field_name)
                values.append(field_value)
                placeholders.append("%s")

        # Use psycopg's sql module to safely handle table/column names
        query = sql.SQL("""
            INSERT INTO {table} ({columns})
            VALUES ({placeholders})
            RETURNING *
        """).format(
            table=sql.Identifier(table_name),
            columns=sql.SQL(', ').join(map(sql.Identifier, columns)),
            placeholders=sql.SQL(', ').join([sql.Placeholder()] * len(columns))
        )

        async with conn.cursor(row_factory=dict_row) as cur:
            await cur.execute(query, values)
            result = await cur.fetchone()
            await conn.commit()

        return item.__class__(**result)

async def get_item(
    model: Type[T],
    item_id: int
) -> Optional[T]:
    """Get a single item by ID.

    Args:
        model: The SQLModel class
        item_id: The item's ID

    Returns:
        The item if found, None otherwise
    """
    async with get_connection() as conn:
        table_name = model.__tablename__
        query = sql.SQL("SELECT * FROM {table} WHERE id = %s").format(
            table=sql.Identifier(table_name)
        )

        async with conn.cursor(row_factory=dict_row) as cur:
            await cur.execute(query, (item_id,))
            result = await cur.fetchone()

        return model(**result) if result else None

async def get_items(
    model: Type[T],
    limit: int = 100,
    offset: int = 0,
    where: Optional[Dict[str, Any]] = None,
    order_by: Optional[str] = None
) -> List[T]:
    """Get multiple items with optional filtering.

    Args:
        model: The SQLModel class
        limit: Maximum number of items to return
        offset: Number of items to skip
        where: Dictionary of field=value filters
        order_by: Column name to order by

    Returns:
        List of items matching the criteria
    """
    async with get_connection() as conn:
        table_name = model.__tablename__
        query_parts = [sql.SQL("SELECT * FROM {}").format(sql.Identifier(table_name))]
        params = []

        if where:
            where_clauses = []
            for field, value in where.items():
                where_clauses.append(sql.SQL("{} = %s").format(sql.Identifier(field)))
                params.append(value)
            query_parts.append(sql.SQL("WHERE {}").format(sql.SQL(' AND ').join(where_clauses)))

        if order_by:
            query_parts.append(sql.SQL("ORDER BY {}").format(sql.Identifier(order_by)))

        query_parts.append(sql.SQL("LIMIT %s OFFSET %s"))
        params.extend([limit, offset])

        query = sql.SQL(" ").join(query_parts)

        async with conn.cursor(row_factory=dict_row) as cur:
            await cur.execute(query, params)
            results = await cur.fetchall()

        return [model(**row) for row in results]

async def update_item(
    model: Type[T],
    item_id: int,
    updates: Dict[str, Any]
) -> Optional[T]:
    """Update an item by ID.

    Args:
        model: The SQLModel class
        item_id: The item's ID
        updates: Dictionary of field=value updates

    Returns:
        The updated item if found, None otherwise
    """
    async with get_connection() as conn:
        table_name = model.__tablename__
        set_clauses = []
        params = []

        for field, value in updates.items():
            set_clauses.append(sql.SQL("{} = %s").format(sql.Identifier(field)))
            params.append(value)

        params.append(item_id)

        query = sql.SQL("""
            UPDATE {table}
            SET {updates}
            WHERE id = %s
            RETURNING *
        """).format(
            table=sql.Identifier(table_name),
            updates=sql.SQL(', ').join(set_clauses)
        )

        async with conn.cursor(row_factory=dict_row) as cur:
            await cur.execute(query, params)
            result = await cur.fetchone()
            await conn.commit()

        return model(**result) if result else None

async def delete_item(
    model: Type[T],
    item_id: int
) -> bool:
    """Delete an item by ID.

    Args:
        model: The SQLModel class
        item_id: The item's ID

    Returns:
        True if deleted, False if not found
    """
    async with get_connection() as conn:
        table_name = model.__tablename__
        query = sql.SQL("DELETE FROM {table} WHERE id = %s RETURNING id").format(
            table=sql.Identifier(table_name)
        )

        async with conn.cursor() as cur:
            await cur.execute(query, (item_id,))
            result = await cur.fetchone()
            await conn.commit()

        return result is not None

async def execute_query(
    query: str,
    params: Optional[Sequence[Any]] = None
) -> List[Dict[str, Any]]:
    """Execute a raw SQL query.

    Args:
        query: SQL query string
        params: Query parameters

    Returns:
        List of result rows as dictionaries
    """
    async with get_connection() as conn:
        async with conn.cursor(row_factory=dict_row) as cur:
            await cur.execute(query, params or [])
            results = await cur.fetchall()

    return results

async def execute_transaction(
    operations: List[tuple[str, Optional[Sequence[Any]]]]
) -> None:
    """Execute multiple operations in a transaction.

    Args:
        operations: List of (query, params) tuples

    Raises:
        Exception: If any operation fails, all are rolled back
    """
    async with get_connection() as conn:
        try:
            async with conn.cursor() as cur:
                for query, params in operations:
                    await cur.execute(query, params or [])
            await conn.commit()
        except Exception as e:
            await conn.rollback()
            logger.error(f"Transaction failed: {e}")
            raise

async def bulk_create(
    model: Type[T],
    items: List[Dict[str, Any]]
) -> List[T]:
    """Bulk create multiple items efficiently.

    Args:
        model: The SQLModel class
        items: List of dictionaries with item data

    Returns:
        List of created items
    """
    if not items:
        return []

    async with get_connection() as conn:
        table_name = model.__tablename__

        # Get columns from first item (excluding id)
        columns = [k for k in items[0].keys() if k != "id"]

        # Build VALUES clause with multiple rows
        placeholders_row = f"({', '.join(['%s'] * len(columns))})"
        placeholders_all = ', '.join([placeholders_row] * len(items))

        # Flatten values
        values = []
        for item in items:
            for col in columns:
                values.append(item.get(col))

        # Build the query safely
        query = sql.SQL("""
            INSERT INTO {table} ({columns})
            VALUES {values}
            RETURNING *
        """).format(
            table=sql.Identifier(table_name),
            columns=sql.SQL(', ').join(map(sql.Identifier, columns)),
            values=sql.SQL(placeholders_all)
        )

        async with conn.cursor(row_factory=dict_row) as cur:
            await cur.execute(query, values)
            results = await cur.fetchall()
            await conn.commit()

        return [model(**row) for row in results]
