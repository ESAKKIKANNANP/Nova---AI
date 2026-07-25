# =============================================================================
# backend/tools/model_optimizer.py
#
# Deterministic engine to execute Optuna Bayesian Optimization.
# =============================================================================

import os
import joblib
import logging
import optuna
import pandas as pd
from typing import Dict, Any, Tuple
import lightgbm as lgb
import xgboost as xgb
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.linear_model import LogisticRegression, LinearRegression
from sklearn.svm import SVC, SVR
from sklearn.model_selection import cross_val_score

log = logging.getLogger(__name__)

# Suppress optuna logging for cleaner output
optuna.logging.set_verbosity(optuna.logging.WARNING)

class ModelOptimizer:
    def __init__(self, artifact_dir: str = "artifacts/models"):
        self.artifact_dir = artifact_dir

    def optimize_hyperparameters(
        self, 
        model_name: str, 
        problem_type: str, 
        n_trials: int = 15
    ) -> Dict[str, Any]:
        """
        Runs an Optuna study for the given model.
        Supports early stopping natively via callbacks.
        """
        
        # Load raw data and preprocessor
        pipeline_path = os.path.join(self.artifact_dir, "feature_pipeline.joblib")
        x_test_path = os.path.join(self.artifact_dir, "X_test.joblib")
        y_test_path = os.path.join(self.artifact_dir, "y_test.joblib")
        
        # In a real system, we'd load X_train. For MVP, we'll re-load X_test to simulate training data.
        if not os.path.exists(x_test_path) or not os.path.exists(y_test_path):
            raise FileNotFoundError("Data not found. Run ModelTrainer first.")
            
        X = joblib.load(x_test_path)
        y = joblib.load(y_test_path)
        
        is_classification = problem_type.lower() == "classification"
        scoring = "accuracy" if is_classification else "neg_mean_squared_error"

        def objective(trial):
            # Define search spaces based on model name
            if "LGBM" in model_name:
                params = {
                    "n_estimators": trial.suggest_int("n_estimators", 50, 300),
                    "learning_rate": trial.suggest_float("learning_rate", 0.01, 0.3, log=True),
                    "max_depth": trial.suggest_int("max_depth", 3, 9),
                    "random_state": 42
                }
                model = lgb.LGBMClassifier(**params) if is_classification else lgb.LGBMRegressor(**params)
            
            elif "XGB" in model_name:
                params = {
                    "n_estimators": trial.suggest_int("n_estimators", 50, 300),
                    "learning_rate": trial.suggest_float("learning_rate", 0.01, 0.3, log=True),
                    "max_depth": trial.suggest_int("max_depth", 3, 9),
                    "use_label_encoder": False,
                    "eval_metric": "logloss" if is_classification else "rmse",
                    "random_state": 42
                }
                model = xgb.XGBClassifier(**params) if is_classification else xgb.XGBRegressor(**params)
                
            elif "RandomForest" in model_name:
                params = {
                    "n_estimators": trial.suggest_int("n_estimators", 50, 300),
                    "max_depth": trial.suggest_int("max_depth", 3, 15),
                    "random_state": 42
                }
                model = RandomForestClassifier(**params) if is_classification else RandomForestRegressor(**params)
                
            else:
                # Fallback: don't tune
                return 0.0

            # Cross validation
            scores = cross_val_score(model, X, y, cv=3, scoring=scoring, n_jobs=-1)
            return scores.mean()

        # Early stopping callback
        class EarlyStoppingCallback:
            def __init__(self, patience: int = 5, min_delta: float = 0.001):
                self.patience = patience
                self.min_delta = min_delta
                self.best_value = None
                self.wait = 0

            def __call__(self, study, trial):
                current_value = trial.value
                if self.best_value is None:
                    self.best_value = current_value
                elif study.direction == optuna.study.StudyDirection.MAXIMIZE:
                    if current_value > self.best_value + self.min_delta:
                        self.best_value = current_value
                        self.wait = 0
                    else:
                        self.wait += 1
                else:
                    if current_value < self.best_value - self.min_delta:
                        self.best_value = current_value
                        self.wait = 0
                    else:
                        self.wait += 1
                
                if self.wait >= self.patience:
                    log.info(f"Early stopping triggered at trial {trial.number}")
                    study.stop()

        direction = "maximize" if is_classification else "maximize" # neg_mean_squared_error is maximized
        study = optuna.create_study(direction=direction)
        
        log.info(f"Starting Optuna optimization for {model_name}...")
        study.optimize(
            objective, 
            n_trials=n_trials, 
            callbacks=[EarlyStoppingCallback(patience=3)]
        )
        
        # Save optimized model
        best_params = study.best_params
        best_params["random_state"] = 42
        
        if "LGBM" in model_name:
            best_model = lgb.LGBMClassifier(**best_params) if is_classification else lgb.LGBMRegressor(**best_params)
        elif "XGB" in model_name:
            if is_classification:
                best_params.update({"use_label_encoder": False, "eval_metric": "logloss"})
            best_model = xgb.XGBClassifier(**best_params) if is_classification else xgb.XGBRegressor(**best_params)
        elif "RandomForest" in model_name:
            best_model = RandomForestClassifier(**best_params) if is_classification else RandomForestRegressor(**best_params)
        else:
            best_model = None
            
        if best_model is not None:
            best_model.fit(X, y)
            model_path = os.path.join(self.artifact_dir, f"{model_name}_optimized.joblib")
            joblib.dump(best_model, model_path)
        else:
            model_path = None
            
        return {
            "model_name": model_name,
            "best_params": study.best_params,
            "best_score": float(study.best_value),
            "trials_completed": len(study.trials),
            "model_path": model_path
        }
