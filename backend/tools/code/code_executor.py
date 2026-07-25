# =============================================================================
# backend/tools/code/code_executor.py
#
# Python Tool: Executes dynamic Python code blocks.
# Captures standard output, standard error, and returns computed variables.
# =============================================================================

import sys
import io
import traceback
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field

from tools.base import BaseTool


class PythonExecutorInput(BaseModel):
    code: str = Field(
        ...,
        description="The Python code block to execute.",
    )
    globals_dict: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Optional dictionary containing global variable context to execute within.",
    )


class PythonExecutorTool(BaseTool):
    """
    Tool that runs arbitrary Python code blocks dynamically and returns standard streams
    and the modified variables dictionary.
    """
    name = "python_executor"
    description = "Executes arbitrary Python code. Captures stdout, stderr, and returns updated variable bindings."
    args_schema = PythonExecutorInput

    def _run(self, code: str, globals_dict: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        if globals_dict is None:
            globals_dict = {}
        
        # Ensure common packages are imported in context if not explicitly done
        if "pd" not in globals_dict:
            import pandas as pd
            globals_dict["pd"] = pd
        if "np" not in globals_dict:
            import numpy as np
            globals_dict["np"] = np

        # Capture output streams
        stdout_capture = io.StringIO()
        stderr_capture = io.StringIO()
        
        original_stdout = sys.stdout
        original_stderr = sys.stderr
        
        sys.stdout = stdout_capture
        sys.stderr = stderr_capture
        
        exec_error = None
        local_vars: Dict[str, Any] = {}
        
        try:
            # We execute in a shared namespace copy to keep it isolated
            execution_globals = {**globals_dict}
            
            # Using exec to run code block
            exec(code, execution_globals, local_vars)
            
            # Update the original dict with modifications, ignoring internal system modules
            for key, val in execution_globals.items():
                if not key.startswith("__") and not hasattr(val, "__module__"):
                    globals_dict[key] = val
            for key, val in local_vars.items():
                if not key.startswith("__"):
                    globals_dict[key] = val
        except Exception:
            exec_error = traceback.format_exc()
        finally:
            # Revert standard streams
            sys.stdout = original_stdout
            sys.stderr = original_stderr

        stdout_val = stdout_capture.getvalue()
        stderr_val = stderr_capture.getvalue()
        
        # Serialize only primitive/serializable outputs for variables mapping (excluding modules/classes)
        serializable_vars = {}
        for k, v in globals_dict.items():
            if type(v).__name__ in ("DataFrame", "Series"):
                # Represent pandas objects by their basic shape/head metadata
                serializable_vars[k] = {
                    "type": type(v).__name__,
                    "shape": v.shape,
                    "columns": list(v.columns) if hasattr(v, "columns") else None
                }
            elif type(v).__name__ in ("int", "float", "str", "bool", "list", "dict", "NoneType"):
                serializable_vars[k] = v

        if exec_error:
            raise RuntimeError(
                f"Execution failed.\nStdout:\n{stdout_val}\nStderr:\n{stderr_val}\nTraceback:\n{exec_error}"
            )

        return {
            "stdout": stdout_val,
            "stderr": stderr_val,
            "variables": serializable_vars
        }
