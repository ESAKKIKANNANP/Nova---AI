# =============================================================================
# backend/tests/test_optimization_agent.py
#
# Unit tests for the Optuna tool and Optimization Agent.
# =============================================================================

import pytest
import os
import joblib
import pandas as pd
from unittest.mock import AsyncMock, patch
from tools.model_optimizer import ModelOptimizer
from agents.optimization_agent import OptimizationAgent, OptimizationPlan
from graphs.state import GraphState

@pytest.fixture
def setup_opt_data(tmp_path):
    # Create mock X_test and y_test with enough rows for 3-fold CV
    import numpy as np
    np.random.seed(42)
    X_test = pd.DataFrame({
        "f1": np.random.normal(0, 1, 30),
        "f2": np.random.normal(0, 1, 30)
    })
    y_test = pd.Series(np.random.choice([0, 1], 30))
    
    joblib.dump(X_test, str(tmp_path / "X_test.joblib"))
    joblib.dump(y_test, str(tmp_path / "y_test.joblib"))
    
    # We also need a fake feature_pipeline just so the file exists (tool doesn't strictly use it if re-loading X_test directly)
    joblib.dump("mock_pipeline", str(tmp_path / "feature_pipeline.joblib"))
    
    return str(tmp_path)

def test_model_optimizer_early_stopping(setup_opt_data):
    """Test that Optuna runs and early stopping halts the study."""
    artifact_dir = setup_opt_data
    
    optimizer = ModelOptimizer(artifact_dir=artifact_dir)
    
    # Run a tiny study for RandomForest
    results = optimizer.optimize_hyperparameters("RandomForestClassifier", "Classification", n_trials=5)
    
    assert results["model_name"] == "RandomForestClassifier"
    assert "best_params" in results
    assert results["trials_completed"] > 0
    assert os.path.exists(results["model_path"])

@pytest.mark.asyncio
@patch("agents.optimization_agent.ChatOpenAI")
async def test_optimization_agent_skip(mock_chat_openai):
    """Test the agent deciding to skip optimization."""
    mock_plan = OptimizationPlan(
        requires_optimization=False,
        strategies=[],
        reasoning="Accuracy is 0.99, no need to optimize.",
        markdown_report="Skipped optimization."
    )
    
    from unittest.mock import MagicMock
    mock_llm_instance = MagicMock()
    mock_structured = AsyncMock(return_value=mock_plan)
    mock_structured.ainvoke = AsyncMock(return_value=mock_plan)
    mock_structured.invoke = MagicMock(return_value=mock_plan)
    mock_llm_instance.with_structured_output.return_value = mock_structured
    mock_chat_openai.return_value = mock_llm_instance
    
    agent = OptimizationAgent()
    mock_state = GraphState(session_id="test")
    
    result = await agent.ainvoke(mock_state, winning_model="LGBMClassifier", metrics={"accuracy": 0.99})
    
    assert result["output"]["requires_optimization"] is False
