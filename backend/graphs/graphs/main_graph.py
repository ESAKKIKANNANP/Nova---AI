# =============================================================================
# graphs/graphs/main_graph.py
#
# LangGraph state machine assembly.
# =============================================================================

import logging
from langgraph.graph import StateGraph, START, END

from graphs.state import GraphState
from graphs.nodes.planner_node import planner_node
from graphs.nodes.analyzer_node import analyzer_node
from graphs.nodes.cleaning_node import cleaning_node
from graphs.nodes.eda_node import eda_node
from graphs.nodes.problem_detection_node import problem_detection_node
from graphs.edges.conditions import is_dataset_valid

log = logging.getLogger(__name__)

def build_graph() -> StateGraph:
    """Builds the uncompiled StateGraph representing the AI agent workflow."""
    builder = StateGraph(GraphState)
    
    # 1. Add Nodes
    builder.add_node("planner_node", planner_node)
    builder.add_node("analyzer_node", analyzer_node)
    builder.add_node("cleaning_node", cleaning_node)
    builder.add_node("eda_node", eda_node)
    builder.add_node("problem_detection_node", problem_detection_node)
    
    # 2. Define Edges (The Workflow)
    # Start -> Planner
    builder.add_edge(START, "planner_node")
    
    # Planner -> Analyzer
    builder.add_edge("planner_node", "analyzer_node")
    
    # Analyzer -> Conditional Routing (Valid?)
    builder.add_conditional_edges(
        "analyzer_node",
        is_dataset_valid,
        {
            "continue": "cleaning_node",
            "stop": END
        }
    )
    
    # Cleaning -> EDA
    builder.add_edge("cleaning_node", "eda_node")
    
    # EDA -> Problem Detection
    builder.add_edge("eda_node", "problem_detection_node")
    
    # Problem Detection -> END
    builder.add_edge("problem_detection_node", END)
    
    return builder

def compile_graph(checkpointer=None):
    """Compiles the StateGraph with an optional checkpointer."""
    builder = build_graph()
    graph = builder.compile(checkpointer=checkpointer)
    log.info("Successfully compiled main graph workflow.")
    return graph
