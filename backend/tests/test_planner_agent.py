# =============================================================================
# tests/test_planner_agent.py
#
# Tests for the Planner Agent.
# =============================================================================

import pytest
from unittest.mock import AsyncMock, MagicMock

from langchain_core.messages import AIMessage
from langchain_core.language_models import BaseChatModel

from agents.planner_agent import PlannerAgent, TaskPlanOutput, TaskItem
from graphs.memory import MemoryManager
from graphs.state import create_initial_state

class MockChatModel(BaseChatModel):
    """A mock LangChain chat model that returns a hardcoded structured output."""
    
    @property
    def _llm_type(self) -> str:
        return "mock"
        
    def _generate(self, messages, stop=None, run_manager=None, **kwargs):
        return AIMessage(content="mock")
        
    def with_structured_output(self, schema, **kwargs):
        """Mock the structured output binding to return our test object."""
        mock_plan = TaskPlanOutput(
            tasks=[
                TaskItem(
                    task_id="task_1",
                    description="Perform EDA on numerical columns",
                    assigned_agent="Data Analyst Agent",
                    required_tools=["python_sandbox"],
                    dependencies=[]
                )
            ],
            estimated_duration_seconds=300,
            selected_models=["RandomForest", "XGBoost"]
        )
        mock_chain = AsyncMock(return_value=mock_plan)
        mock_chain.ainvoke = AsyncMock(return_value=mock_plan)
        mock_chain.invoke = MagicMock(return_value=mock_plan)
        return mock_chain

@pytest.fixture
def mock_memory():
    """Mock memory manager."""
    short_term = AsyncMock()
    long_term = AsyncMock()
    return MemoryManager(short_term=short_term, long_term=long_term)

@pytest.mark.asyncio
async def test_planner_agent_generates_valid_plan(mock_memory):
    """
    Test that the PlannerAgent correctly invokes the LLM, parses the
    structured output, and returns a valid TaskPlanDict matching our state.
    """
    # 1. Setup
    mock_llm = MockChatModel()
    agent = PlannerAgent(llm=mock_llm, memory=mock_memory)
    
    initial_state = create_initial_state(
        session_id="test-session-123",
        user_id="test-user-456",
        user_goal="Predict house prices based on historical data.",
        dataset_id="test-dataset-789",
        dataset_path="/tmp/test.csv"
    )
    
    # Inject fake data profile
    initial_state["data_profile"] = {
        "row_count": 1000,
        "column_count": 5,
        "columns": ["id", "bedrooms", "bathrooms", "sqft", "price"]
    }
    
    # 2. Execute
    plan = await agent.generate_plan(initial_state)
    
    # 3. Assertions
    assert plan is not None
    assert "plan_id" in plan
    assert len(plan["tasks"]) == 1
    
    task = plan["tasks"][0]
    assert task["task_id"] == "task_1"
    assert task["assigned_agent"] == "Data Analyst Agent"
    assert "python_sandbox" in task["required_tools"]
    
    assert plan["estimated_duration_seconds"] == 300
    assert "XGBoost" in plan["selected_models"]
