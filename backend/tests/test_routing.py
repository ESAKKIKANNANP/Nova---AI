# =============================================================================
# tests/test_routing.py
#
# Unit tests for the conditional routing in LangGraph.
# =============================================================================

import pytest
from graphs.graphs.main_graph import compile_graph
from graphs.state import create_initial_state
from graphs.checkpointers.postgres_checkpointer import get_memory_checkpointer

@pytest.mark.asyncio
async def test_graph_valid_dataset_routing():
    """
    Test that a valid dataset flows through the entire pipeline:
    Planner -> Analyzer -> Cleaning -> EDA -> Problem Detection -> END.
    """
    checkpointer = get_memory_checkpointer()
    graph = compile_graph(checkpointer=checkpointer)
    
    state = create_initial_state(
        session_id="test-1",
        user_id="user",
        user_goal="Test goal",
        dataset_id="1",
        dataset_path="test.csv"
    )
    
    config = {"configurable": {"thread_id": "thread-1"}}
    final_state = await graph.ainvoke(state, config=config)
    
    # Our stub analyzer_node sets data_profile row_count to 1000
    # so it should pass the is_dataset_valid condition and reach problem_detection_node.
    assert final_state["current_node"] == "problem_detection_node"
    assert final_state["is_complete"] is True
