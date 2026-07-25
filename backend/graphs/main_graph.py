# =============================================================================
# backend/graphs/main_graph.py
#
# Master LangGraph assembly wiring all agents and deterministic tools together.
# =============================================================================

import os
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from graphs.state import GraphState
from graphs.routers import evaluate_performance

# Import all nodes created across Phase 1 and 2
from graphs.nodes.planner_node import planner_node
from graphs.nodes.analyzer_node import analyzer_node
from graphs.nodes.cleaning_node import cleaning_node
from graphs.nodes.eda_node import eda_node
from graphs.nodes.problem_detection_node import problem_detection_node
from graphs.nodes.feature_node import feature_node
from graphs.nodes.model_select_node import model_select_node
from graphs.nodes.train_node import train_node
from graphs.nodes.eval_node import eval_node
from graphs.nodes.optimize_node import optimize_node
from graphs.nodes.explain_node import explain_node
from graphs.nodes.insight_node import insight_node
from graphs.nodes.report_node import report_node

def build_graph():
    """
    Constructs the master Autonomous Data Scientist pipeline.
    """
    workflow = StateGraph(GraphState)

    # 1. Add all nodes
    workflow.add_node("planner_node", planner_node)
    workflow.add_node("analyzer_node", analyzer_node)
    workflow.add_node("cleaning_node", cleaning_node)
    workflow.add_node("eda_node", eda_node)
    workflow.add_node("problem_detection_node", problem_detection_node)
    workflow.add_node("feature_node", feature_node)
    workflow.add_node("model_select_node", model_select_node)
    workflow.add_node("train_node", train_node)
    workflow.add_node("eval_node", eval_node)
    workflow.add_node("optimize_node", optimize_node)
    workflow.add_node("explain_node", explain_node)
    workflow.add_node("insight_node", insight_node)
    workflow.add_node("report_node", report_node)

    # 2. Define the Linear Phase 1 Flow
    workflow.set_entry_point("planner_node")
    workflow.add_edge("planner_node", "analyzer_node")
    workflow.add_edge("analyzer_node", "cleaning_node")
    workflow.add_edge("cleaning_node", "eda_node")
    workflow.add_edge("eda_node", "problem_detection_node")
    
    # 3. Define the Linear Phase 2 Flow
    workflow.add_edge("problem_detection_node", "feature_node")
    workflow.add_edge("feature_node", "model_select_node")
    workflow.add_edge("model_select_node", "train_node")
    workflow.add_edge("train_node", "eval_node")
    
    # 4. The Autonomous Cyclic Decision Loop
    workflow.add_conditional_edges(
        "eval_node",
        evaluate_performance,
        {
            "optimize_node": "optimize_node",
            "explain_node": "explain_node"
        }
    )
    
    # Loop back from optimize to eval to score the new model
    workflow.add_edge("optimize_node", "eval_node")
    
    # 5. Insight Node
    workflow.add_edge("explain_node", "insight_node")
    
    # 6. Report Generation
    workflow.add_edge("insight_node", "report_node")
    
    # 7. End Pipeline
    workflow.add_edge("report_node", END)

    # Compile with memory for checkpointer support
    memory = MemorySaver()
    app = workflow.compile(checkpointer=memory)
    
    return app

if __name__ == "__main__":
    app = build_graph()
    print("Graph successfully compiled.")
