# =============================================================================
# backend/tools/model_trainer.py
#
# Deterministic engine to execute ML training, cross validation, and saving.
# =============================================================================

import os
import joblib
import logging
import pandas as pd
import numpy as np
from typing import Dict, Any, Tuple

from sklearn.model_selection import train_test_split, RandomizedSearchCV
from sklearn.metrics import accuracy_score, f1_score, mean_squared_error, r2_score

# Dynamically import algorithms
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.linear_model import LogisticRegression, LinearRegression
from sklearn.svm import SVC, SVR
from sklearn.cluster import KMeans
import xgboost as xgb
import lightgbm as lgb
# Note: CatBoost and Prophet are omitted here for brevity but can be added similarly.

log = logging.getLogger(__name__)

class ModelTrainer:
    def __init__(self, artifact_dir: str = "artifacts/models"):
        self.artifact_dir = artifact_dir
        os.makedirs(self.artifact_dir, exist_ok=True)
        
    def _get_model_instance(self, model_name: str) -> Any:
        mapping = {
            "RandomForestClassifier": RandomForestClassifier(random_state=42),
            "XGBClassifier": xgb.XGBClassifier(random_state=42, use_label_encoder=False, eval_metric="logloss"),
            "LGBMClassifier": lgb.LGBMClassifier(random_state=42),
            "LogisticRegression": LogisticRegression(random_state=42, max_iter=1000),
            "SVC": SVC(random_state=42),
            "RandomForestRegressor": RandomForestRegressor(random_state=42),
            "XGBRegressor": xgb.XGBRegressor(random_state=42),
            "LGBMRegressor": lgb.LGBMRegressor(random_state=42),
            "LinearRegression": LinearRegression(),
            "SVR": SVR(),
            "KMeans": KMeans(random_state=42, n_init="auto")
        }
        if model_name not in mapping:
            raise ValueError(f"Model {model_name} is not supported by the ModelTrainer.")
        return mapping[model_name]

    def train_and_evaluate(
        self, 
        df: pd.DataFrame, 
        pipeline_path: str, 
        target_col: str, 
        problem_type: str, 
        model_name: str, 
        search_space: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Executes the entire training flow for a single algorithm.
        """
        log.info(f"Starting training for {model_name}...")
        
        # 1. Load Preprocessor Pipeline
        if not os.path.exists(pipeline_path):
            raise FileNotFoundError(f"Feature pipeline not found at {pipeline_path}")
        preprocessor = joblib.load(pipeline_path)
        
        # 2. Split Data
        if target_col:
            X = df.drop(columns=[target_col])
            y = df[target_col]
            X_processed = preprocessor.transform(X)
            X_train, X_test, y_train, y_test = train_test_split(
                X_processed, y, test_size=0.2, random_state=42, 
                stratify=y if problem_type.lower() == "classification" else None
            )
        else:
            X = df
            y = None
            X_processed = preprocessor.transform(X)
            X_train, X_test = train_test_split(X_processed, test_size=0.2, random_state=42)
            y_train, y_test = None, None
        
        # Save test sets for the Evaluation Agent
        joblib.dump(X_test, os.path.join(self.artifact_dir, "X_test.joblib"))
        if y_test is not None:
            joblib.dump(y_test, os.path.join(self.artifact_dir, "y_test.joblib"))
        
        # 3. Instantiate base model
        base_model = self._get_model_instance(model_name)
        
        # 4. Cross Validation & Hyperparameter Tuning
        if y_train is not None:
            if search_space:
                n_samples = len(X_train)
                if problem_type.lower() == "classification":
                    min_class_count = int(pd.Series(y_train).value_counts().min())
                    max_cv = min(n_samples, min_class_count)
                else:
                    max_cv = n_samples
                    
                cv_splits = min(5 if problem_type.lower() == "classification" else 3, max_cv)
                
                if cv_splits < 2:
                    best_model = base_model
                    best_model.fit(X_train, y_train)
                    best_params = {}
                else:
                    # Limit n_iter to parameter grid space size if it is smaller than 5
                    import math
                    grid_size = math.prod(len(v) for v in search_space.values()) if search_space else 1
                    search = RandomizedSearchCV(
                        estimator=base_model,
                        param_distributions=search_space,
                        n_iter=min(5, grid_size),
                        cv=cv_splits,
                        random_state=42,
                        n_jobs=-1
                    )
                    search.fit(X_train, y_train)
                    best_model = search.best_estimator_
                    best_params = search.best_params_
            else:
                best_model = base_model
                best_model.fit(X_train, y_train)
                best_params = {}
        else:
            best_model = base_model
            best_model.fit(X_train)
            best_params = {}
        
        # 5. Evaluate on Test Set
        metrics = {}
        if problem_type.lower() == "classification" and y_test is not None:
            y_pred = best_model.predict(X_test)
            metrics["accuracy"] = float(accuracy_score(y_test, y_pred))
            metrics["f1_score"] = float(f1_score(y_test, y_pred, average='weighted'))
        elif y_test is not None:
            y_pred = best_model.predict(X_test)
            metrics["rmse"] = float(np.sqrt(mean_squared_error(y_test, y_pred)))
            metrics["r2"] = float(r2_score(y_test, y_pred))
        else:
            # Clustering metrics (e.g. silhouette or inertia)
            metrics["inertia"] = float(getattr(best_model, "inertia_", 0.0))
            
        # 6. Save Winning Model
        model_path = os.path.join(self.artifact_dir, f"{model_name}_best.joblib")
        joblib.dump(best_model, model_path)
        
        log.info(f"Finished {model_name}. Best params: {best_params}")
        
        return {
            "model_name": model_name,
            "metrics": metrics,
            "best_params": best_params,
            "model_path": model_path
        }
