# =============================================================================
# graphs/nodes/problem_detection_node.py
#
# LangGraph node wrapping the Problem Detection Agent.
# =============================================================================

import logging
from graphs.state import GraphState
from agents.problem_detection_agent import ProblemDetectionAgent
from langchain_openai import ChatOpenAI

log = logging.getLogger(__name__)

async def problem_detection_node(state: GraphState) -> GraphState:
    log.info(f"Executing problem_detection_node for session: {state.get('session_id')}")
    
    # Instantiate LLM and Agent
    llm = ChatOpenAI(model="gpt-4o", temperature=0.1)
    agent = ProblemDetectionAgent(llm)
    agent_output = await agent.detect_problem(state)
    
    # Determine normalized task_type
    prob_type = agent_output["data_profile"]["problem_type"].lower()
    if "time series" in prob_type:
        task_type = "time_series"
    elif "clustering" in prob_type:
        task_type = "clustering"
    elif "regression" in prob_type:
        task_type = "regression"
    else:
        task_type = "classification"
        
    return {
        "current_node": "problem_detection_node",
        "data_profile": agent_output["data_profile"],
        "task_type": task_type,
        "execution_results": agent_output["execution_results"]
    }
