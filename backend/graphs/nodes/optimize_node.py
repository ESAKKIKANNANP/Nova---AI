# =============================================================================
# backend/graphs/nodes/optimize_node.py
#
# LangGraph node for executing Optuna Bayesian Optimization.
# =============================================================================

import logging
from graphs.state import GraphState
from tools.model_optimizer import ModelOptimizer
from agents.optimization_agent import OptimizationAgent
from services.mlflow_service import MLflowService

log = logging.getLogger(__name__)

async def optimize_node(state: GraphState) -> GraphState:
    log.info(f"Executing optimize_node for session: {state.get('session_id')}")
    
    # 1. Identify the winning model and metrics from the Evaluation Node
    eval_results = state.get("execution_results", {}).get("eval_node", {})
    raw_metrics = eval_results.get("raw_metrics", {})
    
    # Get winning model from training agent summary
    train_summary = state.get("execution_results", {}).get("train_node", {}).get("summary", {})
    winning_model = train_summary.get("winning_model")
    
    if not winning_model or winning_model not in raw_metrics:
        return {"current_node": "optimize_node", "error_message": "Winning model or metrics missing."}
        
    problem_type = state.get("data_profile", {}).get("problem_type", "Classification")
    
    # 2. Ask the Agent if optimization is required
    agent = OptimizationAgent()
    agent_output = await agent.ainvoke(state, winning_model, raw_metrics[winning_model])
    
    plan = agent_output["output"]
    requires_opt = plan.get("requires_optimization", False)
    
    new_artifacts = []
    opt_results = None
    
    # 3. Execute Optuna if required
    if requires_opt:
        log.info(f"Optimization requested for {winning_model}. Launching Optuna...")
        optimizer = ModelOptimizer()
        try:
            opt_results = optimizer.optimize_hyperparameters(winning_model, problem_type, n_trials=10)
            
            # Save the new optimized model as an artifact
            if opt_results.get("model_path"):
                new_artifacts.append({
                    "artifact_id": f"optimized-model-{state.get('session_id')}",
                    "artifact_type": "model",
                    "s3_path": opt_results["model_path"],
                    "mime_type": "application/octet-stream",
                    "title": f"Optimized Model: {winning_model}"
                })
                
                # Log to MLflow
                mlflow_svc = MLflowService()
                try:
                    mlflow_svc.log_evaluation_run(
                        session_id=state.get("session_id", "default"),
                        model_name=f"{winning_model}_optimized",
                        model_path=opt_results["model_path"],
                        metrics={"best_score": opt_results["best_score"]},
                        params=opt_results["best_params"],
                        artifact_paths=[]
                    )
                except Exception as e:
                    log.warning(f"Failed to log optimized model to MLflow: {e}")
                
        except Exception as e:
            log.error(f"Optuna optimization failed: {e}")
            plan["markdown_report"] += f"\n\n**Note**: Optimization failed due to an error: {e}"
            
    # 4. Save Report Artifact
    new_artifacts.append({
        "artifact_id": f"opt-report-{state.get('session_id')}",
        "artifact_type": "report",
        "s3_path": "",
        "mime_type": "text/markdown",
        "title": "Model Optimization Report",
        "content": plan.get("markdown_report", "")
    })
    
    
    # Increment attempt counter
    current_attempts = state.get("optimization_attempts", 0)
    
    return {
        "current_node": "optimize_node",
        "artifacts": new_artifacts,
        "agent_outputs": [agent_output],
        "optimization_attempts": current_attempts + 1,
        "execution_results": {"optimize_node": {"opt_results": opt_results, "plan": plan}}
    }
