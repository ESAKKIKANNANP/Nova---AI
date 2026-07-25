# =============================================================================
# backend/tests/test_feature_engineering_agent.py
#
# Unit tests for the Feature Engineering Agent and Pipeline Builder.
# =============================================================================

import pytest
import pandas as pd
import os
from tools.pipeline_builder import PipelineBuilder

def test_pipeline_builder_creation():
    """Test that the deterministic builder successfully creates and saves a pipeline."""
    
    # Mock blueprint from the LLM
    mock_plan = {
        "transformations": [
            {
                "columns": ["age", "monthly_charges"],
                "operation": "Standard Scaling",
                "reasoning": "Numeric columns with normal-ish distribution."
            },
            {
                "columns": ["contract_type"],
                "operation": "One-Hot Encoding",
                "reasoning": "Low cardinality categorical."
            }
        ],
        "drop_columns": ["customer_id"]
    }
    
    # Mock dataset
    df = pd.DataFrame({
        "customer_id": ["C1", "C2", "C3"],
        "age": [25, 45, 65],
        "monthly_charges": [29.99, 59.99, 99.99],
        "contract_type": ["Month-to-month", "One year", "Two year"],
        "churn": ["No", "Yes", "No"]
    })
    
    builder = PipelineBuilder(artifact_dir="backend/tests/fixtures/models")
    pipeline_path = builder.build_and_fit(df, mock_plan, target_col="churn")
    
    assert os.path.exists(pipeline_path), "Pipeline joblib file was not created!"
    
    # Test Loading it
    import joblib
    loaded_pipeline = joblib.load(pipeline_path)
    
    # The pipeline should be able to transform the df
    transformed = loaded_pipeline.transform(df)
    
    # Standard scaling (2 cols) + OHE (3 categories) = 5 columns in output
    assert transformed.shape[1] == 5, f"Expected 5 columns, got {transformed.shape[1]}"
