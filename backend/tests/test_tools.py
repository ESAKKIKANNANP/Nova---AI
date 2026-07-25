# =============================================================================
# backend/tests/test_tools.py
#
# Unit tests verifying functionality, validation, logging, and error handling
# for all tools in the Tool Registry.
# =============================================================================

import os
import uuid
import pytest
import pandas as pd
from pydantic import BaseModel

from tools.base import BaseTool, ToolResult
from tools.registry import ToolRegistry, registry
from tools.code.code_executor import PythonExecutorTool
from tools.data.csv_loader import FileLoaderTool
from tools.data.sql_reader import SQLReaderTool
from tools.visualization.chart_renderer import ChartRendererTool
from tools.ml.model_trainer import ModelTrainerTool
from tools.external.rag_tool import RAGQueryTool


# -----------------------------------------------------------------------------
# 1. BaseTool & Registry Tests
# -----------------------------------------------------------------------------

class DummyArgs(BaseModel):
    num: int

class DummyTool(BaseTool):
    name = "dummy"
    description = "Dummy tool for test"
    args_schema = DummyArgs

    def _run(self, num: int) -> int:
        if num < 0:
            raise ValueError("Must be non-negative")
        return num * 2


@pytest.mark.unit
def test_base_tool_validation_and_errors() -> None:
    tool = DummyTool()
    
    # Successful execution
    res = tool.run(num=5)
    assert res.success is True
    assert res.data == 10
    assert res.error is None
    assert res.execution_time_ms >= 0

    # Validation failure (missing arg)
    res_val_fail = tool.run()
    assert res_val_fail.success is False
    assert "validation failed" in res_val_fail.error.lower()

    # Runtime error
    res_runtime_fail = tool.run(num=-1)
    assert res_runtime_fail.success is False
    assert "must be non-negative" in res_runtime_fail.error.lower()


@pytest.mark.unit
def test_tool_registry() -> None:
    # Check default registered tools
    assert len(registry.list_tools()) >= 6
    python_tool = registry.get_tool("python_executor")
    assert isinstance(python_tool, PythonExecutorTool)

    with pytest.raises(KeyError):
        registry.get_tool("nonexistent_tool")


# -----------------------------------------------------------------------------
# 2. Python Executor Tool Tests
# -----------------------------------------------------------------------------

@pytest.mark.unit
def test_python_executor_success() -> None:
    tool = PythonExecutorTool()
    code = """
import pandas as pd
res_val = 10 + 20
print(f"Output is: {res_val}")
df = pd.DataFrame({'a': [1, 2]})
"""
    res = tool.run(code=code)
    assert res.success is True
    assert "Output is: 30" in res.data["stdout"]
    assert res.data["variables"]["res_val"] == 30
    assert res.data["variables"]["df"]["type"] == "DataFrame"
    assert res.data["variables"]["df"]["shape"] == (2, 1)


@pytest.mark.unit
def test_python_executor_syntax_error() -> None:
    tool = PythonExecutorTool()
    res = tool.run(code="invalid python code syntax ---")
    assert res.success is False
    assert "SyntaxError" in res.error or "NameError" in res.error


# -----------------------------------------------------------------------------
# 3. File Loader Tool Tests
# -----------------------------------------------------------------------------

@pytest.mark.unit
def test_file_loader_csv(tmp_path) -> None:
    # Create temp CSV
    csv_file = tmp_path / "test_data.csv"
    df = pd.DataFrame({
        "name": ["Alice", "Bob", "Charlie"],
        "age": [25, 30, 35],
        "score": [88.5, 92.0, 79.5]
    })
    df.to_csv(csv_file, index=False)

    tool = FileLoaderTool()
    res = tool.run(file_path=str(csv_file))
    
    assert res.success is True
    assert res.data["row_count"] == 3
    assert res.data["column_count"] == 3
    assert len(res.data["columns"]) == 3
    assert res.data["columns"][1]["name"] == "age"
    assert res.data["columns"][1]["mean"] == 30.0
    assert res.data["columns"][1]["min"] == 25.0
    assert len(res.data["preview_data"]) == 3


@pytest.mark.unit
def test_file_loader_excel(tmp_path) -> None:
    excel_file = tmp_path / "test_data.xlsx"
    df = pd.DataFrame({"col1": [1, 2], "col2": [3, 4]})
    df.to_excel(excel_file, index=False)

    tool = FileLoaderTool()
    res = tool.run(file_path=str(excel_file))
    assert res.success is True
    assert res.data["row_count"] == 2
    assert res.data["column_count"] == 2


# -----------------------------------------------------------------------------
# 4. SQL Reader Tool Tests
# -----------------------------------------------------------------------------

@pytest.mark.unit
def test_sql_reader_sqlite(tmp_path) -> None:
    db_file = tmp_path / "test.db"
    conn_uri = f"sqlite:///{db_file}"
    
    # Seed db using sqlite connection
    df = pd.DataFrame({"id": [1, 2], "value": ["A", "B"]})
    from sqlalchemy import create_engine
    engine = create_engine(conn_uri)
    df.to_sql("test_table", engine, index=False)
    engine.dispose()

    tool = SQLReaderTool()
    
    # Read SELECT query
    res = tool.run(connection_uri=conn_uri, query="SELECT * FROM test_table")
    assert res.success is True
    assert res.data["row_count"] == 2
    assert res.data["columns"] == ["id", "value"]
    assert res.data["rows"][0]["value"] == "A"

    # Block non-SELECT query
    res_block = tool.run(connection_uri=conn_uri, query="DROP TABLE test_table")
    assert res_block.success is False
    assert "only read-only select" in res_block.error.lower()


# -----------------------------------------------------------------------------
# 5. Chart Renderer Tool Tests
# -----------------------------------------------------------------------------

@pytest.mark.unit
def test_chart_renderer_line() -> None:
    tool = ChartRendererTool()
    data = [
        {"x": 1, "y": 10, "grp": "A"},
        {"x": 2, "y": 20, "grp": "A"},
        {"x": 1, "y": 15, "grp": "B"},
        {"x": 2, "y": 25, "grp": "B"}
    ]
    res = tool.run(
        data=data,
        chart_type="line",
        x_column="x",
        y_column="y",
        hue_column="grp",
        title="Sample Chart"
    )
    assert res.success is True
    assert "image_base64" in res.data
    assert res.data["image_base64"].startswith("data:image/png;base64,")
    assert res.data["plotly_spec"]["chart_type"] == "line"


# -----------------------------------------------------------------------------
# 6. Model Trainer Tool Tests
# -----------------------------------------------------------------------------

@pytest.mark.unit
def test_model_trainer_classification() -> None:
    # Synthetic classification dataset
    data = []
    for i in range(100):
        # Feature correlation
        val = i % 2
        data.append({
            "feat1": float(val * 10 + (i % 3)),
            "feat2": float((1 - val) * 5),
            "label": "class_a" if val == 1 else "class_b"
        })

    tool = ModelTrainerTool()
    res = tool.run(
        data=data,
        target_column="label",
        task_type="classification"
    )
    assert res.success is True
    assert res.data["task_type"] == "classification"
    assert "accuracy" in res.data["metrics"]
    assert "f1_score" in res.data["metrics"]
    assert res.data["feature_count"] == 2
    assert "feat1" in res.data["feature_importances"]


@pytest.mark.unit
def test_model_trainer_regression() -> None:
    # Synthetic regression dataset
    data = []
    for i in range(100):
        data.append({
            "feat1": float(i),
            "feat2": float(i * 1.5),
            "target": float(i * 10 + 5)
        })

    tool = ModelTrainerTool()
    res = tool.run(
        data=data,
        target_column="target",
        task_type="regression"
    )
    assert res.success is True
    assert res.data["task_type"] == "regression"
    assert "r2_score" in res.data["metrics"]
    assert "root_mean_squared_error" in res.data["metrics"]


# -----------------------------------------------------------------------------
# 7. RAG Query Tool Tests
# -----------------------------------------------------------------------------

@pytest.mark.unit
def test_rag_query() -> None:
    documents = [
        {"id": "1", "text": "The quick brown fox jumps over the lazy dog.", "source_uri": "s1", "title": "t1"},
        {"id": "2", "text": "SQL databases store structured rows and tables.", "source_uri": "s2", "title": "t2"},
        {"id": "3", "text": "Random Forest is a machine learning algorithm for tabular datasets.", "source_uri": "s3", "title": "t3"}
    ]
    tool = RAGQueryTool()
    
    # Query for ML details
    res = tool.run(query="machine learning algorithm random forest", documents=documents, top_k=1)
    assert res.success is True
    assert res.data["count"] == 1
    assert res.data["results"][0]["document"]["id"] == "3"
    assert res.data["results"][0]["score"] > 0.0
