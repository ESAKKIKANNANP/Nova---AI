# =============================================================================
# graphs/nodes/train_node.py
#
# Stub node for Model Training.
# =============================================================================

import logging
import pandas as pd
from graphs.state import GraphState
from tools.model_trainer import ModelTrainer
from agents.training_agent import TrainingSummaryAgent
from services.mlflow_service import MLflowService

log = logging.getLogger(__name__)

async def train_node(state: GraphState) -> GraphState:
    log.info(f"Executing train_node for session: {state.get('session_id')}")
    
    # Check for cancellation
    if state.get("is_cancelled"):
        log.warning("Training cancelled by user request.")
        return {"current_node": "train_node", "error_message": "Training cancelled."}
    
    dataset_path = state.get("dataset_path")
    if not dataset_path or not dataset_path.endswith(".csv"):
        return {"current_node": "train_node", "error_message": "Invalid dataset path for training."}
    
    df = pd.DataFrame()
    try:
        df = pd.read_csv(dataset_path)
    except Exception as e:
        return {"current_node": "train_node", "error_message": f"Failed to load data: {e}"}
        
    problem_type = state.get("task_type", "classification")
    target_col = state.get("data_profile", {}).get("target_column")
    
    # Retrieve pipelines and models
    pipeline_path = None
    for art in state.get("artifacts", []):
        if art.get("title") == "Feature Engineering Pipeline (Joblib)":
            pipeline_path = art.get("s3_path")
            break
            
    if not pipeline_path:
        return {"current_node": "train_node", "error_message": "Feature pipeline not found."}
        
    blueprint = state.get("execution_results", {}).get("model_select_node", {}).get("blueprint", {})
    selected_models = blueprint.get("selected_models", [])
    
    session_id = state.get("session_id", "default")
    import os
    artifact_dir = os.path.join("artifacts", "models", session_id)
    trainer = ModelTrainer(artifact_dir=artifact_dir)
    results = []
    
    # Train each model
    for model_info in selected_models:
        model_name = model_info["model_name"]
        search_space = model_info["hyperparameter_search_space"]
        try:
            res = trainer.train_and_evaluate(df, pipeline_path, target_col, problem_type, model_name, search_space)
            results.append(res)
        except Exception as e:
            log.error(f"Failed to train {model_name}: {e}")
            
    if not results:
        return {"current_node": "train_node", "error_message": "All models failed to train."}
        
    # Log to MLflow
    mlflow_svc = MLflowService()
    for res in results:
        try:
            mlflow_svc.log_evaluation_run(
                session_id=state.get("session_id", "default"),
                model_name=res["model_name"],
                model_path=res["model_path"],
                metrics=res["metrics"],
                params=res["best_params"],
                artifact_paths=[pipeline_path] if pipeline_path else []
            )
        except Exception as e:
            log.warning(f"Failed to log {res['model_name']} to MLflow: {e}")
        
    # Generate Summary
    agent = TrainingSummaryAgent()
    summary = await agent.ainvoke(state, results)
    
    winning_model_name = summary["output"]["winning_model"]
    winning_model_path = next((r["model_path"] for r in results if r["model_name"] == winning_model_name), None)
    
    new_artifacts = []
    if winning_model_path:
        new_artifacts.append({
            "artifact_id": f"winning-model-{state.get('session_id')}",
            "artifact_type": "model",
            "s3_path": winning_model_path,
            "mime_type": "application/octet-stream",
            "title": f"Winning Model: {winning_model_name}"
        })
        
    # Format for dynamic model_results state
    model_results = []
    for rank, res in enumerate(results, start=1):
        model_results.append({
            "model_name": res.get("model_name"),
            "params": res.get("best_params", {}),
            "metrics": res.get("metrics", {}),
            "rank": rank
        })
        
    return {
        "current_node": "train_node",
        "artifacts": new_artifacts,
        "agent_outputs": [summary],
        "model_results": model_results,
        "execution_results": {"train_node": {"training_results": results, "summary": summary["output"]}}
    }
