# =============================================================================
# backend/services/pipeline_service.py
#
# Pipeline Service integrating LangGraph Checkpointer and Memory.
#
# Architecture Decisions:
# 1. Per-Project Memory: LangGraph's checkpointer tracks state via `thread_id`.
#    By mapping `thread_id` directly to `project_id`, we natively isolate memory
#    and conversation history per workspace.
# 2. Resumption & Recovery: Because we use the `checkpointer` when compiling,
#    calling `.ainvoke()` or `.astream()` with an existing `project_id` automatically
#    fetches the previous graph state (including metadata, cleaning history, EDA).
# 3. Message Appending: We pass the user's new message as a partial state update.
#    LangGraph's reducers will automatically append it to the `messages` array.
# =============================================================================

import logging
from typing import Any, Dict

from graphs.state import create_initial_state, GraphState
from graphs.graphs.main_graph import compile_graph
from graphs.checkpointers.postgres_checkpointer import get_memory_checkpointer

log = logging.getLogger(__name__)

class PipelineService:
    """
    Service responsible for orchestrating the LangGraph pipeline execution,
    managing per-project memory, and handling state resumption.
    """
    
    def __init__(self, checkpointer=None):
        """
        Initialize with a checkpointer. Defaults to memory saver for tests,
        but in production this would be the PostgresCheckpointer.
        """
        self.checkpointer = checkpointer or get_memory_checkpointer()
        self.graph = compile_graph(checkpointer=self.checkpointer)

    async def invoke_pipeline(
        self, 
        project_id: str, 
        user_input: str,
        is_new_session: bool = False,
        dataset_meta: Dict[str, Any] = None
    ) -> GraphState:
        """
        Invokes the LangGraph pipeline for a specific project.
        
        Args:
            project_id: The unique workspace ID. Acts as the checkpointer's thread_id.
            user_input: The chat message or command from the user.
            is_new_session: If True, creates a fresh state. If False, resumes existing state.
            dataset_meta: Metadata to inject if it's a new session.
            
        Returns:
            The resulting GraphState after execution.
        """
        # The crucial mapping: thread_id = project_id
        config = {"configurable": {"thread_id": project_id}}
        
        if is_new_session:
            log.info(f"Starting NEW pipeline session for project {project_id}")
            if not dataset_meta:
                dataset_meta = {}
                
            # Create the absolute initial state
            initial_state = create_initial_state(
                session_id=project_id,
                user_id="system",
                user_goal=user_input,
                dataset_id=dataset_meta.get("dataset_id", "unknown"),
                dataset_path=dataset_meta.get("dataset_path", "unknown")
            )
            
            # Append the first message
            initial_state["messages"] = [{"role": "user", "content": user_input}]
            
            # Execute from scratch
            return await self.graph.ainvoke(initial_state, config=config)
            
        else:
            log.info(f"Resuming EXISTING pipeline session for project {project_id}")
            
            # Fetch the existing state from the checkpointer
            state_snapshot = await self.graph.aget_state(config)
            
            if not state_snapshot or not state_snapshot.values:
                raise ValueError(f"No existing memory found for project {project_id}")
                
            # We ONLY pass the newly appended message as a partial update.
            # LangGraph's reducers (_append_list) will merge this into the existing state
            # without overwriting the dataset metadata, EDA results, or problem type.
            partial_update = {
                "messages": [{"role": "user", "content": user_input}]
            }
            
            # Execute starting from wherever the graph last paused (or from START if it finished)
            return await self.graph.ainvoke(partial_update, config=config)

    async def invoke_pipeline_background(
        self,
        project_id: str,
        user_input: str,
        is_new_session: bool = False,
        dataset_meta: Dict[str, Any] = None
    ) -> None:
        """
        Wrapper to execute the pipeline in the background. Catches unhandled exceptions
        and writes them into the graph state so the /status endpoint can report them.
        """
        try:
            await self.invoke_pipeline(project_id, user_input, is_new_session, dataset_meta)
            log.info(f"Background pipeline for project {project_id} completed successfully.")
        except Exception as e:
            log.error(f"Background pipeline failed for project {project_id}: {str(e)}")
            # Try to push the error into the state
            config = {"configurable": {"thread_id": project_id}}
            try:
                await self.graph.aupdate_state(config, {"error_message": str(e)})
            except Exception as update_err:
                log.error(f"Failed to update error state: {str(update_err)}")

    async def stream_pipeline_events(self, project_id: str):
        """
        Resumes the pipeline and streams execution events (SSE compatible).
        Note: If this is a new run, `invoke_pipeline_background` handles the execution.
        This stream method is meant to tail an *already running* graph, but in LangGraph
        you generally stream during the actual invocation. Since we use BackgroundTasks
        for simplicity right now, this stream method would be implemented by tailing 
        checkpoint writes or using an external event bus. 
        For this MVP, we will yield simple state snapshots by polling, or use a pub/sub.
        """
        pass  # Real-time streaming requires Redis PubSub when decoupling from HTTP.

