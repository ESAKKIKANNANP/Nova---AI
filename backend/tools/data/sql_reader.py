# =============================================================================
# backend/tools/data/sql_reader.py
#
# SQL Tool: Connects to relational databases and executes SQL queries.
# =============================================================================

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from sqlalchemy import create_engine, text

from tools.base import BaseTool


class SQLReaderInput(BaseModel):
    connection_uri: str = Field(
        ...,
        description="SQLAlchemy database connection URI (e.g. postgresql://user:pass@localhost:5432/db).",
    )
    query: str = Field(
        ...,
        description="The SQL SELECT query statement to execute.",
    )
    row_limit: int = Field(
        default=100,
        description="Maximum number of rows to return (default: 100).",
    )


class SQLReaderTool(BaseTool):
    """
    Tool that connects to an SQL database, executes a query safely, and returns the rows.
    """
    name = "sql_reader"
    description = "Executes SELECT queries against SQL databases and returns query results in JSON format."
    args_schema = SQLReaderInput

    def _run(self, connection_uri: str, query: str, row_limit: int = 100) -> Dict[str, Any]:
        # Validate that query is read-only (SELECT statement)
        cleaned_query = query.strip().lower()
        if not cleaned_query.startswith("select") and not cleaned_query.startswith("with"):
            raise PermissionError("Only read-only SELECT or WITH query operations are permitted.")

        # Create connection engine
        try:
            engine = create_engine(connection_uri, future=True)
        except Exception as exc:
            raise RuntimeError(f"Failed to create database connection: {exc}")

        # Execute query
        try:
            with engine.connect() as conn:
                result = conn.execute(text(query))
                
                # Fetch headers
                columns = list(result.keys())
                
                # Fetch rows up to the limit
                rows: List[Dict[str, Any]] = []
                count = 0
                for row in result:
                    if count >= row_limit:
                        break
                    # Zip headers with values, converting non-standard Python types
                    row_dict = {}
                    for col, val in zip(columns, row, strict=False):
                        if hasattr(val, "isoformat"):  # Convert datetime/date objects
                            row_dict[col] = val.isoformat()
                        elif hasattr(val, "value") and hasattr(val, "name"):  # Enum objects
                            row_dict[col] = val.value
                        else:
                            row_dict[col] = val
                    rows.append(row_dict)
                    count += 1
                
                return {
                    "columns": columns,
                    "row_count": len(rows),
                    "rows": rows,
                    "truncated": result.rowcount > row_limit if hasattr(result, "rowcount") else False
                }
        except Exception as exc:
            raise RuntimeError(f"Failed executing SQL query: {exc}")
        finally:
            engine.dispose()
