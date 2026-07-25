# =============================================================================
# backend/tools/model_evaluator.py
#
# Deterministic engine to calculate robust test set metrics for ML models.
# =============================================================================

import os
import joblib
import logging
import numpy as np
from typing import Dict, Any, List

from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score, 
    roc_auc_score, confusion_matrix,
    mean_absolute_error, mean_squared_error, r2_score, mean_absolute_percentage_error
)

log = logging.getLogger(__name__)

class ModelEvaluator:
    def __init__(self, artifact_dir: str = "artifacts/models"):
        self.artifact_dir = artifact_dir

    def evaluate_models(self, model_paths: List[str], problem_type: str) -> Dict[str, Any]:
        """
        Loads the hold-out test set and calculates metrics for all provided models.
        """
        x_test_path = os.path.join(self.artifact_dir, "X_test.joblib")
        y_test_path = os.path.join(self.artifact_dir, "y_test.joblib")
        
        is_clustering = problem_type.lower() == "clustering"
        
        if not os.path.exists(x_test_path) or (not is_clustering and not os.path.exists(y_test_path)):
            raise FileNotFoundError("Hold-out test sets not found. Ensure ModelTrainer ran successfully.")
            
        X_test = joblib.load(x_test_path)
        y_test = joblib.load(y_test_path) if not is_clustering else None
        
        results = {}
        
        for model_path in model_paths:
            if not os.path.exists(model_path):
                log.warning(f"Model file {model_path} not found. Skipping.")
                continue
                
            model_name = os.path.basename(model_path).replace("_best.joblib", "")
            model = joblib.load(model_path)
            
            y_pred = model.predict(X_test) if not is_clustering else None
            metrics = {}
            
            if is_clustering:
                metrics["inertia"] = float(getattr(model, "inertia_", 0.0))
            elif problem_type.lower() == "classification":
                metrics["accuracy"] = float(accuracy_score(y_test, y_pred))
                metrics["precision"] = float(precision_score(y_test, y_pred, average='weighted', zero_division=0))
                metrics["recall"] = float(recall_score(y_test, y_pred, average='weighted', zero_division=0))
                metrics["f1_score"] = float(f1_score(y_test, y_pred, average='weighted', zero_division=0))
                
                # ROC AUC requires probabilities
                if hasattr(model, "predict_proba"):
                    y_prob = model.predict_proba(X_test)
                    try:
                        # Handle multi-class vs binary
                        if y_prob.shape[1] > 2:
                            metrics["roc_auc"] = float(roc_auc_score(y_test, y_prob, multi_class='ovr', average='weighted'))
                        else:
                            metrics["roc_auc"] = float(roc_auc_score(y_test, y_prob[:, 1]))
                    except Exception as e:
                        log.warning(f"ROC AUC failed for {model_name}: {e}")
                        metrics["roc_auc"] = None
                
                # Confusion Matrix
                cm = confusion_matrix(y_test, y_pred)
                metrics["confusion_matrix"] = cm.tolist()
                
            else:
                metrics["mae"] = float(mean_absolute_error(y_test, y_pred))
                metrics["rmse"] = float(np.sqrt(mean_squared_error(y_test, y_pred)))
                metrics["r2"] = float(r2_score(y_test, y_pred))
                metrics["mape"] = float(mean_absolute_percentage_error(y_test, y_pred))
                
            results[model_name] = metrics
            
        return results
