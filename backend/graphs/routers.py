# =============================================================================
# backend/graphs/routers.py
#
# Conditional routing logic for the LangGraph workflow.
# =============================================================================

import logging
from graphs.state import GraphState

log = logging.getLogger(__name__)

def evaluate_performance(state: GraphState) -> str:
    """
    Decides whether to proceed to explainability or loop back to optimization.
    """
    log.info(f"Evaluating performance for routing (Session: {state.get('session_id')})")
    
    # Check attempts
    attempts = state.get("optimization_attempts", 0)
    max_attempts = state.get("max_optimization_attempts", 3)
    
    if attempts >= max_attempts:
        log.info(f"Max optimization attempts ({max_attempts}) reached. Proceeding to explain.")
        return "explain_node"
        
    # Check metrics
    eval_results = state.get("execution_results", {}).get("eval_node", {})
    raw_metrics = eval_results.get("raw_metrics", {})
    
    train_summary = state.get("execution_results", {}).get("train_node", {}).get("summary", {})
    winning_model = train_summary.get("winning_model")
    
    # If the optuna node just ran, it might have saved a new model under {winning_model}_optimized
    opt_model_name = f"{winning_model}_optimized"
    
    # Determine the best available metric
    current_best_score = 0.0
    target = state.get("target_metric_threshold", 0.90)
    problem_type = state.get("data_profile", {}).get("problem_type", "Classification")
    
    # Metric key based on problem type
    metric_key = "accuracy" if problem_type.lower() == "classification" else "r2"
    
    # Check optimized model first
    if opt_model_name in raw_metrics and metric_key in raw_metrics[opt_model_name]:
        current_best_score = raw_metrics[opt_model_name][metric_key]
    elif winning_model in raw_metrics and metric_key in raw_metrics[winning_model]:
        current_best_score = raw_metrics[winning_model][metric_key]
        
    log.info(f"Current best {metric_key}: {current_best_score}. Target: {target}.")
    
    if current_best_score >= target:
        log.info("Target metric achieved! Proceeding to explain.")
        return "explain_node"
    else:
        log.info("Target not met. Routing to optimize.")
        return "optimize_node"
