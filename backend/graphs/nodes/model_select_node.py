# =============================================================================
# graphs/nodes/model_select_node.py
#
# Stub node for Model Selection.
# =============================================================================

import logging
from graphs.state import GraphState
from agents.model_selection_agent import ModelSelectionAgent

log = logging.getLogger(__name__)

async def model_select_node(state: GraphState) -> GraphState:
    log.info(f"Executing model_select_node for session: {state.get('session_id')}")
    
    agent = ModelSelectionAgent()
    agent_output = await agent.ainvoke(state)
    
    # Extract the blueprint which contains the ranked selected_models
    blueprint = agent_output["output"]
    
    return {
        "current_node": "model_select_node",
        "agent_outputs": [agent_output],
        "execution_results": {"model_select_node": {"blueprint": blueprint}}
    }
