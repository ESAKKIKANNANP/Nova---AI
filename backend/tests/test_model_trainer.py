# =============================================================================
# backend/tests/test_model_trainer.py
#
# Unit tests for the ModelTrainer tool.
# =============================================================================

import pytest
import pandas as pd
import os
import joblib
from tools.model_trainer import ModelTrainer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.compose import ColumnTransformer

@pytest.fixture
def mock_dataset():
    return pd.DataFrame({
        "feature1": [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0],
        "feature2": [8.0, 7.0, 6.0, 5.0, 4.0, 3.0, 2.0, 1.0],
        "target": [0, 1, 0, 1, 0, 1, 0, 1]
    })

@pytest.fixture
def mock_pipeline(tmp_path):
    # Create a simple mock pipeline
    preprocessor = ColumnTransformer(
        transformers=[
            ('num', StandardScaler(), ['feature1', 'feature2'])
        ],
        remainder='drop'
    )
    # Fit it on some dummy data so it's ready
    preprocessor.fit(pd.DataFrame({
        "feature1": [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0],
        "feature2": [8.0, 7.0, 6.0, 5.0, 4.0, 3.0, 2.0, 1.0]
    }))
    
    pipe_path = str(tmp_path / "mock_pipeline.joblib")
    joblib.dump(preprocessor, pipe_path)
    return pipe_path

def test_model_trainer_lgbm(mock_dataset, mock_pipeline, tmp_path):
    """Test that the ModelTrainer can train LGBMClassifier and save it."""
    
    trainer = ModelTrainer(artifact_dir=str(tmp_path))
    
    # Basic search space
    search_space = {
        "n_estimators": [10, 20],
        "learning_rate": [0.1]
    }
    
    result = trainer.train_and_evaluate(
        df=mock_dataset,
        pipeline_path=mock_pipeline,
        target_col="target",
        problem_type="Classification",
        model_name="LGBMClassifier",
        search_space=search_space
    )
    
    assert result["model_name"] == "LGBMClassifier"
    assert "accuracy" in result["metrics"]
    assert "best_params" in result
    
    # Assert model was saved
    assert os.path.exists(result["model_path"])
    
    # Verify we can load it
    loaded_model = joblib.load(result["model_path"])
    assert loaded_model is not None
