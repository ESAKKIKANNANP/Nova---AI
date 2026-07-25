# =============================================================================
# tests/test_graph.py
#
# Tests for the LangGraph foundation.
# =============================================================================

import pytest
from graphs.state import create_initial_state
from graphs.graphs.main_graph import compile_graph
from graphs.checkpointers.postgres_checkpointer import get_memory_checkpointer

@pytest.mark.asyncio
async def test_graph_initialization_and_execution():
    """
    Test that the LangGraph foundation compiles and can execute a simple pass-through.
    Since all nodes are currently stubs, the graph should execute from START to END
    without raising exceptions.
    """
    # 1. Setup Checkpointer
    checkpointer = get_memory_checkpointer()

    # 2. Compile Graph
    graph = compile_graph(checkpointer=checkpointer)
    
    assert graph is not None
    
    # 3. Create Initial State
    initial_state = create_initial_state(
        session_id="test-session-123",
        user_id="test-user-456",
        user_goal="Predict house prices",
        dataset_id="test-dataset-789",
        dataset_path="/tmp/test.csv"
    )

    # 4. Invoke Graph
    config = {"configurable": {"thread_id": "test-thread-1"}}
    
    # Run the graph
    final_state = await graph.ainvoke(initial_state, config=config)
    
    # 5. Assertions
    assert final_state is not None
    assert final_state["session_id"] == "test-session-123"
    
    # Since it's linear and critic_passed defaults to True in the stub:
    # it should have reached the problem_detection_node and set is_complete to True.
    assert final_state["is_complete"] is True
    assert final_state["current_node"] == "problem_detection_node"
