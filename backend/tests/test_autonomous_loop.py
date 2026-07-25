# =============================================================================
# backend/tests/test_autonomous_loop.py
#
# Unit tests for conditional routing.
# =============================================================================

import pytest
from graphs.routers import evaluate_performance
from graphs.state import GraphState

def test_evaluate_performance_under_threshold():
    """Test that it routes to optimize when score is below target."""
    state = GraphState(
        session_id="test",
        optimization_attempts=0,
        max_optimization_attempts=3,
        target_metric_threshold=0.90,
        data_profile={"problem_type": "Classification"},
        execution_results={
            "train_node": {"summary": {"winning_model": "LGBMClassifier"}},
            "eval_node": {"raw_metrics": {"LGBMClassifier": {"accuracy": 0.85}}}
        }
    )
    
    route = evaluate_performance(state)
    assert route == "optimize_node"

def test_evaluate_performance_over_threshold():
    """Test that it skips optimization when score hits target."""
    state = GraphState(
        session_id="test",
        optimization_attempts=0,
        max_optimization_attempts=3,
        target_metric_threshold=0.90,
        data_profile={"problem_type": "Classification"},
        execution_results={
            "train_node": {"summary": {"winning_model": "LGBMClassifier"}},
            "eval_node": {"raw_metrics": {"LGBMClassifier": {"accuracy": 0.95}}}
        }
    )
    
    route = evaluate_performance(state)
    assert route == "explain_node"

def test_evaluate_performance_max_attempts():
    """Test that it breaks the loop when max attempts reached."""
    state = GraphState(
        session_id="test",
        optimization_attempts=3, # Max reached
        max_optimization_attempts=3,
        target_metric_threshold=0.95,
        data_profile={"problem_type": "Classification"},
        execution_results={
            "train_node": {"summary": {"winning_model": "LGBMClassifier"}},
            "eval_node": {"raw_metrics": {"LGBMClassifier": {"accuracy": 0.85}}} # Still low
        }
    )
    
    route = evaluate_performance(state)
    assert route == "explain_node"
    
def test_evaluate_performance_optimized_model():
    """Test that it respects the score of the newly optimized model during the loop."""
    state = GraphState(
        session_id="test",
        optimization_attempts=1,
        max_optimization_attempts=3,
        target_metric_threshold=0.90,
        data_profile={"problem_type": "Classification"},
        execution_results={
            "train_node": {"summary": {"winning_model": "LGBMClassifier"}},
            "eval_node": {
                "raw_metrics": {
                    "LGBMClassifier": {"accuracy": 0.85},
                    "LGBMClassifier_optimized": {"accuracy": 0.92} # New score passes!
                }
            }
        }
    )
    
    route = evaluate_performance(state)
    assert route == "explain_node"
