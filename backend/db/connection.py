# =============================================================================
# backend/db/connection.py
#
# Centralized database connection logic.
# =============================================================================

import os
import logging
from langchain_community.utilities import SQLDatabase
from sqlalchemy import create_engine

log = logging.getLogger(__name__)

def get_db_connection() -> SQLDatabase:
    """
    Initializes the SQLAlchemy engine and wraps it in LangChain's SQLDatabase.
    Expects DATABASE_URI environment variable (e.g. postgresql://user:pass@localhost:5432/mydb).
    Falls back to a local SQLite database if none is provided.
    """
    db_uri = os.environ.get("DATABASE_URI")
    
    if not db_uri:
        log.warning("DATABASE_URI not found in environment. Defaulting to local SQLite (for dev/testing).")
        # Ensure we have a dummy db file path or in memory
        db_uri = "sqlite:///artifacts/test_db.sqlite"
        
    engine = create_engine(db_uri)
    db = SQLDatabase(engine)
    
    return db
