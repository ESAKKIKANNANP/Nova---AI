# =============================================================================
# backend/graphs/nodes/eval_node.py
#
# LangGraph node for executing model evaluation.
# =============================================================================

import logging
from typing import List
from graphs.state import GraphState
from tools.model_evaluator import ModelEvaluator
from agents.evaluation_agent import EvaluationAgent

log = logging.getLogger(__name__)

async def eval_node(state: GraphState) -> GraphState:
    log.info(f"Executing eval_node for session: {state.get('session_id')}")
    
    # 1. Gather all saved models from previous nodes
    train_results = state.get("execution_results", {}).get("train_node", {}).get("training_results", [])
    model_paths = [res["model_path"] for res in train_results if "model_path" in res]
    
    if not model_paths:
        return {"current_node": "eval_node", "error_message": "No trained models found to evaluate."}
        
    problem_type = state.get("data_profile", {}).get("problem_type", "Classification")
    
    # 2. Run deterministic evaluator
    session_id = state.get("session_id", "default")
    import os
    artifact_dir = os.path.join("artifacts", "models", session_id)
    evaluator = ModelEvaluator(artifact_dir=artifact_dir)
    try:
        raw_metrics = evaluator.evaluate_models(model_paths, problem_type)
    except Exception as e:
        log.error(f"Evaluation tool failed: {e}")
        return {"current_node": "eval_node", "error_message": f"Evaluation tool failed: {str(e)}"}
        
    # 3. Generate LLM Report
    agent = EvaluationAgent()
    try:
        agent_output = await agent.ainvoke(state, raw_metrics)
    except Exception as e:
        log.error(f"Evaluation agent failed: {e}")
        return {"current_node": "eval_node", "error_message": f"Evaluation agent failed: {str(e)}"}
        
    markdown_report = agent_output["output"]["markdown_report"]
    
    # Save Report as artifact
    new_artifact = {
        "artifact_id": f"eval-report-{state.get('session_id')}",
        "artifact_type": "report",
        "s3_path": "", # In memory or DB for now
        "mime_type": "text/markdown",
        "title": "Model Evaluation Report",
        "content": markdown_report
    }
    
    return {
        "current_node": "eval_node",
        "artifacts": [new_artifact],
        "agent_outputs": [agent_output],
        "execution_results": {"eval_node": {"raw_metrics": raw_metrics, "summary": agent_output["output"]}}
    }
