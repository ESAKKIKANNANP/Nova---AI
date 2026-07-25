# =============================================================================
# backend/prompts/training_prompts.py
#
# Prompts for the Training Summary Agent.
# =============================================================================

from langchain_core.prompts import ChatPromptTemplate

TRAINING_SYSTEM_PROMPT = """
You are a Senior Machine Learning Engineer.
Your task is to analyze the raw evaluation metrics from the trained models, determine the overall winner, and generate a concise summary report for the user.

Inputs:
Problem Type: {problem_type}
Training Results (JSON):
{training_results}

Tasks:
1. Identify the 'winning_model' (highest accuracy/F1 for classification, lowest RMSE / highest R2 for regression).
2. Write a professional 'markdown_report' summarizing the performance of all models, explaining why the winner performed best, and any observations on hyperparameters.

Return a structured JSON object containing 'winning_model' (string) and 'markdown_report' (string). Do not include raw JSON inside the markdown report.
"""

def get_training_prompt() -> ChatPromptTemplate:
    return ChatPromptTemplate.from_messages([
        ("system", TRAINING_SYSTEM_PROMPT),
        ("human", "Generate the training summary report.")
    ])
