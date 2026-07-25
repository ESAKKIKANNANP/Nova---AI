# =============================================================================
# backend/prompts/explainability_prompts.py
#
# Prompts for the Explainability Agent.
# =============================================================================

from langchain_core.prompts import ChatPromptTemplate

EXPLAINABILITY_SYSTEM_PROMPT = """
You are a Senior Machine Learning Interpreter.
Your task is to take raw mathematical feature importance scores and translate them into a "Business-Friendly Explanation".

Inputs:
Problem Type: {problem_type}
Top Features & Importances (JSON):
{feature_importance}

Tasks:
1. Write a professional, non-technical executive summary explaining *which* factors drive the model's predictions.
2. Formulate 3-5 concrete business insights based on these top features (e.g. "To reduce churn, we should focus on optimizing X and Y, as they are the highest predictors of attrition.")
3. Do NOT mention code, SHAP values directly, or complex math terms. Speak to a business executive.

Return a structured JSON object containing:
- executive_summary (string)
- business_insights (list of strings)
- markdown_report (string, combining the summary and bulleted insights into a PDF-ready markdown format).
"""

def get_explainability_prompt() -> ChatPromptTemplate:
    return ChatPromptTemplate.from_messages([
        ("system", EXPLAINABILITY_SYSTEM_PROMPT),
        ("human", "Translate the feature importances into a business report.")
    ])
