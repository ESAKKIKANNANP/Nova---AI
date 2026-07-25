# =============================================================================
# backend/services/mlflow_service.py
#
# Centralized MLOps service for logging runs, models, and artifacts to MLflow.
# =============================================================================

import os
import logging
import joblib
import mlflow
import mlflow.sklearn
import mlflow.xgboost
import mlflow.lightgbm
from typing import Dict, Any, List

log = logging.getLogger(__name__)

class MLflowService:
    def __init__(self, tracking_uri: str = "sqlite:///mlflow.db"):
        """
        Initializes MLflow backend. For MVP, we use local SQLite to support Model Registry.
        """
        # Ensure directory for sqlite db exists
        os.makedirs("mlruns", exist_ok=True)
        
        mlflow.set_tracking_uri(tracking_uri)
        log.info(f"Connected to MLflow Tracking Server at {tracking_uri}")

    def get_or_create_experiment(self, experiment_name: str) -> str:
        """Returns experiment ID, creating it if necessary."""
        exp = mlflow.get_experiment_by_name(experiment_name)
        if exp is None:
            return mlflow.create_experiment(experiment_name)
        return exp.experiment_id

    def log_evaluation_run(
        self, 
        session_id: str,
        model_name: str, 
        model_path: str,
        metrics: Dict[str, float], 
        params: Dict[str, Any],
        artifact_paths: List[str] = None
    ) -> str:
        """
        Logs a single model evaluation run to MLflow.
        """
        exp_id = self.get_or_create_experiment(f"Session_{session_id}")
        
        with mlflow.start_run(experiment_id=exp_id, run_name=model_name) as run:
            # 1. Log Parameters
            clean_params = {k: str(v) for k, v in params.items()}
            mlflow.log_params(clean_params)
            
            # 2. Log Metrics (Filter out non-numeric like confusion matrix)
            numeric_metrics = {k: v for k, v in metrics.items() if isinstance(v, (int, float))}
            mlflow.log_metrics(numeric_metrics)
            
            # 3. Log external artifacts (SHAP plots, Markdown reports, feature pipelines)
            if artifact_paths:
                for path in artifact_paths:
                    if os.path.exists(path):
                        mlflow.log_artifact(path)
                        
            # 4. Log and Register the Model itself
            if os.path.exists(model_path):
                model = joblib.load(model_path)
                # Register based on model type
                if "XGB" in model_name:
                    mlflow.xgboost.log_model(model, artifact_path="model", registered_model_name=f"{session_id}_{model_name}")
                elif "LGBM" in model_name:
                    mlflow.lightgbm.log_model(model, artifact_path="model", registered_model_name=f"{session_id}_{model_name}")
                else:
                    mlflow.sklearn.log_model(model, artifact_path="model", registered_model_name=f"{session_id}_{model_name}")
                    
            log.info(f"Successfully logged run {run.info.run_id} to MLflow.")
            return run.info.run_id
