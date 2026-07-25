# =============================================================================
# graphs/nodes/planner_node.py
#
# LangGraph node wrapping the PlannerAgent.
# =============================================================================

import logging
from langchain_openai import ChatOpenAI
from graphs.state import GraphState
from agents.planner_agent import PlannerAgent
from graphs.memory import MemoryManager, InMemoryShortTermMemory, InMemoryLongTermMemory

log = logging.getLogger(__name__)

async def planner_node(state: GraphState) -> GraphState:
    log.info(f"Executing planner_node for session: {state.get('session_id')}")
    
    # Initialize real agent and memory manager
    llm = ChatOpenAI(model="gpt-4o", temperature=0.1)
    memory = MemoryManager(InMemoryShortTermMemory(), InMemoryLongTermMemory())
    agent = PlannerAgent(llm, memory)
    
    plan = await agent.generate_plan(state)
    
    return {
        "current_node": "planner_node",
        "task_plan": plan
    }
