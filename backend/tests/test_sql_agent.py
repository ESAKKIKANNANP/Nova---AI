# =============================================================================
# backend/tests/test_sql_agent.py
#
# Unit tests for the SQL Agent and Security Guardrails.
# =============================================================================

import pytest
import os
import sqlite3
from unittest.mock import patch
from db.connection import get_db_connection
from agents.sql_agent import SafeSQLAgent

@pytest.fixture
def mock_db(tmp_path, monkeypatch):
    """Creates a temporary SQLite database for testing."""
    db_path = str(tmp_path / "test.db")
    
    # Create schema and data
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("CREATE TABLE users (id INTEGER, name TEXT, sales INTEGER)")
    cursor.execute("INSERT INTO users VALUES (1, 'Alice', 1000)")
    cursor.execute("INSERT INTO users VALUES (2, 'Bob', 500)")
    conn.commit()
    conn.close()
    
    db_uri = f"sqlite:///{db_path}"
    monkeypatch.setenv("DATABASE_URI", db_uri)
    
    return db_uri

def test_db_connection(mock_db):
    db = get_db_connection()
    # Check if table exists
    assert "users" in db.get_usable_table_names()

@patch("agents.sql_agent.create_sql_agent")
def test_sql_agent_guardrails(mock_create_sql_agent):
    """Tests the Python-level regex guardrails."""
    agent = SafeSQLAgent()
    
    assert agent.validate_query("SELECT * FROM users") is True
    assert agent.validate_query("SELECT count(*) FROM sales") is True
    
    # Malicious queries should be blocked
    assert agent.validate_query("DROP TABLE users") is False
    assert agent.validate_query("DELETE FROM users WHERE id=1") is False
    assert agent.validate_query("UPDATE users SET name='Hack'") is False
    assert agent.validate_query("INSERT INTO users VALUES (3)") is False
    assert agent.validate_query("SELECT * FROM users; DROP TABLE users;") is False

@pytest.mark.asyncio
@patch("agents.sql_agent.create_sql_agent")
async def test_sql_agent_ainvoke(mock_create_sql_agent, mock_db):
    """Tests the execution flow of the SQL agent."""
    class MockExecutor:
        async def ainvoke(self, args):
            return {"output": "There are 2 users in the database."}
            
    mock_create_sql_agent.return_value = MockExecutor()
    
    agent = SafeSQLAgent()
    result = await agent.ainvoke("How many users are there?")
    
    assert "2 users" in result
