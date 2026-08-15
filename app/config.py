import os


AWS_REGION = os.getenv("AWS_REGION", "us-west-2")

WORKFLOW_DEFINITIONS_TABLE_NAME = os.getenv(
    "WORKFLOW_DEFINITIONS_TABLE_NAME",
    "WorkflowDefinitions",
)

OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-5")
