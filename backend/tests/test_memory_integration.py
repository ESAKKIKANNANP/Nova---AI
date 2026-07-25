# =============================================================================
# tests/test_memory_integration.py
#
# Unit tests proving that LangGraph memory works correctly per project
# and recovers state across multiple invocations.
# =============================================================================

import pytest
import uuid
from services.pipeline_service import PipelineService
from graphs.checkpointers.postgres_checkpointer import get_memory_checkpointer

@pytest.mark.asyncio
async def test_per_project_memory_isolation_and_recovery():
    """
    Test that memory is isolated per project and state is fully retained
    across multiple pipeline invocations (simulating restarts).
    """
    # 1. Setup shared checkpointer to simulate the persistence layer
    shared_checkpointer = get_memory_checkpointer()
    service = PipelineService(checkpointer=shared_checkpointer)
    
    project_id = str(uuid.uuid4())
    
    # 2. First Invocation (New Session)
    dataset_meta = {"dataset_id": "ds-1", "dataset_path": "/fake/path.csv"}
    
    # Run the first pass
    final_state_1 = await service.invoke_pipeline(
        project_id=project_id,
        user_input="Analyze this dataset.",
        is_new_session=True,
        dataset_meta=dataset_meta
    )
    
    # Verify initial state populated
    assert final_state_1["user_goal"] == "Analyze this dataset."
    assert len(final_state_1["messages"]) == 1
    assert final_state_1["messages"][0]["content"] == "Analyze this dataset."
    
    # Simulate some downstream agent modifying the state (which our stubs do by returning partials)
    # Since our stubs just pass through, let's manually inject some EDA/Cleaning history 
    # directly into the checkpointer state to simulate agent work.
    config = {"configurable": {"thread_id": project_id}}
    await service.graph.aupdate_state(
        config,
        {
            "cleaning_history": ["Removed nulls from age column"],
            "data_profile": {"problem_type": "Regression"}
        }
    )
    
    # 3. Second Invocation (Simulating recovery/follow-up chat)
    # We pass only the new user message. We do NOT pass the dataset meta or goal again.
    final_state_2 = await service.invoke_pipeline(
        project_id=project_id,
        user_input="What was the problem type?",
        is_new_session=False
    )
    
    # 4. Assertions: Memory Recovery
    # The graph should have remembered EVERYTHING from the previous run
    assert final_state_2["user_goal"] == "Analyze this dataset." # Recalled from pass 1
    assert final_state_2["dataset_path"] == "/fake/path.csv"      # Recalled from pass 1
    
    # Messages should be appended (1 from pass 1 + 1 from pass 2)
    assert len(final_state_2["messages"]) == 2
    assert final_state_2["messages"][1]["content"] == "What was the problem type?"
    
    # Assert that simulated agent work was retained
    assert "Removed nulls from age column" in final_state_2["cleaning_history"]
    assert final_state_2["data_profile"]["problem_type"] == "Regression"

@pytest.mark.asyncio
async def test_memory_isolation_between_projects():
    """Test that two different projects do not share memory."""
    checkpointer = get_memory_checkpointer()
    service = PipelineService(checkpointer=checkpointer)
    
    p1 = "project-1"
    p2 = "project-2"
    
    # Project 1
    await service.invoke_pipeline(p1, "Goal 1", True, {"dataset_id": "1"})
    
    # Project 2
    await service.invoke_pipeline(p2, "Goal 2", True, {"dataset_id": "2"})
    
    # Fetch states
    state1 = await service.graph.aget_state({"configurable": {"thread_id": p1}})
    state2 = await service.graph.aget_state({"configurable": {"thread_id": p2}})
    
    assert state1.values["user_goal"] == "Goal 1"
    assert state2.values["user_goal"] == "Goal 2"
