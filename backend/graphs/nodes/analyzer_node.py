# =============================================================================
# graphs/nodes/analyzer_node.py
#
# LangGraph node wrapping the Dataset Analyzer Agent.
# =============================================================================

import logging
from graphs.state import GraphState

from langchain_openai import ChatOpenAI
from agents.analyzer_agent import AnalyzerAgent
from agents.business_intelligence_agent import BusinessIntelligenceAgent

log = logging.getLogger(__name__)

async def analyzer_node(state: GraphState) -> GraphState:
    log.info(f"Executing analyzer_node for session: {state.get('session_id')}")
    
    llm = ChatOpenAI(model="gpt-4o", temperature=0.1)
    agent = AnalyzerAgent(llm)
    agent_output = await agent.generate_profile(state)
    
    # Run Agent 2 to infer business context
    temp_state = dict(state)
    temp_state["data_profile"] = agent_output["data_profile"]
    bi_agent = BusinessIntelligenceAgent()
    business_context = await bi_agent.infer_context(temp_state)
    
    return {
        "current_node": "analyzer_node",
        "data_profile": agent_output["data_profile"],
        "business_context": business_context,
        "metadata": agent_output["metadata"]
    }
