# =============================================================================
# graphs/state.py
#
# LangGraph Graph State Definition — Autonomous Data Scientist
#
# This module defines the *single source of truth* for all data that flows
# through the LangGraph StateGraph.  Every node receives the current state
# as input and returns a **partial** state update (a dict containing only the
# keys it modified).  LangGraph merges those partials back into the canonical
# state using the *reducer* functions annotated on each field.
#
# Design Decisions
# ──────────────────
# 1. TypedDict (not dataclass / Pydantic) — LangGraph requires TypedDict so
#    that its internal diffing, checkpointing, and streaming work correctly.
# 2. Annotated + reducer — fields that accumulate values (lists, dicts) use
#    `Annotated[T, reducer_fn]` so merges are non-destructive.  Scalar fields
#    are plain types; the last writer wins.
# 3. All fields are Optional with sensible defaults — ensures a node can
#    return only what it changed without breaking downstream reads.
# 4. Separate sub-types (DataProfile, TaskPlan, …) are plain dataclasses
#    stored as frozen dicts in state (JSON-serializable for checkpointing).
#
# Field groups
# ─────────────
#   [SESSION]     Identity and lifecycle
#   [INPUT]       What the user provided
#   [PLANNING]    Planner agent's task decomposition
#   [EXECUTION]   Runtime data for each pipeline stage
#   [QUALITY]     Critic / verifier pass results
#   [OUTPUT]      Final artefacts and report
#   [CONTROL]     Routing, retry, and human-in-the-loop flags
# =============================================================================

from __future__ import annotations

import operator
from typing import Annotated, Any, TypedDict


# ---------------------------------------------------------------------------
# Reducer helpers
# ---------------------------------------------------------------------------

def _append_list(existing: list[Any], update: list[Any]) -> list[Any]:
    """
    Reducer for list fields: appends ``update`` to ``existing``.

    Used for fields that accumulate results across nodes (e.g. agent outputs,
    executed code snippets, artefacts).  LangGraph calls this automatically
    when a node returns a partial update for an Annotated list field.

    Example::

        existing = [1, 2]
        update   = [3, 4]
        result   = [1, 2, 3, 4]
    """
    if existing is None:
        return update or []
    return existing + (update or [])


def _merge_dict(existing: dict[str, Any], update: dict[str, Any]) -> dict[str, Any]:
    """
    Reducer for dict fields: shallow-merges ``update`` into ``existing``.

    Later keys from ``update`` overwrite earlier ones, which is the standard
    accumulation pattern for metadata dicts that get enriched by multiple nodes.

    Example::

        existing = {"a": 1, "b": 2}
        update   = {"b": 99, "c": 3}
        result   = {"a": 1, "b": 99, "c": 3}
    """
    if existing is None:
        return update or {}
    return {**(existing or {}), **(update or {})}


# ---------------------------------------------------------------------------
# Sub-types (stored as plain dicts inside GraphState for JSON serializability)
# ---------------------------------------------------------------------------

class ColumnProfileDict(TypedDict, total=False):
    dtype: str
    cardinality: int
    null_pct: float
    sample_values: list[Any]
    role: str # "target" | "feature" | "id" | "date" | "text"

class BusinessContextDict(TypedDict, total=False):
    domain: str
    key_metrics: list[str]
    narrative_goals: list[str]

class ModelResultDict(TypedDict, total=False):
    model_name: str
    params: dict[str, Any]
    metrics: dict[str, float]
    rank: int

class ChartSpecDict(TypedDict, total=False):
    chart_type: str # "bar" | "line" | "area" | "scatter" | "treemap" | "donut" | "table" | "heatmap"
    columns: list[str]
    title: str
    rationale: str

class WidgetDict(TypedDict, total=False):
    widget_type: str # "kpi" | "chart" | "table" | "insights"
    data_binding_key: str
    grid_position: int
    size: int # span columns

class DataProfileDict(TypedDict, total=False):
    """Schema for the data-profile sub-object produced by the ingest node."""

    row_count: int                          # number of rows in the dataset
    column_count: int                       # number of columns
    columns: list[str]                      # column names
    dtypes: dict[str, str]                  # col → pandas dtype string
    missing_pct: dict[str, float]           # col → % missing values
    numeric_summary: dict[str, Any]         # col → {mean, std, min, max, …}
    categorical_summary: dict[str, Any]     # col → {top, freq, unique_count}
    target_column: str | None               # user-specified target (if any)
    problem_type: str | None                # "classification" | "regression" | "clustering" | None
    column_profiles: dict[str, ColumnProfileDict]  # col → detailed profile


class TaskPlanDict(TypedDict, total=False):
    """Schema for the task plan produced by the Planner agent."""

    plan_id: str                            # UUID for this particular plan version
    tasks: list[dict[str, Any]]             # ordered list of task descriptors
    dag_json: str                           # JSON-encoded directed-acyclic-graph
    estimated_duration_seconds: int         # rough time estimate
    selected_models: list[str]              # candidate model names


class AgentOutputDict(TypedDict, total=False):
    """Schema for a single agent's output appended to `agent_outputs`."""

    agent_name: str                         # e.g. "data_analyst_agent"
    node_id: str                            # LangGraph node key
    output: Any                             # raw structured output
    validated: bool                         # True after Critic passes it
    critique: str | None                    # Critic feedback (if any)
    tokens_used: int                        # LLM tokens consumed
    latency_ms: float                       # wall-clock time for this node


class ArtifactDict(TypedDict, total=False):
    """Schema for a generated artefact (plot, model file, CSV, etc.)."""

    artifact_id: str                        # UUID
    artifact_type: str                      # "chart" | "model" | "csv" | "report"
    s3_path: str                            # object-store key / path
    mime_type: str                          # MIME type string
    title: str                              # human-readable title
    created_at: str                         # ISO-8601 timestamp


# ---------------------------------------------------------------------------
# Main Graph State
# ---------------------------------------------------------------------------

class GraphState(TypedDict, total=False):
    """
    Canonical state object for the Autonomous Data Scientist LangGraph.

    Every node receives the full ``GraphState`` and returns a **partial** dict
    containing only the fields it modified.  LangGraph merges those partials
    back using the reducer functions declared via ``Annotated``.

    Usage in a node::

        def my_node(state: GraphState) -> GraphState:
            # Read
            goal = state["user_goal"]
            # Produce partial update
            return {"current_node": "my_node", "agent_outputs": [my_result]}

    Annotated list/dict fields use custom reducers so they accumulate across
    nodes instead of being overwritten.
    """

    # ── SESSION ──────────────────────────────────────────────────────────────

    session_id: str
    """Unique identifier for the analysis session (UUID4 string).
    Shared across all nodes so that logs, events, and artefacts can be
    correlated back to a single user request."""

    user_id: str
    """Identifier of the authenticated user who initiated the session."""

    created_at: str
    """ISO-8601 timestamp of when the session was created."""

    # ── INPUT ─────────────────────────────────────────────────────────────────

    user_goal: str
    """Natural-language goal entered by the user.
    Example: 'Predict churn probability for the telecom dataset'."""

    dataset_id: str
    """Reference to the dataset record in PostgreSQL."""

    dataset_path: str
    """Resolved object-store path (S3 key or local path) to the raw dataset."""

    dataset_format: str
    """File format: 'csv' | 'excel' | 'json' | 'parquet' | 'database'."""

    # ── PLANNING ─────────────────────────────────────────────────────────────

    data_profile: Annotated[DataProfileDict | None, _merge_dict]
    """Populated by the *ingest_node*. Contains row count, dtypes, missing-
    value percentages, and a summary of numeric and categorical columns."""

    task_plan: TaskPlanDict | None
    """Populated by the *planner_node*. A DAG of tasks that maps directly to
    downstream LangGraph nodes."""

    business_context: Annotated[BusinessContextDict | None, _merge_dict]
    """Populated by the *business_insight_agent*. Contains inferred domain,
    KPIs, and narrative goals."""

    task_type: str | None
    """Populated by the *problem_detection_node*. E.g., 'classification', 'regression', etc."""

    model_results: Annotated[list[ModelResultDict], _append_list]
    """Populated by the *train_node*. Contains a list of evaluation results for all models."""

    chart_specs: Annotated[list[ChartSpecDict], _append_list]
    """Populated by the *visualizer_node*. Contains instructions on which columns
    to display on which chart type."""

    widgets: Annotated[list[WidgetDict], _append_list]
    """Populated by the *dashboard_designer_node*. Describes layout configurations."""

    # ── EXECUTION ─────────────────────────────────────────────────────────────

    agent_outputs: Annotated[list[AgentOutputDict], _append_list]
    """Accumulated list of per-node outputs.  Uses ``_append_list`` reducer so
    that each node *appends* its output rather than overwriting the list."""

    executed_code: Annotated[list[str], _append_list]
    """Accumulates every Python snippet executed in the sandbox.  Useful for
    audit, debugging, and report generation."""

    cleaning_history: Annotated[list[str], _append_list]
    """Accumulates a log of all data cleaning transformations applied."""

    messages: Annotated[list[Any], _append_list]
    """Conversation history containing user inputs and agent responses."""

    execution_results: Annotated[dict[str, Any], _merge_dict]
    """Key-value store of intermediate results indexed by node name.
    Uses ``_merge_dict`` so each node adds its keys without clobbering others.

    Example::

        {"eda_node": {...stats...}, "feature_node": {"feature_list": [...]}}
    """

    # ── QUALITY ───────────────────────────────────────────────────────────────

    critic_feedback: str | None
    """Latest feedback from the Critic / Verifier agent.
    ``None`` when quality checks have not run yet or when the last run passed."""

    critic_passed: bool | None
    """``True`` — output quality is acceptable; routing continues downstream.
    ``False`` — routing loops back to the planner for retry."""

    retry_count: int
    """Number of times the graph has looped back via the critic path.
    Used by conditional edges to enforce a maximum retry limit."""

    # ── OUTPUT ────────────────────────────────────────────────────────────────

    artifacts: Annotated[list[ArtifactDict], _append_list]
    """Accumulates all generated artefacts (charts, model files, CSVs, etc.)
    throughout the pipeline.  Appended to by visualiser and other nodes."""

    final_report: str | None
    """Markdown-formatted final report generated by the insight_generator_node.
    Stored in PostgreSQL and surfaced to the user via the API."""

    # ── CONTROL ───────────────────────────────────────────────────────────────

    current_node: str | None
    """Name of the node currently executing.  Set at the start of each node
    for observability (streaming events, logging)."""

    next_node: str | None
    """Explicit routing hint written by conditional edge functions when
    straight-line routing is not sufficient."""

    error_message: str | None
    """Set by any node that catches an unrecoverable exception.
    The ``error_recovery_node`` reads this and decides whether to retry or
    escalate to human review."""

    error_node: str | None
    """Name of the node that raised the error, for targeted retry logic."""

    requires_human: bool
    """When ``True`` the graph pauses at ``human_review_node`` and waits for
    external input via the ``Command`` primitive (LangGraph ≥ 0.2)."""
    
    # Autonomous Loop tracking
    optimization_attempts: int
    max_optimization_attempts: int
    target_metric_threshold: float
    is_cancelled: bool
    is_complete: bool
    """Sentinel set by the *report_node* when the pipeline finishes
    successfully.  The ``should_end`` edge function reads this to route to
    ``END``."""

    # ── METADATA ──────────────────────────────────────────────────────────────

    metadata: Annotated[dict[str, Any], _merge_dict]
    """Catch-all dict for arbitrary key-value pairs that nodes want to persist
    without adding new top-level fields.  Merged across nodes."""


# ---------------------------------------------------------------------------
# Default state factory
# ---------------------------------------------------------------------------

def create_initial_state(
    *,
    session_id: str,
    user_id: str,
    user_goal: str,
    dataset_id: str,
    dataset_path: str,
    dataset_format: str = "csv",
    created_at: str | None = None,
) -> GraphState:
    """
    Create a fully-initialised ``GraphState`` with all optional fields set to
    safe defaults.

    This is the canonical entry-point for creating state — callers should never
    build the dict by hand because missing keys cause ``KeyError`` in nodes.

    Args:
        session_id:     UUID4 string identifying this analysis session.
        user_id:        Authenticated user identifier.
        user_goal:      Natural-language goal from the user.
        dataset_id:     Database record ID of the uploaded dataset.
        dataset_path:   Object-store path (S3 key or local) to the raw file.
        dataset_format: One of 'csv', 'excel', 'json', 'parquet', 'database'.
        created_at:     ISO-8601 timestamp; defaults to UTC now if omitted.

    Returns:
        A ``GraphState`` dict ready to be passed as ``input`` to
        ``graph.invoke()``.
    """
    import datetime

    return GraphState(
        # Session
        session_id=session_id,
        user_id=user_id,
        created_at=created_at or datetime.datetime.utcnow().isoformat() + "Z",
        # Input
        user_goal=user_goal,
        dataset_id=dataset_id,
        dataset_path=dataset_path,
        dataset_format=dataset_format,
        # Planning
        data_profile=None,
        task_plan=None,
        business_context=None,
        task_type=None,
        model_results=[],
        chart_specs=[],
        widgets=[],
        # Execution
        agent_outputs=[],
        executed_code=[],
        cleaning_history=[],
        messages=[],
        execution_results={},
        # Quality
        critic_feedback=None,
        critic_passed=None,
        retry_count=0,
        # Output
        artifacts=[],
        final_report=None,
        # Control
        current_node=None,
        next_node=None,
        error_message=None,
        error_node=None,
        requires_human=False,
        is_complete=False,
        # Metadata
        metadata={},
    )
