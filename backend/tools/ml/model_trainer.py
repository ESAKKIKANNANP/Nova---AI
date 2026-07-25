# =============================================================================
# backend/tools/ml/model_trainer.py
#
# ML Tool: Automatic training and evaluation of Classification and Regression models.
# =============================================================================

from typing import Any, Dict, List, Optional
import pandas as pd
import numpy as np
from pydantic import BaseModel, Field

from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score, confusion_matrix,
    mean_absolute_error, mean_squared_error, r2_score
)

from tools.base import BaseTool


class ModelTrainerInput(BaseModel):
    data: List[Dict[str, Any]] = Field(
        ...,
        description="Dataset training rows as a list of dictionaries.",
    )
    target_column: str = Field(
        ...,
        description="Name of the target/label column to predict.",
    )
    task_type: str = Field(
        default="auto",
        description="Type of task: classification, regression, or auto (auto-detects based on target column datatype).",
    )
    exclude_columns: Optional[List[str]] = Field(
        default=None,
        description="Optional list of columns to drop / exclude from training features.",
    )
    test_size: float = Field(
        default=0.2,
        description="Proportion of the dataset to include in the test split (0.1 to 0.9).",
    )


class ModelTrainerTool(BaseTool):
    """
    Tool that prepares features, splits dataset, trains a baseline RandomForest model,
    evaluates it on test data, and computes metrics and feature importances.
    """
    name = "model_trainer"
    description = "Trains and evaluates a machine learning model on a dataset. Returns evaluation metrics and feature importances."
    args_schema = ModelTrainerInput

    def _run(
        self,
        data: List[Dict[str, Any]],
        target_column: str,
        task_type: str = "auto",
        exclude_columns: Optional[List[str]] = None,
        test_size: float = 0.2,
    ) -> Dict[str, Any]:
        # 1. Validation & Data Prep
        if not data:
            raise ValueError("Training dataset cannot be empty.")
        
        df = pd.DataFrame(data)
        if target_column not in df.columns:
            raise ValueError(f"Target column '{target_column}' is missing from the dataset.")

        # Exclude features
        if exclude_columns is None:
            exclude_columns = []
        
        # Always exclude the target itself from features
        exclude_columns.append(target_column)
        
        # Prepare target variable (remove NaNs)
        df = df.dropna(subset=[target_column])
        
        y = df[target_column]
        X = df.drop(columns=[col for col in exclude_columns if col in df.columns])

        # Auto-detect task type
        if task_type == "auto":
            if y.dtype in (np.number, np.float64, np.int64) and y.nunique() > 10:
                task_type = "regression"
            else:
                task_type = "classification"

        # Preprocess features: Convert categorical variables via one-hot encoding, fill NaNs
        X = pd.get_dummies(X, drop_first=True)
        # Simple imputation for remaining missing values
        for col in X.columns:
            if X[col].isnull().any():
                fill_value = X[col].median() if pd.api.types.is_numeric_dtype(X[col]) else X[col].mode()[0]
                X[col] = X[col].fillna(fill_value)

        # Split data
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=test_size, random_state=42)

        # 3. Model Training & Scoring
        metrics: Dict[str, Any] = {}
        feature_importances: Dict[str, float] = {}

        if task_type == "classification":
            # Train RandomForestClassifier
            model = RandomForestClassifier(n_estimators=100, random_state=42)
            model.fit(X_train, y_train)
            
            predictions = model.predict(X_test)
            
            # Compute classification metrics
            unique_classes = np.unique(y_test)
            average_strategy = "macro"

            metrics["accuracy"] = float(accuracy_score(y_test, predictions))
            metrics["precision"] = float(precision_score(y_test, predictions, average=average_strategy, zero_division=0))
            metrics["recall"] = float(recall_score(y_test, predictions, average=average_strategy, zero_division=0))
            metrics["f1_score"] = float(f1_score(y_test, predictions, average=average_strategy, zero_division=0))
            
            # Confusion matrix
            cm = confusion_matrix(y_test, predictions)
            metrics["confusion_matrix"] = cm.tolist()
            metrics["classes"] = [str(c) for c in unique_classes]

        elif task_type == "regression":
            # Train RandomForestRegressor
            model = RandomForestRegressor(n_estimators=100, random_state=42)
            model.fit(X_train, y_train)
            
            predictions = model.predict(X_test)
            
            # Compute regression metrics
            mae = mean_absolute_error(y_test, predictions)
            mse = mean_squared_error(y_test, predictions)
            rmse = np.sqrt(mse)
            r2 = r2_score(y_test, predictions)
            
            # Mean Absolute Percentage Error
            with np.errstate(divide="ignore", invalid="ignore"):
                mape = np.mean(np.abs((y_test - predictions) / y_test)) * 100
                if np.isinf(mape) or np.isnan(mape):
                    mape = None

            metrics["mean_absolute_error"] = float(mae)
            metrics["mean_squared_error"] = float(mse)
            metrics["root_mean_squared_error"] = float(rmse)
            metrics["r2_score"] = float(r2)
            metrics["mean_absolute_percentage_error"] = float(mape) if mape is not None else None
        else:
            raise ValueError(f"Unknown task_type: {task_type}. Use classification, regression, or auto.")

        # Compute feature importances
        importances = model.feature_importances_
        indices = np.argsort(importances)[::-1]
        
        for idx in indices:
            feature_importances[str(X.columns[idx])] = float(importances[idx])

        return {
            "task_type": task_type,
            "metrics": metrics,
            "feature_importances": feature_importances,
            "feature_count": len(X.columns),
            "sample_counts": {
                "total": len(df),
                "train": len(X_train),
                "test": len(X_test)
            }
        }
