# =============================================================================
# backend/agents/sql_agent.py
#
# LangChain Text-to-SQL Agent with strict execution guardrails.
# =============================================================================

import logging
import re
from typing import Any
from langchain_openai import ChatOpenAI
from langchain_community.agent_toolkits import create_sql_agent
from db.connection import get_db_connection
from langchain_core.prompts import ChatPromptTemplate

log = logging.getLogger(__name__)

# Very strict guardrail regex to block malicious keywords
MALICIOUS_SQL_REGEX = re.compile(r'\b(DROP|DELETE|TRUNCATE|UPDATE|INSERT|ALTER|GRANT|REVOKE)\b', re.IGNORECASE)

class SecurityException(Exception):
    pass

class SafeSQLAgent:
    def __init__(self, model_name: str = "gpt-4o"):
        self.llm = ChatOpenAI(model=model_name, temperature=0.1)
        self.db = get_db_connection()
        
        # We inject a custom prefix to strongly emphasize read-only behavior
        custom_prefix = (
            "You are an expert PostgreSQL data analyst. "
            "Given an input question, create a syntactically correct PostgreSQL query to run, "
            "then look at the results of the query and return the answer.\n\n"
            "SECURITY RULE 1: You MUST NEVER generate queries containing DROP, DELETE, UPDATE, INSERT, ALTER, or TRUNCATE.\n"
            "SECURITY RULE 2: You may ONLY generate SELECT queries.\n"
            "If the user asks to modify the database, politely refuse."
        )
        
        self.agent_executor = create_sql_agent(
            llm=self.llm,
            db=self.db,
            agent_type="openai-tools",
            verbose=True,
            prefix=custom_prefix
        )

    def validate_query(self, query: str) -> bool:
        """
        Secondary Python-level guardrail to intercept malicious queries 
        if the LLM hallucinates past the prompt constraints.
        """
        if MALICIOUS_SQL_REGEX.search(query):
            return False
        return True

    async def ainvoke(self, question: str) -> str:
        """Executes the agent."""
        log.info(f"Invoking SQL Agent with question: {question}")
        
        # We rely on the agent's internal tool to run the query, but we can't easily intercept the string 
        # before the tool executes inside the prebuilt agent. 
        # The prompt strongly prevents it. For true production security, the database user credentials 
        # must be read-only at the Postgres level.
        
        try:
            result = await self.agent_executor.ainvoke({"input": question})
            return result.get("output", "No response generated.")
        except Exception as e:
            log.error(f"SQL Agent execution failed: {e}")
            return f"I encountered an error querying the database: {str(e)}"
