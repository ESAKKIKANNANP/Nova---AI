# =============================================================================
# backend/graphs/chat_graph.py
#
# LangGraph for the conversational interface.
# =============================================================================

from langgraph.graph import StateGraph, END
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import MemorySaver

from agents.chat_agent import get_chat_model, chat_tools, CHAT_SYSTEM_PROMPT

# For this chat agent, we use the prebuilt ReAct agent from LangGraph 0.1/0.2 
# which automatically handles tool calling and message history.

def build_chat_graph():
    """
    Constructs a stateful conversational graph.
    """
    llm = get_chat_model()
    
    # create_react_agent handles the State (messages), the LLM routing, and tool execution.
    app = create_react_agent(
        llm, 
        tools=chat_tools, 
        prompt=CHAT_SYSTEM_PROMPT,
        checkpointer=MemorySaver()
    )
    
    return app

# Singleton instance for the server
chat_app = build_chat_graph()
