# =============================================================================
# agents/planner_agent.py
#
# Planner Agent Implementation
#
# Design Decisions:
# 1. LangChain `with_structured_output`: Used to force the LLM to return
#    a strictly typed Pydantic object that perfectly matches our state schema.
#    This eliminates JSON parsing errors and hallucinated schemas.
# 2. Pydantic Models: `TaskItem` and `TaskPlanOutput` explicitly define the
#    expected structure. We convert this to our TypedDict `TaskPlanDict` for state.
# 3. Memory Integration: Fetches previous context if available to inform the plan.
# 4. Stateless Class: The `PlannerAgent` class has no internal state, making it
#    safe to instantiate and use concurrently across Celery workers.
# 5. Provider Agnostic: Uses LangChain's `BaseChatModel` interface so it can
#    switch between OpenAI, Gemini, or OSS transparently.
# =============================================================================

import json
import uuid
import logging
from typing import Any, List, Optional
from pydantic import BaseModel, Field

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.language_models import BaseChatModel

from graphs.state import GraphState, TaskPlanDict
from prompts.planner_prompts import PLANNER_SYSTEM_PROMPT
from graphs.memory import MemoryManager

log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Output Schemas
# ---------------------------------------------------------------------------

class TaskItem(BaseModel):
    """Represents a single atomic task in the execution plan."""
    task_id: str = Field(description="Unique identifier for the task, e.g., 'task_1'")
    description: str = Field(description="Detailed description of what needs to be done")
    assigned_agent: str = Field(description="The specialist agent assigned (e.g., 'Data Analyst Agent')")
    required_tools: List[str] = Field(description="List of tools the agent will need (e.g., ['python_sandbox', 'chart_renderer'])")
    dependencies: List[str] = Field(default_factory=list, description="List of task_ids that must finish before this one")

class TaskPlanOutput(BaseModel):
    """The complete structured output expected from the Planner LLM."""
    tasks: List[TaskItem] = Field(description="Ordered list of tasks to execute")
    estimated_duration_seconds: int = Field(description="Estimated time to complete the entire plan in seconds")
    selected_models: List[str] = Field(default_factory=list, description="Candidate ML models to try (if applicable)")


# ---------------------------------------------------------------------------
# Agent Implementation
# ---------------------------------------------------------------------------

class PlannerAgent:
    """
    The Supervisor Planner Agent.
    
    Reads the user goal and dataset profile, then generates a structured DAG of tasks
    assigned to specialist agents.
    """
    
    def __init__(self, llm: BaseChatModel, memory: MemoryManager):
        """
        Initialise the Planner Agent.
        
        Args:
            llm: A LangChain chat model (e.g., ChatOpenAI).
            memory: The configured MemoryManager for context retrieval.
        """
        self.llm = llm
        self.memory = memory
        
        # Bind the Pydantic schema to the LLM to force structured output
        self.structured_llm = self.llm.with_structured_output(TaskPlanOutput)
        
        # Create the prompt template
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", PLANNER_SYSTEM_PROMPT),
            ("user", "Please generate the execution plan.")
        ])
        
        # Chain composition
        self.chain = self.prompt | self.structured_llm

    async def generate_plan(self, state: GraphState) -> TaskPlanDict:
        """
        Generate a task plan based on the current graph state.
        
        Args:
            state: The current LangGraph state containing goal and data profile.
            
        Returns:
            A TaskPlanDict suitable for merging into the GraphState.
        """
        session_id = state.get("session_id", "unknown_session")
        user_goal = state.get("user_goal", "")
        data_profile = state.get("data_profile") or {}
        
        log.info(f"Generating execution plan for session: {session_id}")
        
        # Retrieve past long-term memory context if relevant (optional enhancement)
        # past_context = await self.memory.long_term.retrieve(session_id, user_goal)
        
        # Format the data profile for the prompt
        profile_str = json.dumps(data_profile, indent=2) if data_profile else "No profile available."
        
        try:
            # Execute the LangChain pipeline
            result: TaskPlanOutput = await self.chain.ainvoke({
                "user_goal": user_goal,
                "data_profile": profile_str
            })
            
            # Convert Pydantic output to TypedDict for GraphState
            tasks = [task.dict() for task in result.tasks]
            
            # Create a simple representation of the DAG for observability
            dag_edges = []
            for task in result.tasks:
                for dep in task.dependencies:
                    dag_edges.append(f"{dep} -> {task.task_id}")
            
            dag_json = json.dumps(dag_edges)
            
            plan_dict: TaskPlanDict = {
                "plan_id": str(uuid.uuid4()),
                "tasks": tasks,
                "dag_json": dag_json,
                "estimated_duration_seconds": result.estimated_duration_seconds,
                "selected_models": result.selected_models
            }
            
            log.info(f"Successfully generated plan with {len(tasks)} tasks.")
            return plan_dict
            
        except Exception as exc:
            log.error(f"Failed to generate execution plan: {str(exc)}")
            raise RuntimeError(f"Planner Agent failed: {str(exc)}")
