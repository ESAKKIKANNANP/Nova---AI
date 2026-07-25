# =============================================================================
# graphs/nodes/human_review_node.py
#
# Stub node for Human Review wait state.
# =============================================================================

import logging
from graphs.state import GraphState

log = logging.getLogger(__name__)

def human_review_node(state: GraphState) -> GraphState:
    log.info(f"Executing human_review_node for session: {state.get('session_id')}")
    return {
        "current_node": "human_review_node",
        "requires_human": False # Clear flag after processing
    }
