# =============================================================================
# backend/graphs/nodes/explain_node.py
#
# LangGraph node for executing model explainability and generating business reports.
# =============================================================================

import logging
from graphs.state import GraphState
from tools.model_explainer import ModelExplainer
from agents.explainability_agent import ExplainabilityAgent

log = logging.getLogger(__name__)

async def explain_node(state: GraphState) -> GraphState:
    log.info(f"Executing explain_node for session: {state.get('session_id')}")
    
    # 1. Identify the optimized/winning model
    winning_model = None
    
    opt_results = state.get("execution_results", {}).get("optimize_node", {}).get("opt_results", {})
    if opt_results:
        winning_model = opt_results.get("model_name")
        
    if not winning_model:
        train_summary = state.get("execution_results", {}).get("train_node", {}).get("summary", {})
        winning_model = train_summary.get("winning_model")
        
    if not winning_model:
        return {"current_node": "explain_node", "error_message": "Winning model not found for explainability."}
        
    problem_type = state.get("data_profile", {}).get("problem_type", "Classification")
    
    # 2. Run deterministic explainer to get math metrics and plots
    session_id = state.get("session_id", "default")
    import os
    artifact_dir = os.path.join("artifacts", "models", session_id)
    explainer = ModelExplainer(artifact_dir=artifact_dir)
    try:
        explanation_data = explainer.generate_explanations(winning_model, problem_type)
    except Exception as e:
        log.error(f"Explainer tool failed: {e}")
        return {"current_node": "explain_node", "error_message": f"Explainer tool failed: {str(e)}"}
        
    # Add plot artifacts
    new_artifacts = []
    for plot_path in explanation_data.get("plots", []):
        new_artifacts.append({
            "artifact_id": f"plot-{plot_path.split('/')[-1]}-{state.get('session_id')}",
            "artifact_type": "image",
            "s3_path": plot_path,
            "mime_type": "image/png",
            "title": f"Explanation Plot: {plot_path.split('/')[-1]}"
        })
        
    # 3. Generate LLM Business Report
    agent = ExplainabilityAgent()
    try:
        agent_output = await agent.ainvoke(state, explanation_data["feature_importance"])
    except Exception as e:
        log.error(f"Explainability agent failed: {e}")
        return {"current_node": "explain_node", "error_message": f"Explainability agent failed: {str(e)}"}
        
    markdown_report = agent_output["output"]["markdown_report"]
    
    # Save Report Artifact
    new_artifacts.append({
        "artifact_id": f"explain-report-{state.get('session_id')}",
        "artifact_type": "report",
        "s3_path": "",
        "mime_type": "text/markdown",
        "title": "Executive Explainability Report",
        "content": markdown_report
    })
    
    return {
        "current_node": "explain_node",
        "artifacts": new_artifacts,
        "agent_outputs": [agent_output],
        "execution_results": {"explain_node": {"explanation_data": explanation_data, "business_summary": agent_output["output"]}}
    }
