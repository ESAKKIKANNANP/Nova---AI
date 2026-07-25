# =============================================================================
# backend/agents/ml_model_registry.py
#
# Config-driven registry mapping task_type to machine learning algorithms,
# parameter grids, and evaluation metrics.
# =============================================================================

from typing import Any, Dict, List

# Registry matching task_type to supported model configurations
MODEL_REGISTRY: Dict[str, Dict[str, Any]] = {
    "classification": {
        "metrics": ["accuracy", "precision", "recall", "f1_score", "roc_auc"],
        "default_metric": "f1_score",
        "models": {
            "XGBClassifier": {
                "class_path": "xgboost.XGBClassifier",
                "param_grid": {
                    "n_estimators": [50, 100, 200],
                    "max_depth": [3, 5, 7],
                    "learning_rate": [0.01, 0.1, 0.2]
                }
            },
            "LGBMClassifier": {
                "class_path": "lightgbm.LGBMClassifier",
                "param_grid": {
                    "n_estimators": [50, 100, 200],
                    "max_depth": [3, 5, -1],
                    "learning_rate": [0.01, 0.1, 0.2]
                }
            },
            "RandomForestClassifier": {
                "class_path": "sklearn.ensemble.RandomForestClassifier",
                "param_grid": {
                    "n_estimators": [50, 100, 200],
                    "max_depth": [None, 10, 20],
                    "min_samples_split": [2, 5]
                }
            },
            "LogisticRegression": {
                "class_path": "sklearn.linear_model.LogisticRegression",
                "param_grid": {
                    "C": [0.1, 1.0, 10.0],
                    "solver": ["lbfgs", "liblinear"]
                }
            }
        }
    },
    "regression": {
        "metrics": ["mae", "mse", "rmse", "r2"],
        "default_metric": "r2",
        "models": {
            "XGBRegressor": {
                "class_path": "xgboost.XGBRegressor",
                "param_grid": {
                    "n_estimators": [50, 100, 200],
                    "max_depth": [3, 5, 7],
                    "learning_rate": [0.01, 0.1, 0.2]
                }
            },
            "LGBMRegressor": {
                "class_path": "lightgbm.LGBMRegressor",
                "param_grid": {
                    "n_estimators": [50, 100, 200],
                    "max_depth": [3, 5, -1],
                    "learning_rate": [0.01, 0.1, 0.2]
                }
            },
            "RandomForestRegressor": {
                "class_path": "sklearn.ensemble.RandomForestRegressor",
                "param_grid": {
                    "n_estimators": [50, 100, 200],
                    "max_depth": [None, 10, 20],
                    "min_samples_split": [2, 5]
                }
            },
            "LinearRegression": {
                "class_path": "sklearn.linear_model.LinearRegression",
                "param_grid": {}
            }
        }
    },
    "clustering": {
        "metrics": ["silhouette_score"],
        "default_metric": "silhouette_score",
        "models": {
            "KMeans": {
                "class_path": "sklearn.cluster.KMeans",
                "param_grid": {
                    "n_clusters": [3, 5, 8],
                    "init": ["k-means++", "random"]
                }
            }
        }
    }
}

def get_supported_models(task_type: str) -> List[str]:
    """Returns the names of all models configured for the given task_type."""
    task = task_type.lower()
    if task not in MODEL_REGISTRY:
        return []
    return list(MODEL_REGISTRY[task]["models"].keys())

def get_model_config(task_type: str, model_name: str) -> Dict[str, Any]:
    """Retrieves class path and param grid for a specific model."""
    task = task_type.lower()
    if task not in MODEL_REGISTRY or model_name not in MODEL_REGISTRY[task]["models"]:
        return {}
    return MODEL_REGISTRY[task]["models"][model_name]
