# =============================================================================
# backend/tools/pipeline_builder.py
#
# Deterministic Python tool that translates the Agent's JSON blueprint into 
# a scikit-learn ColumnTransformer / Pipeline and saves it via joblib.
# =============================================================================

import pandas as pd
import joblib
import logging
import os
from typing import Dict, Any

from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler, MinMaxScaler, RobustScaler, OneHotEncoder, OrdinalEncoder
from sklearn.impute import SimpleImputer
# TargetEncoder is available in sklearn 1.3+
try:
    from sklearn.preprocessing import TargetEncoder
except ImportError:
    TargetEncoder = None

log = logging.getLogger(__name__)

class PipelineBuilder:
    """
    Builds, fits, and saves a scikit-learn pipeline based on a JSON blueprint.
    """
    def __init__(self, artifact_dir: str = "artifacts/models"):
        self.artifact_dir = artifact_dir
        os.makedirs(self.artifact_dir, exist_ok=True)

    def _get_transformer(self, operation: str) -> Any:
        """Maps JSON operation strings to actual sklearn classes."""
        if operation == "Standard Scaling":
            return Pipeline([("imputer", SimpleImputer(strategy="median")), ("scaler", StandardScaler())])
        elif operation == "MinMax Scaling":
            return Pipeline([("imputer", SimpleImputer(strategy="median")), ("scaler", MinMaxScaler())])
        elif operation == "Robust Scaling":
            return Pipeline([("imputer", SimpleImputer(strategy="median")), ("scaler", RobustScaler())])
        elif operation == "One-Hot Encoding":
            return Pipeline([
                ("imputer", SimpleImputer(strategy="most_frequent")), 
                ("encoder", OneHotEncoder(handle_unknown="ignore", sparse_output=False))
            ])
        elif operation == "Label Encoding":
            return Pipeline([
                ("imputer", SimpleImputer(strategy="most_frequent")), 
                ("encoder", OrdinalEncoder(handle_unknown="use_encoded_value", unknown_value=-1))
            ])
        elif operation == "Target Encoding" and TargetEncoder:
            return Pipeline([
                ("imputer", SimpleImputer(strategy="most_frequent")), 
                ("encoder", TargetEncoder())
            ])
        elif operation == "Missing Value Indicators":
            return SimpleImputer(strategy="constant", fill_value="missing", add_indicator=True)
        else:
            # Fallback for complex ops not directly mappable in this MVP builder
            log.warning(f"Operation '{operation}' not fully supported in MVP builder. Falling back to passthrough.")
            return "passthrough"

    def build_and_fit(self, df: pd.DataFrame, plan: Dict[str, Any], target_col: str = None) -> str:
        """
        Constructs the ColumnTransformer, fits it to df, and saves it.
        Returns the path to the saved joblib pipeline.
        """
        transformers = []
        
        # Pre-filter drop columns
        drop_cols = plan.get("drop_columns", [])
        if target_col and target_col not in drop_cols:
            drop_cols.append(target_col)
            
        for idx, transform in enumerate(plan.get("transformations", [])):
            cols = [c for c in transform["columns"] if c in df.columns and c not in drop_cols]
            if not cols:
                continue
                
            sklearn_transformer = self._get_transformer(transform["operation"])
            name = f"step_{idx}_{transform['operation'].replace(' ', '_').lower()}"
            transformers.append((name, sklearn_transformer, cols))
            
        # Create ColumnTransformer (dropping unspecified columns by default)
        preprocessor = ColumnTransformer(transformers=transformers, remainder="drop")
        
        # Fit the pipeline
        y = df[target_col] if target_col and target_col in df.columns else None
        
        log.info("Fitting scikit-learn pipeline...")
        preprocessor.fit(df, y)
        
        # Save pipeline
        pipeline_path = os.path.join(self.artifact_dir, "feature_pipeline.joblib")
        joblib.dump(preprocessor, pipeline_path)
        log.info(f"Pipeline saved to {pipeline_path}")
        
        return pipeline_path
