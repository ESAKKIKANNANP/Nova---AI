# =============================================================================
# backend/tests/test_mlflow_service.py
#
# Unit tests for the MLflow Service.
# =============================================================================

import pytest
import os
import joblib
from services.mlflow_service import MLflowService
from sklearn.linear_model import LogisticRegression

@pytest.fixture
def setup_mlflow_data(tmp_path):
    model = LogisticRegression()
    # Need to fit it so MLflow sklearn logger doesn't complain about un-fitted models sometimes
    model.fit([[0, 0], [1, 1]], [0, 1]) 
    model_path = str(tmp_path / "model.joblib")
    joblib.dump(model, model_path)
    
    # Fake artifact
    artifact_path = str(tmp_path / "plot.png")
    with open(artifact_path, "w") as f:
        f.write("fake png data")
        
    db_uri = f"sqlite:///{tmp_path}/mlflow.db"
    
    return db_uri, model_path, artifact_path

def test_mlflow_service_log_run(setup_mlflow_data):
    db_uri, model_path, artifact_path = setup_mlflow_data
    
    service = MLflowService(tracking_uri=db_uri)
    
    metrics = {"accuracy": 0.95, "f1": 0.94}
    params = {"C": 1.0, "max_iter": 100}
    
    run_id = service.log_evaluation_run(
        session_id="test_session",
        model_name="LogisticRegression",
        model_path=model_path,
        metrics=metrics,
        params=params,
        artifact_paths=[artifact_path]
    )
    
    assert run_id is not None
    assert isinstance(run_id, str)
    
    # Assert DB was created
    assert os.path.exists(db_uri.replace("sqlite:///", ""))
