# =============================================================================
# backend/agents/chat_agent.py
#
# Conversational ReAct Agent that can answer questions about the ML pipeline.
# =============================================================================

import os
import logging
from typing import Annotated, TypedDict
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from langchain_core.messages import BaseMessage, SystemMessage
from services.rag_service import RAGService
from agents.sql_agent import SafeSQLAgent

log = logging.getLogger(__name__)

# --- TOOLS ---

@tool
def get_project_report(session_id: str) -> str:
    """
    Reads the master Markdown report for a given session. 
    Use this to answer broad questions about EDA, Model Comparison, or Business Insights.
    """
    path = f"artifacts/reports/report_{session_id}.md"
    if os.path.exists(path):
        with open(path, "r") as f:
            return f.read()
    return "Report not found. The pipeline might not be finished yet."

@tool
def get_feature_importance(session_id: str) -> str:
    """
    Returns the feature importance / SHAP summary. Use this when asked what drives the model.
    """
    path = f"artifacts/reports/report_{session_id}.md"
    if os.path.exists(path):
        with open(path, "r") as f:
            content = f.read()
            # Extremely naive extraction for MVP
            if "Explainability" in content:
                return "Found SHAP Explanations in report. " + content.split("Explainability")[1][:500]
    return "Feature importance data not found."

@tool
def predict_new_dataset(dataset_path: str) -> str:
    """
    Simulates predicting a new dataset. Use this when asked to 'Predict another dataset'.
    """
    return f"Successfully initiated prediction job for {dataset_path}. The results will be ready shortly."

@tool
def search_knowledge_base(query: str) -> str:
    """
    Searches the uploaded documents (PDFs, DOCX, CSVs) for information relevant to the user's query.
    Always use this when the user asks questions about specific domain knowledge, uploaded documents, or guidelines.
    """
    rag = RAGService()
    docs = rag.retrieve(query, k=3)
    
    if not docs:
        return "I could not find any relevant information in the uploaded knowledge base."
        
    formatted_results = "Here is the relevant information I found in the uploaded documents:\n\n"
    for idx, doc in enumerate(docs):
        source = doc.metadata.get("source", "Unknown Source")
        page = doc.metadata.get("page", "")
        citation = f"Source: {source}" + (f", Page: {page}" if page else "")
        formatted_results += f"[{idx+1}] {citation}\nExcerpt: {doc.page_content}\n\n"
        
    return formatted_results

@tool
def query_database(question: str) -> str:
    """
    Translates a natural language question into a SQL query and runs it against the PostgreSQL database.
    Use this tool whenever the user asks for data analytics, metrics, counts, averages, or top customers 
    that would naturally live in a relational database.
    """
    sql_agent = SafeSQLAgent()
    # Synchronously run the async agent by using asyncio if needed, or better, since it's an async tool:
    import asyncio
    try:
        # If we are already in an event loop, this tool should technically be async, but LangChain tools can handle sync/async.
        # We will wrap it synchronously just in case the executor isn't async friendly in all contexts.
        loop = asyncio.get_event_loop()
        if loop.is_running():
            import nest_asyncio
            nest_asyncio.apply()
        return loop.run_until_complete(sql_agent.ainvoke(question))
    except Exception as e:
        return f"Database query failed: {str(e)}"

# --- AGENT SETUP ---

def get_chat_model():
    return ChatOpenAI(model="gpt-4o", temperature=0.7, streaming=True)

chat_tools = [get_project_report, get_feature_importance, predict_new_dataset, search_knowledge_base, query_database]

CHAT_SYSTEM_PROMPT = """You are the Autonomous Data Scientist Chat Assistant.
You help users understand the machine learning models you just built.
You have tools to read the project reports, fetch feature importances, and run new predictions.
Crucially, you also have access to a semantic search tool (`search_knowledge_base`). Use it heavily if the user asks conceptual questions, asks about methodology, or references uploaded documents.
You also have access to a SQL database via the `query_database` tool. Use it to answer analytical questions about the raw data (e.g. "top 20 customers", "average sales").
Always be professional and concise. When using information from `search_knowledge_base`, clearly cite your sources using the metadata provided by the tool.
"""
