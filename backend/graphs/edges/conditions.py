# =============================================================================
# graphs/edges/conditions.py
#
# Conditional routing logic for LangGraph.
# =============================================================================

from typing import Literal
from graphs.state import GraphState
import logging

log = logging.getLogger(__name__)

def is_dataset_valid(state: GraphState) -> Literal["continue", "stop"]:
    """
    Checks if the dataset is valid after the Analyzer Node.
    Returns 'stop' if it's completely empty or malformed.
    Returns 'continue' otherwise.
    """
    profile = state.get("data_profile", {})
    
    # E.g., if there are no rows or no columns, it's invalid.
    row_count = profile.get("row_count", 0)
    col_count = profile.get("column_count", 0)
    
    if row_count == 0 or col_count == 0:
        log.warning("Dataset is invalid (0 rows or 0 columns). Routing to STOP.")
        return "stop"
        
    log.info("Dataset is valid. Routing to CONTINUE.")
    return "continue"
