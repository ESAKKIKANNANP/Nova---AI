# =============================================================================
# graphs/nodes/ingest_node.py
#
# Stub node for Data Ingestion.
# =============================================================================

import logging
from graphs.state import GraphState

log = logging.getLogger(__name__)

def ingest_node(state: GraphState) -> GraphState:
    """
    Ingest the dataset and profile it. (Stub)
    """
    log.info(f"Executing ingest_node for session: {state.get('session_id')}")
    
    # Simulate processing
    current_node = "ingest_node"
    
    # Return partial state update
    return {
        "current_node": current_node,
        "metadata": {"ingest_status": "completed"}
    }
